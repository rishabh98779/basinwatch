%%% CHAPTER 10 %%%

# CHAPTER 10: TESTING AND VALIDATION

## 10.1 Testing Strategy

The project uses a dependency-free assertion suite rather than an external test framework. The suite is a plain Java program with a `main` method, compiled by Maven and executed with assertions enabled and the SQLite JDBC driver on its classpath by the `scripts/test.ps1` runner. This choice keeps the test infrastructure minimal and transparent: there is no framework to configure, and the whole suite can be read and understood directly.

The strategy is to test *invariants* rather than incidental behaviour. An invariant is a property that must hold no matter how threads are scheduled: a reservation must never over-allocate; a full buffer must never lose an accepted event; a restored session must match the saved one; a corrupt save must never be accepted. Testing invariants is the right approach for a concurrent system, because it is exactly the properties that matter under concurrency that are hardest to observe by hand.

The suite defines three helpers: `check` for a boolean condition, `expect` for an expected exception type, and `await` for a condition that should become true within a timeout. Each helper increments an assertion counter. When the suite was executed during the preparation of this report, it printed:

```
BasinWatch invariant suite passed (76 assertions).
```

*Listing 10.1: The result reported by the invariant suite when executed.*

## 10.2 Unit and Invariant Tests

The first suite, `parsesAndValidatesSensorEvents`, checks that a sensor reading survives an encode-and-parse round trip unchanged, and that malformed input is rejected: a line with a non-numeric field, a negative tick, and an identifier containing an illegal character each raise `IllegalArgumentException`.

## 10.3 Concurrency Tests

Concurrency is tested through the buffer suite, `coordinatesBoundedEventBuffer`, which uses real threads and latches. It verifies that an empty consumer waits on the queue condition, that a producer wakes it with a real event, that a full bounded queue applies back-pressure to a producer, that removing an item releases the waiting producer, and that closing the queue wakes waiters with an explicit end-of-stream result.

## 10.4 Resource Contention Tests

The suite `reservesSharedResourcesAtomically` is the clearest demonstration of the resource invariant. Twenty-four threads are released simultaneously from a start gate, each attempting to reserve the last pump and the last field crew. The suite asserts that **exactly one** reservation succeeds, that the reserved pump becomes unavailable, that a release returns it to stock, that a second release of the same reservation raises `IllegalStateException`, and that the rejected duplicate release does not corrupt the crew inventory.

## 10.5 Buffer Tests

Buffer behaviour is covered by the concurrency suite described in Section 10.3. The buffer's own counters (`waitingConsumers`, `waitingProducers`, `activeConsumers`) make the conditions observable, which is why the suite can wait for a specific condition rather than guessing at a delay.

## 10.6 Persistence Tests

Persistence is covered by two suites. `validatesArchiveHeaders` writes two records to a binary archive, reopens the archive to append a third, and confirms that a file with an invalid header is rejected with `IOException`. `savesRestoresAndRejectsUnsafeSnapshots` saves a model with a reading and an active evacuation, restores it, and confirms that the tick, the zone measurements, the active mission, and the resource inventory all round-trip exactly.

## 10.7 Database Tests

`persistsJdbcHistoryAndTransactions` writes a sensor reading, dispatches a mission, and completes it, then reads all four history categories back. It asserts that the sensor row contains the expected rainfall, that the mission row shows completion, that every resource allocated to the mission was recorded, that exactly two events were committed for the mission, that a parameterized retention delete removes the sensor row, and that no database failures were reported during successful operation.

## 10.8 Session Round-Trip Tests

The snapshot suite and the engine suite together cover session round-tripping. The engine suite saves a live session, confirms the file reaches disk and that a save made during live observations resumes the feed afterwards, then restores the session and confirms that the loaded tick matches the saved tick and that a persisted mission completes through the existing simulation.

## 10.9 Failure Tests

Failure handling is tested directly. The snapshot suite rejects a four-byte corrupt file and a serialized `ArrayList` that is not a BasinWatch session. The database-unavailable suite makes the database path unusable and confirms that the simulation still processes events, that the binary archive and the automatic session save are still written, and that the operational journal records a `DATABASE WARNING`.

## 10.10 Shutdown Tests

The engine suite closes the engine and confirms that a clean shutdown automatically saves `last-session.bws`, that the operational journal is non-empty, and that the binary archive contains its format marker, its version, and at least one typed record.

## 10.11 UI Testing

The user interface was validated by running the application and exercising its controls, and the screenshots in this report are the evidence. Automated GUI testing was not implemented; the interface is a thin layer over the tested engine, and its correctness depends chiefly on the engine's snapshot and status listeners, which the engine suite exercises.

