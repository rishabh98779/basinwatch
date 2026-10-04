%%% CHAPTER 5 %%%

# CHAPTER 5: JAVA I/O AND PERSISTENCE

## 5.1 Java I/O Overview

Java's I/O library is organised around two parallel hierarchies: **byte streams**, which move raw bytes and are the correct choice for binary data, and **character streams**, which move text and handle character encoding. Both hierarchies are built from the same idea: a stream is a source or sink of data, and streams can be wrapped around one another so that each layer adds one concern. BasinWatch uses both hierarchies, and it chooses between them deliberately: typed measurements and session snapshots are binary, so they use byte streams; the operational journal and the situation report are text, so they use character streams.

## 5.2 Byte Streams

Byte streams are represented by `InputStream` and `OutputStream`. The project's binary archive and its session snapshots are built on these base classes. `SensorArchive` writes through a `DataOutputStream` layered over a `BufferedOutputStream` layered over a file output stream, so that the file ultimately receives bytes. The snapshot store reads and writes bytes through byte-array streams before committing them to a file.

## 5.3 Character Streams

Character streams are represented by `Reader` and `Writer`. The operational journal and the report writer both use a `BufferedWriter` created from `Files.newBufferedWriter` with an explicit UTF-8 charset, so that timestamps and human-readable messages are encoded consistently regardless of the platform default. The sensor pipeline's internal transport is also character-based: the feed writes to a `PipedWriter` and the intake task reads through a `PipedReader` wrapped in a `BufferedReader`.

## 5.4 Buffered Streams

Buffering reduces the number of low-level operating-system calls by batching small reads and writes. The archive uses a `BufferedOutputStream`, the journal uses a `BufferedWriter`, and the intake task reads through a `BufferedReader`. This matters because the application writes many small items — one journal line per event, one typed record per reading — and without buffering each item would incur its own file operation.

## 5.5 Data Streams

Data streams read and write Java's primitive types in a defined, portable order. `SensorArchive` uses `DataOutputStream` to write each measurement as a `long` tick, two `UTF` strings, and two `double` values. The advantage over plain text is that types are preserved exactly: a water level is stored as an eight-byte double, not as a decimal string that would need parsing and could lose precision or depend on a locale.

```java
// io/SensorArchive.java (append, line 40)
public synchronized void append(SensorReading reading) throws IOException {
    output.writeLong(reading.tick());
    output.writeUTF(reading.stationId());
    output.writeUTF(reading.zoneId());
    output.writeDouble(reading.rainfallMillimeters());
    output.writeDouble(reading.observedRiseCentimeters());
}
```

*Listing 5.1: Typed binary records written in a fixed order.*

## 5.6 Filter and Wrapper Streams

The filter streams are the wrapping streams that add behaviour: buffering, typed encoding, or object serialization. The project relies on this pattern repeatedly. The archive is a data stream wrapped around a buffered stream wrapped around a file stream. The journal is a buffered writer around a file. The snapshot store is an object stream around a byte-array stream around a file. Each layer adds exactly one concern, and the domain never needs to know which concrete device lies at the bottom.

| Artefact | Stream chain | Data |
|---|---|---|
| Operational journal | `BufferedWriter` → file | UTF-8 text lines |
| Sensor archive | `DataOutputStream` → `BufferedOutputStream` → file | Typed binary records |
| Session save | `ObjectOutputStream` → `ByteArrayOutputStream` → file | Serialized snapshot |
| Session load | file → `BufferedInputStream` → `ByteArrayInputStream` → `ObjectInputStream` | Deserialized snapshot |
| Situation report | `BufferedWriter` → file | UTF-8 text |

*Table 5.1: Persistence artefacts and their stream chains.*

## 5.7 Byte-Array Streams

Byte-array streams operate on in-memory arrays rather than files. The snapshot store uses `ByteArrayOutputStream` to build a complete serialized payload in memory and `ByteArrayInputStream` to read it back. This matters because it allows the store to measure and validate the entire payload *before* it touches the target file, so a save either succeeds completely or leaves the previous save untouched. A subtlety worth recording, and one the syllabus emphasises, is that a byte-array input stream does not grow its source array: it reads only the bytes it was given.

