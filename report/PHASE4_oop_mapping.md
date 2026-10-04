# BasinWatch Report — PHASE 4 OOP SYLLABUS <-> IMPLEMENTATION MAPPING

Evidence: [A] verified in repo/executed; [D] general OOP background.
Note: the exact 25CSH-208 syllabus document was not supplied [E]; mapping uses the
repository's own concept map (which cites a Unit-2 notes file on Java I/O + threads)
plus standard OOP course topics [D]. All class/method/line references are [A].

## MASTER TABLE (OOP / Java Concept -> BasinWatch Component -> Actual Class/File -> Purpose -> Implementation)
1. Classes & Objects -> whole app -> 50 classes across 6 packages -> model the basin domain -> each class owns state+behaviour.
2. Encapsulation -> private fields + controlled access -> domain/*, io/* -> prevent invalid states -> private fields, package-private mutators, records with compact-ctor validation.
3. Abstraction -> BasinEvent, AutoCloseable, Runnable -> domain/BasinEvent.java -> hide event specifics -> interface contract tick/zoneId/category/describe.
4. Inheritance -> Thread/JFrame/JPanel/renderers/models -> engine/SensorFeed.java, app/MainFrame.java, app/BasinMapPanel.java, app/DatabaseHistoryPanel.java -> reuse framework contracts -> 7 extends sites.
5. Polymorphism -> event dispatch, switch over enums -> domain/BasinModel.java (process), app/MainFrame.java -> vary behaviour by type -> instanceof dispatch; enum switch; overridden methods.
6. Method Overriding -> 26 @Override -> engine/SensorFeed.run, app/BasinMapPanel.paintComponent, etc. -> adapt framework hooks -> run(), paintComponent(), toString(), getTableCellRendererComponent.
7. Method Overloading -> constructors -> domain/ResponseMission.java, domain/ResourceAllocator.java -> alternate construction -> 2 ctors each.
8. Constructors -> validated initialisation -> records + enums + BasinModel chained ctor -> enforce invariants at creation -> compact record ctors throw on invalid input.
9. Access Modifiers -> public/private/package-private/protected -> all packages -> least privilege -> 1 protected (paintComponent), private nested interfaces.
10. Composition -> BasinModel owns zones/missions/allocator/activity; BasinEngine owns services -> domain/BasinModel.java, engine/BasinEngine.java -> lifecycle coupling -> final fields, aggregate root.
11. Association -> engine<->db, UI<->engine -> engine/BasinEngine.java, db/DatabaseService.java -> collaborate without ownership -> listener callbacks, injected references.
12. Aggregation -> MissionType requirements; SimulationSettings shared -> domain/MissionType.java, engine/SimulationSettings.java -> shared vocabulary -> Map<ResourceType,Integer>, shared settings object.
13. Interfaces -> BasinEvent + functional interfaces -> domain/BasinEvent.java, engine/BasinEngine.java, db/DatabaseService.java -> decouple contracts -> public BasinEvent; private IoAction/IoSupplier/SqlAction/SqlSupplier.
14. Abstract Classes -> NOT USED (0) -> - -> deliberate exclusion -> inheritance used only for real framework contracts.
15. Enums -> RiskLevel, MissionType, MissionStatus, ResourceType, DatabaseHistoryType -> domain/*, db/DatabaseHistoryType.java -> bounded vocabularies -> enum ctors with labels/ranks/requirements.
16. Static Members/Constants -> 33 static final + static factories -> domain/ResourceAllocator.java, domain/BasinZone.java -> shared constants/utilities -> MAGIC, WORKER_COUNT, standard(), assessRisk().
17. Immutable Objects -> 15 records -> domain/*, engine/ThreadDiagnostic.java, db/DatabaseHistoryEntry.java -> safe sharing across threads -> records + List.copyOf/Map.copyOf.
18. Event-Driven Design -> BasinEvent pipeline + listeners -> engine/BasinEngine.java -> decouple producer/consumer/UI -> immutable events; CopyOnWriteArrayList listeners; EDT hand-off.
19. Exception Handling -> validation + checked I/O + SQL + interrupts -> domain/*, io/*, db/*, engine/* -> distinct visible outcomes -> IllegalArgumentException/IllegalStateException, IOException, SQLException, interrupt preservation.
20. Collections -> List/Map/Deque/EnumMap/queues -> domain/*, engine/*, db/* -> store/order/dedupe -> LinkedHashMap, ArrayDeque, EnumMap, ArrayBlockingQueue, CopyOnWriteArrayList.
21. Multithreading -> EDT + feed + intake + workers + archive + control + db -> engine/*, db/*, app/* -> responsive concurrent simulation -> 7 named threads + 2 executors.
22. Thread Lifecycle -> start/run/interrupt/join/getState/sleep -> engine/BasinEngine.java, engine/SensorFeed.java -> controlled lifecycle -> explicit stop, bounded join, truthful state reporting.
23. Runnable -> tasks vs execution -> engine/SensorIntake.java, engine/BasinEngine.java (ResponseWorker) -> separate task from thread -> Runnable tasks scheduled on threads.
24. Synchronization -> monitors -> engine/EventBuffer.java, domain/ResourceAllocator.java, domain/BasinModel.java -> protect shared state -> 28 synchronized; short critical sections.
25. Monitors -> intrinsic lock + wait/notifyAll -> engine/EventBuffer.java -> condition signalling -> while-loop condition checks under the same monitor.
26. Inter-thread Communication -> wait()/notifyAll() -> engine/EventBuffer.java -> sleep instead of spin -> producers/consumers signal after state change.
27. Producer-Consumer -> feed->intake->buffer->workers -> engine/EventBuffer.java -> decouple rates + back-pressure -> bounded 96-slot buffer.
28. Serialization -> SessionSnapshot -> io/SessionSnapshot.java, io/SnapshotStore.java -> persist session -> Serializable + serialVersionUID + ObjectOutputStream.
29. Deserialization -> load + validate -> io/SnapshotStore.java -> restore session safely -> ObjectInputFilter allowlist, version + invariant checks.
30. File Handling -> Paths/Files/File metadata -> io/AppPaths.java, io/SaveCatalog.java -> manage local data -> Files.createDirectories, listFiles, lastModified.
31. JDBC/Database -> repositories + service -> db/* -> offline history -> Connection/PreparedStatement/ResultSet/SQLException/transactions.

## PER-CONCEPT RECORDS (selected strong concepts)

### Encapsulation
Definition: bundling state with the methods that guard it, hiding internals.
Where: domain aggregates and DTOs. Class/File: domain/BasinZone.java (private fields,
package-private methods), domain/ResourceAllocator.java, io/SessionSnapshot.java.
Why: invalid basin/resource states must be unrepresentable. How: private fields;
mutators package-private; validation in compact record constructors. Interaction:
BasinModel owns BasinZone; UI reads only immutable snapshots. Excerpt: BasinZone fields
private; SensorReading compact ctor validates ranges. Benefit: no external code can set
water level or stock directly. Syllabus link: encapsulation/access modifiers.

### Abstraction
Definition: expose essential behaviour, hide implementation. Where: event contract.
Class/File: domain/BasinEvent.java (interface: tick/zoneId/category/describe);
concrete SensorReading, SimulationPulse, DispatchRequest. Why: workers process any event
uniformly. How: interface + polymorphic dispatch in BasinModel.process. Interaction:
EventBuffer stores BasinEvent; engine logs event.category()/describe(). Benefit: new
event types need no buffer/worker change. Syllabus link: abstraction/interfaces.

### Inheritance
Definition: derive a class from a superclass to reuse/extend behaviour. Where: threads,
Swing components, renderers/models. Class/File: engine/SensorFeed extends Thread;
engine/ArchiveWorker extends Thread; app/MainFrame extends JFrame; app/BasinMapPanel and
app/DatabaseHistoryPanel extend JPanel; MissionRenderer extends DefaultListCellRenderer;
HistoryTableModel extends AbstractTableModel. Why: adopt real framework lifecycles/hooks.
How: override run()/paintComponent()/getListCellRendererComponent()/table model methods.
Benefit: minimal custom code, correct integration. Syllabus link: inheritance/overriding.
Note: narrow, purposeful inheritance only.

### Polymorphism
Definition: one interface, many behaviours. Where: event processing and rendering.
Class/File: domain/BasinModel.java process() instanceof dispatch; MissionType switch in
applyPulse; RiskLevel switch for colour in app/MainFrame.java/BasinMapPanel.java;
DatabaseHistoryType switch in db/DatabaseService.java. Why: different events/risks/
missions require different handling. How: runtime type dispatch + overridden methods.
Benefit: uniform pipeline, type-specific behaviour. Syllabus link: polymorphism/overriding.

### Composition
Definition: strong whole-part ownership. Where: aggregate roots. Class/File:
domain/BasinModel.java owns LinkedHashMap<String,BasinZone>, missions, ResourceAllocator,
ArrayDeque<ActivityEntry>; engine/BasinEngine.java owns EventBuffer, SimulationSettings,
SnapshotStore, journal, databaseService, workers. Why: coupled state changes together.
How: final fields created in constructor; aggregate methods enforce invariants. Benefit:
single point of coordination; snapshots reflect one consistent state. Syllabus link:
composition/aggregation.

### Enums
Definition: fixed set of named constants. Where: domain vocabulary. Class/File:
RiskLevel (label+rank), MissionType (label, durationTicks, waterEffectMeters,
requirements), MissionStatus, ResourceType, DatabaseHistoryType. Why: prevent invalid
states; carry data. How: enum constructors with fields; switch dispatch; EnumMap storage.
Benefit: compile-time safety, readable code. Syllabus link: enums.

### Immutable Objects
Definition: objects whose state cannot change after construction. Where: snapshots/events.
Class/File: 15 records (SensorReading, SimulationPulse, DispatchRequest, ZoneSnapshot,
MissionSnapshot, BasinSnapshot, ActivityEntry, DatabaseHistoryEntry, ThreadDiagnostic,
EngineDiagnostics, ArchitectureCard, AppPaths, SavedZone/Mission/Activity). Why: safe
sharing across threads without locking. How: record components final; defensive
List.copyOf/Map.copyOf in compact constructors. Benefit: the EDT reads a stable snapshot
while workers mutate the model. Syllabus link: immutability/final.

### Exception Handling
Definition: detect and respond to abnormal conditions. Where: every boundary. Class/File:
domain/* (IllegalArgumentException/IllegalStateException in validation); io/SnapshotStore,
io/SensorArchive (IOException); db/* (SQLException); engine/SensorIntake (malformed line
catch), engine/BasinEngine (worker catch, interrupt preservation). Why: distinguish
malformed telemetry, corrupt saves, resource shortage, DB outage. How: validate at
boundary; try-with-resources; report with context; never convert failure to success.
Benefit: robust, diagnosable operation. Syllabus link: exception handling.

### Collections
Definition: framework data structures. Where: storage/ordering/queues. Class/File:
LinkedHashMap (ordered zones/missions), ArrayDeque (bounded activity + event queue),
EnumMap (resource stock), ArrayList, List.copyOf/Map.copyOf, ArrayBlockingQueue
(ArchiveWorker, DB queue), CopyOnWriteArrayList (listeners). Why: order, dedupe,
thread-safe queues. Benefit: correct ordering and safe concurrent access. Syllabus link:
collections framework.

### Multithreading & Synchronization
Definition: concurrent execution within a process with guarded shared state. Where:
engine/db/app. Class/File: SensorFeed, SensorIntake, EventBuffer, ResponseWorker,
ArchiveWorker, DatabaseService, EDT. Why: keep the UI responsive while observations and
operations proceed. How: one producer, one intake, three workers, bounded buffer with
wait/notifyAll, one short resource monitor, immutable snapshots to EDT. Benefit:
concurrency without corrupting shared state. Syllabus link: threads/synchronization.

### Producer-Consumer
Definition: decouple producers and consumers via a bounded buffer. Where: event pipeline.
Class/File: engine/EventBuffer.java (capacity 96; put waits when full; take waits when
empty; close wakes waiters). Why: independent rates + back-pressure. How: while-loop
condition checks under one monitor; notifyAll() after state changes. Benefit: no busy
spinning, bounded memory, graceful drain on close. Syllabus link: inter-thread comms.

### Serialization / Deserialization
Definition: convert object graph to/from bytes. Where: session save/restore. Class/File:
io/SessionSnapshot.java (Serializable, serialVersionUID, CURRENT_VERSION, transient hint),
io/SnapshotStore.java (ObjectOutputStream -> temp -> ATOMIC_MOVE; ObjectInputFilter
allowlist). Why: reopen a session without replaying history. How: versioned DTO; filter
rejects non-app classes; domain invariants re-checked on restore. Benefit: safe, atomic,
version-aware persistence. Syllabus link: serialization/deserialization/transient.

### JDBC / Database
Definition: standard Java API for relational databases. Where: optional history. Class/
File: db/DatabaseManager (Connection), db/DatabaseInitializer (DDL), repositories
(PreparedStatement/ResultSet), MissionRepository (transactions). Why: durable relational
history. How: embedded SQLite, fresh connection per op, parameterized SQL, try-with-
resources, commit/rollback. Benefit: queryable history isolated from the simulation.
Syllabus link: JDBC/database programming.

## Mapping summary counts [A]
extends sites 7; implements sites 13 (public BasinEvent + 4 Serializable/AutoCloseable +
Runnable + private functional interfaces); @Override 26; synchronized 28; volatile 18;
records 14; enums 5; static final 33; abstract classes 0.