## 10.12 Test Case Table

| Test ID | Component | Scenario | Expected result | Verified result | Status |
|---|---|---|---|---|---|
| T-01 | `SensorReading` | Encode and parse a reading | Round-trips exactly | Round-trips exactly | Pass |
| T-02 | `SensorReading` | Malformed / out-of-range input | `IllegalArgumentException` | Thrown | Pass |
| T-03 | `ResourceAllocator` | 24 threads reserve the last pump+crew | Exactly one succeeds | Exactly one succeeds | Pass |
| T-04 | `ResourceAllocator` | Release then double release | Stock restored; second release throws | `IllegalStateException` | Pass |
| T-05 | `EventBuffer` | Empty consumer waits | Consumer waits; producer wakes it | Verified via counters | Pass |
| T-06 | `EventBuffer` | Full bounded queue | Producer waits (back-pressure) | Verified via counters | Pass |
| T-07 | `EventBuffer` | Close with a waiting consumer | Waiter woken with end-of-stream | Verified | Pass |
| T-08 | `BasinModel` | Dispatch pump; advance to completion | Water falls; pump released; mission completed | Verified | Pass |
| T-09 | `BasinModel` | Levee reinforcement effect | Subsequent runoff reduced | Verified | Pass |
| T-10 | `SnapshotStore` | Save and restore a session | State round-trips exactly | Verified | Pass |
| T-11 | `SnapshotStore` | Corrupt / foreign file | `IOException` | Thrown | Pass |
| T-12 | `SensorArchive` | Valid and invalid headers | Valid appends; invalid rejected | Verified | Pass |
| T-13 | `AppPaths` | Data-dir resolution | Valid accepted; invalid rejected | Verified | Pass |
| T-14 | `DatabaseService` | JDBC insert/select/transaction | Rows and transactions correct | Verified | Pass |
| T-15 | `DatabaseService` | Retention delete | Old rows removed | Verified | Pass |
| T-16 | `BasinEngine` | Full offline session | Events processed; save/restore/report/journal/archive correct | Verified | Pass |
| T-17 | `BasinEngine` | Database unavailable | Simulation and file persistence continue | Verified | Pass |
| T-18 | `BasinEngine` | Clean shutdown | Auto-save written; journal non-empty | Verified | Pass |

*Table 10.1: Test-case summary. Results reflect the executed run of the invariant suite.*

| Suite | Focus | Assertions contributed |
|---|---|---|
| `parsesAndValidatesSensorEvents` | Event parse and validation | Round-trip and rejection checks |
| `reservesSharedResourcesAtomically` | Resource contention | Atomic reservation and release checks |
| `coordinatesBoundedEventBuffer` | Bounded buffer | Waiting, back-pressure, close checks |
| `advancesAndReleasesResponseMissions` | Mission progression | Advance, effect, release checks |
| `savesRestoresAndRejectsUnsafeSnapshots` | Session round-trip | Save/restore and rejection checks |
| `validatesArchiveHeaders` | Binary archive | Header and append checks |
| `resolvesPerUserDataLocations` | Data-dir resolution | Accept and reject checks |
| `persistsJdbcHistoryAndTransactions` | JDBC history | Insert, select, transaction, retention checks |
| `runsACompleteOfflineEngineSession` | Full engine session | Feed, save/restore, report, journal, archive checks |
| `continuesWhenDatabaseIsUnavailable` | Failure isolation | Continue-on-failure checks |

*Table 10.2: Executed evidence summary. The suite reported seventy-six passing assertions in total.*

## 10.13 Results

The invariant suite executed successfully and reported seventy-six passing assertions across its ten suites. Implemented test coverage includes concurrent resource contention, bounded-buffer waiting and closing, event validation and processing, mission progression and release, session round-trip and corrupt-input rejection, binary-archive validation, data-directory resolution, JDBC history and transactions, database-unavailable resilience, and orderly shutdown. No performance figures are claimed, because the suite asserts correctness rather than speed.

## 10.14 Observed Limitations

The suite does not include automated GUI tests, and it does not measure throughput or latency. The resource-contention test uses a small, deterministic scenario rather than a long randomised stress run. These limitations are stated plainly rather than hidden; they are reasonable for a teaching project whose aim is to demonstrate correct concurrency rather than to certify performance.

%%% CHAPTER 11 %%%

# CHAPTER 11: RESULTS AND DISCUSSION

## 11.1 Functional Results