## 5.8 File and File Metadata

`File` and `Path` describe locations and metadata rather than contents. The `AppPaths` record resolves the per-user data root, creates the four data directories, and exposes the database path. The `SaveCatalog` lists session saves by examining file metadata — it filters names ending in `.bws` and sorts by last-modified time — without opening any file's contents.

```java
// io/AppPaths.java (create, line 36)
Path absolute = root.toAbsolutePath().normalize();
Path logs = absolute.resolve("data").resolve("logs");
Path archive = absolute.resolve("data").resolve("archive");
Path saves = absolute.resolve("data").resolve("saves");
Path reports = absolute.resolve("data").resolve("reports");
Path database = absolute.resolve("data").resolve("basinwatch.db");
Files.createDirectories(logs);
Files.createDirectories(archive);
Files.createDirectories(saves);
Files.createDirectories(reports);
```

*Listing 5.2: Directory and path resolution using `Path` and `Files`.*

On Windows the default data root is `%APPDATA%\BasinWatch`; on other platforms it is `~/.basinwatch`. A `--data-dir` argument overrides the location.

## 5.9 Serialization

Serialization converts an object graph into a byte stream. The project serializes a `SessionSnapshot`, a `Serializable` class that carries the simulation tick, the six zones, the resource counts, the missions, and recent activity. The class declares an explicit `serialVersionUID` and a format version, and one field is marked `transient` so that it is never written to disk.

## 5.10 Deserialization

Deserialization reconstructs the object graph. The snapshot store deserializes carefully: it checks the file size, reads at most the permitted number of bytes, and installs an `ObjectInputFilter` before reading. The filter allows only primitives, strings, and the application's own snapshot classes, and rejects graphs that are too deep or too large. After reading, the store validates the format version and re-checks the domain invariants before handing a snapshot to the model.

```java
// io/SnapshotStore.java (filter, line 100)
private static ObjectInputFilter.Status filter(ObjectInputFilter.FilterInfo info) {
    if (info.depth() > 12 || info.references() > 2_000 || info.streamBytes() > MAX_SAVE_BYTES) {
        return ObjectInputFilter.Status.REJECTED;
    }
    Class<?> type = info.serialClass();
    if (type == null) {
        return ObjectInputFilter.Status.UNDECIDED;
    }
    if (type.isPrimitive() || type == String.class
            || type == SessionSnapshot.class || type == SavedZone.class
            || type == SavedMission.class || type == SavedActivity.class) {
        return ObjectInputFilter.Status.ALLOWED;
    }
    // arrays of allowed components ... otherwise REJECTED
    return ObjectInputFilter.Status.REJECTED;
}
```

*Listing 5.3: An allowlist filter that confines deserialization to the application's own snapshot classes.*

## 5.11 `transient` and Runtime-Only State

Some state must never be serialized: locks, live threads, open stream handles, and references to Swing components. `SessionSnapshot` marks its `sourcePathHint` field `transient`, and, more importantly, the snapshot deliberately contains only *data* — never a live `ResourceAllocator` monitor, never a thread, never a Swing object. When a session is restored, the model reconstructs fresh runtime coordination primitives. This is the practical meaning of the syllabus point that runtime-only state belongs to the live process, not to the saved file.

## 5.12 Session Snapshot

The `SessionSnapshot` is a versioned data-transfer object. On save it is built from an immutable `BasinSnapshot`; on load it is converted back into a `BasinSnapshot` and then validated by `BasinModel.restore`. Because the snapshot is a flat DTO rather than the live aggregate, the save file is compact, stable, and independent of the runtime structure.

## 5.13 Sensor Archive

The sensor archive is a versioned binary file. Its first two integers are a magic marker (`0x42574152`) and a format version (1); when an existing archive is opened, the constructor reads and checks these before appending, so a file that is not a BasinWatch archive — or that was written by an incompatible version — is rejected immediately.

## 5.14 Operational Journal

