%%% CHAPTER 3 %%%

# CHAPTER 3: SYSTEM ARCHITECTURE AND DESIGN

## 3.1 Overall Architecture

BasinWatch is a single-process, offline desktop application organised into four logical layers. The **presentation layer** (`com.basinwatch.app`) consists of Swing components that are owned exclusively by the event-dispatch thread (EDT). The **application and engine layer** (`com.basinwatch.engine`) owns the simulation's lifecycle and its background services. The **domain layer** (`com.basinwatch.domain`) holds the model of the basin — zones, events, resources, and missions — and enforces its invariants. The **persistence layer** (`com.basinwatch.io` and `com.basinwatch.db`) writes and reads operational files and the optional embedded database.

The layering is enforced by direction of dependency rather than by a framework: the presentation layer depends on the engine and domain; the engine depends on the domain and persistence; the domain depends on nothing outside itself and the standard library. This keeps the domain testable in isolation and prevents file or database concerns from leaking into the model.

## 3.2 High-Level System Architecture

Figure 3.1 shows the four layers and the principal classes in each. The engine is the hub: it owns the sensor feed, intake task, event buffer, response workers, archive worker, journal, snapshot store, report writer, and database service, and it connects them to the domain model.

[[FIG:fig3_1_highlevel_arch.png|Figure 3.1: BasinWatch high-level system architecture.]]

## 3.3 Layer and Package Architecture

The project is divided into six packages. Figure 3.2 shows the package dependency graph, and Table 3.1 summarises each package's responsibility.

[[FIG:fig3_2_package.png|Figure 3.2: Package diagram for the six BasinWatch packages.]]

| Package | Responsibility | Notable types |
|---|---|---|
| `com.basinwatch.app` | Swing entry point, frame, map panel, database history panel | `BasinWatchApp`, `MainFrame`, `BasinMapPanel`, `DatabaseHistoryPanel` |
| `com.basinwatch.domain` | Model, events, resources, missions, risk | `BasinModel`, `BasinZone`, `BasinEvent`, `ResourceAllocator`, `ResponseMission` |
| `com.basinwatch.engine` | Lifecycle, threading, buffering, workers, diagnostics | `BasinEngine`, `SensorFeed`, `SensorIntake`, `EventBuffer`, `ArchiveWorker` |
| `com.basinwatch.io` | File persistence, snapshots, archive, reports | `AppPaths`, `SnapshotStore`, `SensorArchive`, `OperationalJournal`, `ReportWriter` |
| `com.basinwatch.db` | Optional embedded SQLite history via JDBC | `DatabaseService`, `DatabaseManager`, repositories |
| `com.basinwatch.learning` | In-application architecture notes | `ArchitectureCard`, `LearningCatalog` |

*Table 3.1: Package responsibilities.*

## 3.4 Component Responsibilities

Table 3.2 lists the major runtime components, the thread on which each executes, and its responsibility. The threading column is central to the architecture and is examined in depth in Chapter 6.

| Component | Runs on | Responsibility |
|---|---|---|
| `MainFrame` and panels | Swing EDT | Render immutable snapshots; capture operator actions |
| `BasinEngine` | Caller + `basin-control` executor | Own lifecycle; start/pause/save/load/report/close |
| `SensorFeed` | `basin-sensor-feed` thread | Emit encoded observations and pulses on an interval |
| `SensorIntake` | `basin-sensor-intake` thread | Read, parse, validate, and enqueue events |
| `EventBuffer` | Shared (guarded) | Bounded producer-consumer queue with `wait()`/`notifyAll()` |
| `ResponseWorker` (×3) | `basin-response-1..3` threads | Apply events to the model; advance and complete missions |
| `ArchiveWorker` | `basin-sensor-archive` thread | Write typed measurements to the binary archive |
| `DatabaseService` | `basin-database` thread | Write/read SQLite history off the EDT |
| `BasinModel` | Guarded by `synchronized` | Own zones, inventory, missions, activity; return snapshots |
| `ResourceAllocator` | Guarded by `synchronized` | Atomic all-or-nothing reservation and release |