Every function required in Chapter 2 was observed to work in the running application. The application starts, presents six zones, accepts a live observation feed or single-interval steps, allows a storm cell to be injected, validates observations, ranks and highlights risk, maintains a finite inventory, dispatches three mission types, reserves resources atomically, advances and completes missions, returns resources on completion, displays inventory and active operations, writes a journal, archives typed measurements, saves and restores sessions, exports a report, and maintains an optional database history. The screenshots in Chapters 6 and 8 are direct evidence of the interface.

## 11.2 Runtime Workflow

The runtime workflow behaved as designed. The sensor feed produced observations on its interval, the intake task validated and enqueued them, the response workers applied them to the model, and the interface updated on the EDT from immutable snapshots. During live observation the interface remained responsive to selection and dispatch, which is the practical demonstration that the pipeline does not block the UI.

[[FIG:assets/screenshots/02_basin_map.png|Figure 11.1: The basin map and operations timeline during a live run.]]

## 11.3 Resource Allocation Results

Resource allocation was verified both by the test suite and by observation. In the suite, twenty-four simultaneous contenders produced exactly one successful reservation of the final pump and crew, and a duplicate release was rejected without corrupting inventory. In the running application, dispatching missions reduced the available counts and committing units to active operations, and completing a mission returned the units to the available stock. No double allocation was observed.

## 11.4 Persistence Results

All five persistence mechanisms worked. The operational journal accumulated readable timestamped entries; the binary archive was created with its marker and version and contained typed records; the session save wrote a file that could be restored; the report writer produced a multi-section text report; and the session's automatic save on clean exit produced a resumable `last-session.bws`. A representative report generated during verification ran to several kilobytes and contained zone conditions, available resources, response operations, and recent activity.

## 11.5 Database Results

The optional database behaved as designed. During verification, the history accumulated typed rows across all four tables, and the history panel displayed them. The transaction test confirmed that a mission, its resource rows, and its dispatch event are committed together, and the failure test confirmed that an unusable database does not stop the simulation or the file-based persistence.

## 11.6 Concurrency Results

Concurrency results were positive and, importantly, *bounded*. The buffer applied back-pressure rather than growing without limit; the allocator never over-allocated under contention; snapshots were delivered to the EDT without any observed inconsistency; and shutdown drained accepted work and closed files within the bounded timeout. Thread states reported by the inspector were the platform's own truthful states, and the optional archive-priority experiment changed a scheduling hint without affecting correctness.

## 11.7 OOP Learning Outcomes

The project produced concrete learning outcomes that map directly to the syllabus. Encapsulation was used to make invalid domain states unrepresentable. Abstraction through an event interface kept the pipeline stable. Narrow inheritance was used only where a framework contract required it. Polymorphism localised the differences between events, missions, and risks. Composition gave the model a single owner for state that must remain consistent. Enums replaced error-prone string categories. Immutability was the mechanism that made concurrent reads safe. Exception handling kept failures visible and local. Serialization and JDBC demonstrated persistence through two very different APIs. In short, the object-oriented concepts were not studied in the abstract; they were the tools that solved the domain's problems.

## 11.8 Requirement Achievement

| Objective | Target | Outcome | Status |
|---|---|---|---|
| O1 Concurrent pipeline | Producer-consumer with responsive UI | Implemented and exercised | Achieved |
| O2 Atomic allocation | All-or-nothing reservation | Verified (1 of 24 succeeds) | Achieved |
| O3 Bounded buffering | Bounded buffer with back-pressure and drain | Verified | Achieved |
| O4 Multi-format persistence | Journal, archive, snapshot, report | All four implemented | Achieved |
| O5 Safe session recovery | Save/restore with corrupt-input rejection | Verified | Achieved |
| O6 Optional relational history | SQLite via JDBC, isolated failure | Verified | Achieved |
| O7 Syllabus demonstration | Core OOP/Java concepts applied | Documented in Chapter 4 | Achieved |

*Table 11.1: Requirement achievement. Status reflects verified functionality, not measured performance.*

| Observation | Evidence |
|---|---|
| Application starts and shows the console | Screenshot Figure 8.1 |
| Live simulation with active missions | Screenshot Figure 8.2 |
| Zone risk and water levels update | Screenshots Figures 8.2 and 11.1 |
| Operations list shows mission progress | Screenshot Figure 8.6 |
| Systems inspector reports thread states and queue metrics | Screenshot Figure 8.8 |
| Database history table populated | Screenshot Figure 8.4 |
| Session save and restore work | Invariant suite (T-10, T-16) |
| Situation report generated | Report writer (Chapter 5); Appendix B |
| Atomic reservation under contention | Invariant suite (T-03) |

*Table 11.2: Verified runtime observations and their evidence.*

## 11.9 Discussion