The operational journal is an append-only UTF-8 text file. Every event message is written with a timestamp and category. To avoid an operating-system call per line, the journal buffers writes and flushes only every twelfth line, or immediately when the category contains `WARNING`, `COMPLETE`, or `ALLOCATED` — the categories an operator is most likely to want preserved promptly.

```java
// io/OperationalJournal.java (append, line 22)
public synchronized void append(ActivityEntry entry) throws IOException {
    writer.write(DateTimeFormatter.ISO_INSTANT.format(entry.at()));
    writer.write(" | ");
    writer.write(entry.category().replace('\n', ' '));
    writer.write(" | ");
    writer.write(entry.message().replace('\n', ' '));
    writer.newLine();
    pendingLines++;
    if (pendingLines >= 12 || entry.category().contains("WARNING")
            || entry.category().contains("COMPLETE") || entry.category().contains("ALLOCATED")) {
        writer.flush();
        pendingLines = 0;
    }
}
```

*Listing 5.4: Buffered journal writes with category-sensitive flushing.*

## 5.15 Report Generation

The report writer produces a human-readable situation report in UTF-8 text. Each report has four sections — zone conditions, available resources, response operations, and recent activity — and a timestamped filename that includes a short random suffix so that successive reports never collide.

## 5.16 Save and Restore Workflow

Figure 5.1 shows the complete save and restore workflow. Saving pauses the feed if it is live, waits for accepted events to drain, builds and validates the snapshot, encodes it to a bounded byte array, writes it to a temporary file, and then moves that file into place with an atomic move where the file system supports it. Restoring checks the file size, applies the input filter, validates the format version and the domain invariants, and rebuilds fresh runtime primitives.

[[FIG:fig5_2_save_restore.png|Figure 5.1: Session save and restore flow.]]

The atomic move is the reason the save is safe against interruption: a partially written temporary file never replaces a valid save. If the move must fall back to a non-atomic replacement on a file system that does not support atomic moves, the code does so explicitly rather than silently, and it deletes the temporary file if the move did not happen.

%%% CHAPTER 6 %%%

# CHAPTER 6: MULTITHREADING AND CONCURRENCY

## 6.1 Need for Concurrency

The simulation is concurrent by nature. Observations must be produced on their own schedule, independently of how quickly the operator acts and of how quickly earlier observations are processed. The interface must remain responsive while that happens. Missions progress independently of any single event. If all of this were done on one thread, the interface would stall whenever the simulation worked, and the very behaviour the project exists to demonstrate — sustained coordination under change — would be impossible.

## 6.2 Process Versus Thread

A process has its own address space and resources; a thread shares the address space of its process with its siblings. BasinWatch is a single process. Within it, several threads share one heap, which is precisely why the shared model must be guarded: threads can see each other's data, so correctness depends on synchronisation rather than on isolation.

## 6.3 Thread Lifecycle

Java's `Thread.State` enumeration defines the states a thread can occupy: `NEW`, `RUNNABLE`, `BLOCKED`, `WAITING`, `TIMED_WAITING`, and `TERMINATED`. Two clarifications matter for correctness. First, Java does **not** define a separate `RUNNING` state; a thread that is executing or ready to execute is reported as `RUNNABLE`. Second, a thread that calls `wait()` enters `WAITING` and **releases** its monitor, whereas a thread that calls `Thread.sleep()` enters `TIMED_WAITING` and **does not** release its monitor. These distinctions are not academic; they determine whether other threads can make progress. Figure 6.1 shows the states as BasinWatch uses them.

[[FIG:fig6_1_thread_lifecycle.png|Figure 6.1: Java thread lifecycle as used by BasinWatch.]]

## 6.4 Thread

`Thread` represents an execution path. The project uses two subclasses — `SensorFeed` and `ArchiveWorker` — because each owns a distinct lifecycle and a blocking endpoint. Both are given explicit names (`basin-sensor-feed`, `basin-sensor-archive`) so that diagnostics can report them truthfully.