*Table 3.2: Component responsibilities and threading.*

## 3.5 Data Flow

Figure 3.3 presents a level-one data-flow view. Observations originate in the sensor feed, are validated at intake, are buffered, are applied to the model by response workers, and result in an immutable snapshot delivered to the interface and in records written to the journal, archive, saves, and database.

[[FIG:fig3_3_dfd.png|Figure 3.3: Level-one data-flow diagram.]]

## 3.6 Runtime Workflow

Figure 3.4 shows the end-to-end runtime workflow. The producer writes encoded records to a `PipedWriter`; the intake task reads them through a `PipedReader` wrapped in a `BufferedReader`; accepted events enter the bounded buffer; response workers take them, apply them to the model under synchronization, and publish an immutable snapshot to the EDT.

[[FIG:fig3_4_runtime_workflow.png|Figure 3.4: BasinWatch runtime workflow.]]

The engine starts the feed by constructing a connected pair of piped streams and starting the intake thread before the feed thread, so that a reader exists before any bytes are written. Listing 3.1 shows this startup.

```java
// engine/BasinEngine.java (startFeed, line 279, condensed)
PipedWriter writer = new PipedWriter();
PipedReader reader = new PipedReader(writer, 8_192);
feedWriter = writer;
intakeThread = new Thread(new SensorIntake(
        new BufferedReader(reader), eventBuffer, this::reportFailure,
        ignored -> publishDiagnosticsStatus()), "basin-sensor-intake");
sensorFeed = new SensorFeed(writer, List.of("UPR", "MIL", "NOR", "OLD", "MAR", "SOU"),
        settings, tickSequence, this::reportFailure);
intakeThread.start();
sensorFeed.start();
```

*Listing 3.1: The engine connects the sensor feed and intake task through piped character streams, starting the reader first.*

When an event reaches a worker, the engine processes it inside a synchronized block that captures the model state before and after the transition, so that persistence can reason about what changed. Listing 3.2 shows the core of this method.

```java
// engine/BasinEngine.java (process, line 441, condensed)
private void process(BasinEvent event) throws IOException, InterruptedException {
    BasinSnapshot before;
    BasinSnapshot after;
    List<String> messages;
    synchronized (model) {
        before = model.snapshot();
        messages = model.process(event);
        after = model.snapshot();
    }
    // ... journal each message, archive the reading, persist database deltas ...
    publishSnapshot();
}
```

*Listing 3.2: Event processing captures the before-and-after model state under synchronization, then performs I/O outside the lock.*

Note that the lock is held only while the model transition is computed. Journal writing, archive submission, and database enqueueing happen after the synchronized block, so no blocking I/O is performed while holding the model lock.

## 3.7 Class Relationships

Figures 3.5 and 3.6 show the domain and the engine/UI class relationships respectively. The domain is an aggregate: `BasinModel` owns six `BasinZone` objects, up to five hundred `ResponseMission` objects, one `ResourceAllocator`, and a bounded deque of `ActivityEntry` records. Events implement the `BasinEvent` interface. The engine composes its services and holds a small list of response-worker threads.

[[FIG:fig3_5_domain_class.png|Figure 3.5: Domain class diagram.]]

[[FIG:fig3_6_engine_ui_class.png|Figure 3.6: Engine and UI class diagram.]]

## 3.8 Concurrency Architecture

Concurrency is the architectural spine of the application. Figure 3.7 maps the threads and their interactions. The Swing EDT owns all components. The `basin-control` daemon executor serialises lifecycle actions such as start, pause, save, load, report, and close. The sensor feed and intake form the production side of the pipeline. Three response workers form the consumption side. The archive worker and database service are separate, low-urgency writers. Immutable snapshots cross from workers to the EDT.

[[FIG:fig3_7_thread_map.png|Figure 3.7: Thread and concurrency map.]]