Two observations deserve emphasis. First, the design's safety comes from *structure*, not from luck. The single inventory monitor, the bounded buffer, and immutable snapshots each remove a specific class of bug by construction. The project does not rely on threads happening to run in a convenient order, and it does not treat priority as a correctness mechanism. Second, the simulation's honesty is itself a design feature. By labelling the map as schematic, the parameters as illustrative, and the application as an offline planning tool, the project avoids the trap of presenting a teaching artefact as an operational system. The result is a program that is both instructive about object-oriented programming and candid about its own limits.

%%% CHAPTER 12 %%%

# CHAPTER 12: CONCLUSION AND FUTURE SCOPE

## 12.1 Conclusion

BasinWatch demonstrates that a single, offline Java desktop application can model a genuinely concurrent coordination problem and solve it with disciplined object-oriented design. A bounded producer-consumer pipeline keeps the interface responsive while observations and operations proceed independently; a short synchronized transaction makes resource reservation atomic; immutable snapshots make the hand-off to the interface safe; and a family of persistence mechanisms — text journal, binary archive, session snapshot, readable report, and optional embedded database — preserves the run in forms suited to human review, typed replay, and structured query. The implementation is supported by an executed assertion suite that reported seventy-six passing assertions across concurrency, resource contention, buffering, persistence, database, session round-trip, failure, and shutdown scenarios. Every mechanism described in this report is drawn from the actual source, and every limitation is stated rather than hidden.

## 12.2 Achievements

The project achieved a complete, runnable, tested simulation with a clean package structure, a documented architecture, a demonstrated concurrency model, a safe and versioned persistence design, an optional relational history, and a readable interface. It produced a substantial body of original code and a matching test suite, and it connected each part of that work to the object-oriented syllabus.

## 12.3 Current Limitations

The basin map is schematic and not geospatially accurate. The simulation parameters are illustrative, not calibrated hydrology. The application is single-user and offline, does not ingest real sensors, does not issue alerts, and controls no real infrastructure. Automated GUI testing was not implemented. Performance is not measured. The session format is application-private and versioned.

## 12.4 Future Improvements

Several improvements follow directly from the repository's own stated future direction and from the design: importing a user-authored scenario format; adding replay scrubbing; exporting CSV reports; improving map editing; adding explicit fault-injection scenarios for resource contention; and validating a hydrology model before any real-world advisory use. Each is a natural extension of the existing architecture rather than a rewrite.

## 12.5 Possible Extensions

| Extension | Description | Technology |
|---|---|---|
| Scenario import | Load a user-defined basin scenario | Character streams + validation |
| Replay scrubbing | Step backward and forward through a recorded run | Binary archive + snapshot replay |
| CSV export | Export history and reports as CSV | Character streams |
| Map editing | Let the operator place zones and stations | Swing custom painting |
| Fault injection | Deliberately contend resources to demonstrate failure | Test harness + allocator |
| Hydrology validation | Replace illustrative parameters with a validated model | Numerical modelling (out of current scope) |

*Table 12.1: Possible future extensions.*

%%% REFERENCES %%%

# REFERENCES

1. Oracle Corporation. *Java Platform, Standard Edition 17 API Specification*. Available: https://docs.oracle.com/en/java/javase/17/docs/api/
2. Oracle Corporation. *The Java Tutorials: Concurrency*. Available: https://docs.oracle.com/javase/tutorial/essential/concurrency/
3. Oracle Corporation. *The Java Tutorials: Basic I/O*. Available: https://docs.oracle.com/javase/tutorial/essential/io/
4. Oracle Corporation. *Java Object Serialization Specification*. Available: https://docs.oracle.com/en/java/javase/17/docs/specs/serialization/
5. Oracle Corporation. *Interface ObjectInputFilter (Java SE 17)*. Available: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/ObjectInputFilter.html
6. Oracle Corporation. *Class Thread (Java SE 17)*. Available: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Thread.html
7. Oracle Corporation. *The Java Tutorials: Creating a GUI With Swing*. Available: https://docs.oracle.com/javase/tutorial/uiswing/
8. Oracle Corporation. *The Java Tutorials: JDBC Database Access*. Available: https://docs.oracle.com/javase/tutorial/jdbc/
9. Apache Software Foundation. *Apache Maven Project Documentation*. Available: https://maven.apache.org/
10. SQLite Consortium. *SQLite Documentation*. Available: https://www.sqlite.org/docs.html
11. Xerial Project. *sqlite-jdbc: SQLite JDBC Driver*. Available: https://github.com/xerial/sqlite-jdbc
12. Bloch, J. *Effective Java*, 3rd ed. Addison-Wesley, 2018.
13. Horstmann, C. S. *Core Java, Volume I — Fundamentals*, 11th ed. Pearson, 2018.
14. Goetz, B. et al. *Java Concurrency in Practice*. Addison-Wesley, 2006.