```java
// engine/SensorFeed.java (run, line 33)
public void run() {
    try {
        while (running && !isInterrupted()) {
            long tick = tickSequence.incrementAndGet();
            for (int index = 0; index < zoneIds.size() && running; index++) {
                double rainfall = (2.0 + random.nextDouble() * 14.0) * settings.stormIntensity();
                double rise = (0.3 + random.nextDouble() * 1.6) * settings.stormIntensity();
                SensorReading reading = new SensorReading(tick, "G-" + zoneIds.get(index),
                        zoneIds.get(index), rainfall, rise);
                destination.write(reading.encode());
                destination.write('\n');
            }
            destination.write("PULSE|" + tick + '\n');
            destination.flush();
            Thread.sleep(settings.intervalMillis());
        }
    } catch (InterruptedException ex) {
        interrupt();
    } catch (IOException ex) {
        if (running) {
            failureReporter.accept("Sensor channel stopped unexpectedly: " + ex.getMessage());
        }
    } finally {
        try {
            destination.close();
        } catch (IOException ex) {
            if (running) {
                failureReporter.accept("Could not close sensor channel: " + ex.getMessage());
            }
        }
    }
}
```

*Listing 6.1: The sensor feed writes one interval of observations, flushes, and then sleeps until the next interval.*

## 6.5 Runnable

`Runnable` separates a task from the thread that executes it. The intake task and the response workers implement `Runnable` rather than extending `Thread`, because they are jobs that can be scheduled by worker threads. This is the recommended division: inherit `Thread` only when the thread itself has a lifecycle to own; implement `Runnable` when the work is a task.

```java
// engine/SensorIntake.java (run, line 26)
public void run() {
    try (source) {
        String line;
        while ((line = source.readLine()) != null) {
            BasinEvent event;
            try {
                if (line.startsWith("PULSE|")) {
                    event = new SimulationPulse(Long.parseLong(line.substring(6)));
                } else {
                    event = SensorReading.parse(line);
                }
            } catch (IllegalArgumentException ex) {
                warningReporter.accept("Discarded malformed sensor record: " + ex.getMessage());
                continue;
            }
            if (!destination.put(event)) {
                return;
            }
            acceptedReporter.accept(event.category());
        }
    } catch (IOException ex) {
        warningReporter.accept("Sensor intake ended with an I/O error: " + ex.getMessage());
    }
}
```

*Listing 6.2: The intake task reads complete lines, validates each record, and enqueues accepted events.*

## 6.6 Sensor Feed

The sensor feed is the producer. It increments a shared tick counter, emits one reading per zone, writes a pulse to mark the interval, flushes the pipe, and sleeps until the next interval. Its loop condition checks both a `running` flag and the interrupt status, so shutdown is cooperative rather than abrupt.

## 6.7 Sensor Intake

The intake task is the bridge between the character-pipe transport and the event buffer. It reads complete lines, distinguishes pulses from readings, parses and validates each record, and enqueues accepted events. A malformed record is logged and discarded; it never terminates the intake task, which is what allows the simulation to survive noisy input.

[[FIG:fig8_3_sequence_sensor.png|Figure 6.5: Sequence diagram of the sensor and event pipeline.]]

## 6.8 Event Buffer

The event buffer is a bounded, monitor-protected queue of capacity ninety-six. It is the point at which production and consumption meet, and it is where the project's most important synchronisation lives.

| Operation | Condition | Behaviour |
|---|---|---|
| `put(event)` | Buffer full | Waits until space is available or the buffer closes |
| `offerAll(batch)` | Batch larger than free space | Rejects the whole batch without partial insertion |
| `take()` | Buffer empty | Waits until an event arrives or the buffer closes |
| `complete()` | No event in flight | Throws; otherwise decrements the in-flight count |
| `close()` | Any | Sets closed and wakes all waiters |

*Table 6.1: Event buffer operations and their conditions.*

## 6.9 Producer-Consumer Pattern

The producer-consumer pattern decouples the rate of production from the rate of consumption through a buffer. In BasinWatch, the intake task produces and the response workers consume. The buffer is bounded, so a fast producer cannot exhaust memory; instead it experiences back-pressure and waits. The pattern is what allows the two sides to run at their own speeds while remaining correct.