The architecture deliberately avoids nested locks in the normal path. The event buffer uses its own intrinsic monitor; the resource allocator uses its own; the model uses its own. The allocator's critical section contains only inventory validation and arithmetic — never I/O, never a wait on a different monitor — which removes the circular-wait precondition from normal operation. Section 6.17 examines the deadlock hazard and its prevention in detail.

## 3.9 Persistence Architecture

Figure 3.8 shows the persistence architecture. Five mechanisms serve five purposes: a UTF-8 text journal for human-readable events; a versioned binary archive for typed measurements; a versioned session snapshot for recovery; UTF-8 text reports for review; and an embedded SQLite database for queryable history. Each mechanism uses the stream or API appropriate to its data, and each is isolated so that a failure in one does not corrupt the others.

[[FIG:fig3_8_persistence_arch.png|Figure 3.8: Persistence architecture.]]

## 3.10 Database Architecture

The optional database layer wraps SQLite behind a single-threaded service. All SQL runs on the `basin-database` thread, never on the EDT. Repositories open fresh connections, use prepared statements, and close resources with try-with-resources; linked mission records are written in a transaction. Figure 3.9 is the entity-relationship diagram for the four tables, and Chapter 7 documents the layer fully.

[[FIG:fig3_9_er.png|Figure 3.9: SQLite database entity-relationship diagram.]]

## 3.11 Error Boundaries

The architecture places a deliberate boundary around each category of failure so that one failure cannot silently become another. Table 3.3 summarises the boundaries.

| Boundary | Failure handled | Behaviour |
|---|---|---|
| Sensor intake | Malformed record | Log a warning and discard; intake continues |
| Domain constructors/commands | Impossible zone, negative quantity, invalid transition | Throw `IllegalArgumentException` / `IllegalStateException` |
| Resource allocator | Insufficient units | Return `false`; record a typed rejection |
| Snapshot store | Missing, oversized, corrupt, or unexpected class | Throw `IOException` with an actionable message |
| Sensor archive | Bad marker or version | Throw `IOException` on open |
| Database service | `SQLException` | Report and isolate; simulation continues |
| Response worker | Runtime or I/O failure | Report with event context; continue unrelated work |
| Shutdown | Interrupted or timed-out join | Preserve interrupt status; report, do not pretend success |
| UI action | Any reported failure | Show a status banner or dialog; keep prior valid state |

*Table 3.3: Error boundaries.*

## 3.12 Security and Safe Persistence Considerations

Although the application handles no secrets and has no network surface, it treats its own save files as untrusted input. The snapshot store bounds the payload to five megabytes, reads at most one byte beyond that limit, and installs an `ObjectInputFilter` that rejects any class outside an explicit allowlist and any object graph exceeding shallow depth or reference limits. Because Java deserialization of arbitrary classes is a well-known hazard, restricting it to the application's own snapshot classes is a deliberate safety measure, not an afterthought. The database layer uses prepared statements with bound parameters for all application data, which prevents SQL injection through recorded values.

## 3.13 Design Decisions and Rationale

| Decision | Alternative considered | Rationale |
|---|---|---|
| Bounded event buffer (capacity 96) | Unbounded queue | Bounds memory and applies visible back-pressure |
| Three response workers | One worker or a fixed thread pool per event | Keeps a small, predictable worker set while allowing overlap |
| Immutable snapshots to the EDT | Let the UI read the live model | Avoids exposing mutable state across threads |
| One short allocator monitor | Multiple per-resource locks | Removes circular-wait risk and simplifies reasoning |
| Piped character streams for observations | Direct method calls or a shared queue | Demonstrates the piped-stream mechanism and decouples producer from consumer |
| Versioned, filtered serialization | Plain serialization or JSON | Safe, self-describing local saves with corrupt-input rejection |
| Embedded SQLite via raw JDBC | An ORM or an external database server | Keeps the database real, offline, and dependency-free |
| Text journal separate from binary archive | A single format | Serves human review and typed replay with the right stream each |
| Priority as an optional experiment | Priority-based scheduling | Priority is nondeterministic and must not affect correctness |

*Table 3.4: Design decisions and rationale.*