%%% APPENDICES %%%

# APPENDIX A — IMPORTANT SOURCE CODE

The following excerpts are reproduced verbatim from the project. Line numbers refer to the repository revision used for this report.

**A.1 Application startup** — `app/BasinWatchApp.java` (lines 20–61)
**A.2 Engine feed startup** — `engine/BasinEngine.java` (lines 279–303)
**A.3 Engine event processing** — `engine/BasinEngine.java` (lines 441–472)
**A.4 Engine shutdown** — `engine/BasinEngine.java` (lines 340–417)
**A.5 Sensor feed** — `engine/SensorFeed.java` (lines 33–72)
**A.6 Sensor intake** — `engine/SensorIntake.java` (lines 26–50)
**A.7 Event buffer** — `engine/EventBuffer.java` (lines 23–84)
**A.8 Resource allocator** — `domain/ResourceAllocator.java` (lines 27–64)
**A.9 Basin model dispatch** — `domain/BasinModel.java` (lines 103–125)
**A.10 Sensor archive** — `io/SensorArchive.java` (lines 19–51)
**A.11 Snapshot store** — `io/SnapshotStore.java` (lines 23–122)
**A.12 Operational journal** — `io/OperationalJournal.java` (lines 18–41)
**A.13 JDBC dispatch transaction** — `db/MissionRepository.java` (lines 31–54)
**A.14 Parameterized query** — `db/SensorReadingRepository.java` (lines 45–71)

# APPENDIX B — TEST RESULTS

The invariant suite was executed with assertions enabled and the SQLite JDBC driver on the classpath. It reported:

```
BasinWatch invariant suite passed (76 assertions).
```

The ten suites are: `parsesAndValidatesSensorEvents`, `reservesSharedResourcesAtomically`, `coordinatesBoundedEventBuffer`, `advancesAndReleasesResponseMissions`, `savesRestoresAndRejectsUnsafeSnapshots`, `validatesArchiveHeaders`, `resolvesPerUserDataLocations`, `persistsJdbcHistoryAndTransactions`, `runsACompleteOfflineEngineSession`, and `continuesWhenDatabaseIsUnavailable`.

# APPENDIX C — DATABASE SCHEMA

```sql
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    zone TEXT NOT NULL,
    water_level REAL NOT NULL,
    rainfall REAL NOT NULL,
    risk_level TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS missions (
    id TEXT PRIMARY KEY,
    mission_type TEXT NOT NULL,
    zone TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE TABLE IF NOT EXISTS resource_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    mission_id TEXT NOT NULL REFERENCES missions(id),
    timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS operational_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    zone TEXT,
    message TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_time ON sensor_readings(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_missions_created ON missions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_time ON operational_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_resource_usage_time ON resource_usage(timestamp DESC);
```

# APPENDIX D — CONFIGURATION AND BUILD INFORMATION

**Build.** The project targets Java 17 and is built with Maven. The only runtime dependency is `org.xerial:sqlite-jdbc`. The Maven Shade plugin bundles the driver and sets the main class so that a single executable JAR results.

```
mvn package
java -jar target/basinwatch-1.0.0.jar
```

**Data locations.** On Windows, `%APPDATA%\BasinWatch\data\`; elsewhere, `~/.basinwatch/data/`. Subfolders: `logs`, `archive`, `saves`, `reports`, and the file `basinwatch.db`. The location can be overridden with `--data-dir <folder>`.

**Default parameters.** Observation interval 1500 ms (range 350–8000); storm intensity 1.0 (range 0.2–2.5); event-buffer capacity 96; three response workers; save-size limit 5 MB; database queue 2048; history limit 200; sensor retention 30 days.

# APPENDIX E — ADDITIONAL SCREENSHOTS

Screenshots of the application at startup, during live operation, and across its tabs are included in Chapters 6 and 8. They were captured from the running application.

# APPENDIX F — ADDITIONAL DIAGRAMS

The editable PlantUML sources for every diagram in this report are retained with the project so that the diagrams can be regenerated or amended. They cover the system context, use case, high-level architecture, package structure, data flow, runtime workflow, domain and engine class structure, thread map, persistence architecture, database ER model, session flow, thread lifecycle, producer-consumer buffer, resource allocation, application lifecycle, JDBC architecture, sequence diagrams for the sensor pipeline and resource dispatch, the operator activity diagram, and the OOP concept map.