[[FIG:fig6_2_producer_consumer.png|Figure 6.2: The bounded producer-consumer event buffer.]]

## 6.10 `wait()`

`wait()` suspends the calling thread until another thread signals it, and it **releases the object's monitor** while the thread waits, so other threads can enter the synchronized region. In BasinWatch, a consumer calls `wait()` while the buffer is empty and a producer calls `wait()` while the buffer is full.

## 6.11 `notifyAll()`

`notifyAll()` wakes every thread waiting on the monitor. The project uses `notifyAll()` rather than `notify()` because both producers and consumers may be waiting, and it is impossible to know which single thread should be woken. Every state change — adding an event, removing an event, completing an event, or closing the buffer — is followed by `notifyAll()`.

```java
// engine/EventBuffer.java (put, line 23)
public synchronized boolean put(BasinEvent event) throws InterruptedException {
    if (event == null) {
        throw new IllegalArgumentException("Event is required.");
    }
    while (!closed && events.size() == capacity) {
        waitingProducers++;
        try {
            wait();
        } finally {
            waitingProducers--;
        }
    }
    if (closed) {
        return false;
    }
    events.addLast(event);
    notifyAll();
    return true;
}
```

*Listing 6.3: A producer waits in a `while` loop while the buffer is full, then signals on insertion.*

## 6.12 Synchronization

Synchronisation prevents two threads from executing a critical section simultaneously. The project uses twenty-eight synchronized members. The critical sections are deliberately short: they contain validation and state arithmetic, never I/O and never a wait on another monitor.

## 6.13 Monitor Locks

Every Java object has an intrinsic monitor, entered by a `synchronized` block or method. The event buffer's methods are synchronized on the buffer itself, so `put`, `take`, `complete`, and `close` are mutually exclusive and their condition checks are atomic with respect to one another. The buffer's condition checks occur in `while` loops rather than `if` statements, because a woken thread must re-check the condition: between the wake-up and the reacquisition of the monitor, another thread may have changed the state.

## 6.14 Resource Reservation

Response missions require several resource types at once. A pump deployment needs a pump and a field crew; a levee reinforcement needs a levee crew and a supply truck; an evacuation needs an evacuation vehicle and a field crew. The allocator must reserve all of a mission's requirements or none of them. Table 6.2 lists the standard resource catalogue, and Table 6.3 lists each mission type with its duration, effect, and requirements.

| Resource type | Standard stock |
|---|---|
| Portable pump | 3 |
| Levee crew | 3 |
| Supply truck | 2 |
| Evacuation vehicle | 2 |
| Field crew | 4 |

*Table 6.2: Response resource catalogue and standard stock.*

| Mission type | Duration (ticks) | Water effect (m) | Requirements |
|---|---|---|---|
| Pump deployment | 8 | 0.62 | 1 pump, 1 field crew |
| Levee reinforcement | 10 | 0.0 | 1 levee crew, 1 supply truck |
| Evacuation | 6 | 0.0 | 1 evacuation vehicle, 1 field crew |

*Table 6.3: Mission types, durations, effects, and resource requirements.*

```java
// domain/ResourceAllocator.java (tryReserve, line 36)
public synchronized boolean tryReserve(Map<ResourceType, Integer> request) {
    validateRequest(request);
    for (Map.Entry<ResourceType, Integer> entry : request.entrySet()) {
        if (available.get(entry.getKey()) < entry.getValue()) {
            return false;
        }
    }
    request.forEach((type, amount) -> available.put(type, available.get(type) - amount));
    return true;
}
```

*Listing 6.4: The check and the decrement occur in one synchronized method, so reservation is all-or-nothing.*

## 6.15 Atomic Resource Allocation

The reservation is atomic because the availability check and the decrement happen inside a single synchronized method. Two dispatches running at the same instant cannot both observe the same final pump as available: the first to acquire the monitor decrements it, and the second finds it unavailable. Figure 6.3 shows the flow, and the test suite demonstrates it with twenty-four simultaneous contenders, of which exactly one succeeds.

[[FIG:fig6_3_resource_allocation.png|Figure 6.3: Atomic resource reservation and release.]]

## 6.16 Concurrent Missions

Several missions can be active at once, each with its own progress. Because missions advance deterministically on simulation pulses rather than on worker sleep timing, their progress does not depend on which worker happened to process which event. On completion, a mission releases exactly the resources it reserved.

## 6.17 Deadlock Risk

A deadlock occurs when two or more threads each hold a resource the others need, producing a circular wait. The classic hazard in a system like this would be an allocator that acquired several per-resource locks in different orders for different missions: one mission might hold the pump lock and wait for the crew lock while another holds the crew lock and waits for the pump lock. BasinWatch avoids this hazard by construction.

## 6.18 Deadlock Prevention

Prevention rests on three rules. First, there is a **single** inventory monitor: all reservations go through one synchronized allocator method rather than through several per-resource locks, so there is no lock order to get wrong. Second, no lock is held during I/O, sleep, callbacks, or a wait on a different monitor, so a thread never holds one resource while blocking on another. Third, where the model and the inventory must change together, the model owns the documented lock order. The result is that the normal operation of the application has no circular-wait precondition. It is worth stating plainly that synchronisation alone does not prevent all deadlocks; what prevents this particular deadlock is the single-monitor discipline and the refusal to block while holding a lock.

## 6.19 Thread Interruption

Interruption is the cooperative mechanism by which one thread asks another to stop. The project's workers and the feed check their interrupt status and, when interrupted, preserve the status (`Thread.currentThread().interrupt()`) and return. Preserving the interrupt status matters because a caller further up the stack may still need to know that an interruption occurred.

## 6.20 Graceful Shutdown

Shutdown is explicit and bounded. The engine stops the feed, closes the event buffer (which wakes every waiter), joins each response worker with a timeout, drains and finishes the archive worker, closes the database service, writes an automatic `last-session.bws`, and closes the journal. If any join times out or any I/O fails, the engine reports the failure rather than pretending the shutdown succeeded.

```java
// engine/BasinEngine.java (closeEngine, condensed from line 340)
IOException failure = null;
try { stopFeed(); } catch (IOException ex) { failure = ex; }
eventBuffer.close();
for (Thread worker : List.copyOf(responseThreads)) { join(worker, "response worker"); }
if (failure != null || workersAlive()) {
    throw failure != null ? failure
        : new IOException("Background work is still active; operational files remain open.");
}
if (archiveWorker != null && archiveWorker.isAlive()) {
    archiveWorker.finish();
    join(archiveWorker, "sensor archive");
}
databaseService.close();
snapshotStore.save(paths.saves().resolve("last-session.bws"), model.snapshot());
journal.close();
closed = true;
```

*Listing 6.5: Shutdown drains and closes each service in order, reporting rather than hiding failures.*

[[FIG:fig6_4_app_lifecycle.png|Figure 6.4: Application lifecycle from startup to clean close.]]

## 6.21 Thread Priority and Experimental Diagnostics

Java thread priority is a scheduling **hint**, not a guarantee. The platform is free to ignore it, and it must never be used as a correctness or ordering mechanism. BasinWatch respects this: operational ordering comes from explicit severity and timestamp data, not from priority. The one place priority appears is an optional experiment in the systems inspector, which can lower the archive worker's priority to demonstrate that non-urgent background work can be de-emphasised — while the application's correctness remains independent of the setting. The inspector also reports each thread's name, state, and priority, so the operator can see the truth of the scheduling situation rather than assume it.

## 6.22 Concurrency Safety

Concurrency safety in BasinWatch rests on four pillars: a bounded buffer whose condition checks are protected by one monitor and re-checked in loops; a single short critical section for resource reservation; immutable snapshots for every hand-off to the interface; and cooperative interruption with bounded joins for shutdown. Together these make the application safe under concurrent operation, and the test suite exercises each pillar directly.
