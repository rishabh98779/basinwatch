%%% CHAPTER 4 %%%

# CHAPTER 4: OBJECT ORIENTED DESIGN

This chapter is the analytical heart of the report. It does not merely list the object-oriented features that happen to appear in the code; it explains, for each concept that the project genuinely uses, *where* it appears, *why* the domain needs it, *how* it works, and *how* it connects to the syllabus. Where a concept is deliberately not used, that too is stated, because a disciplined design excludes features it does not need.

## 4.1 OOP Principles Used

The application is built from fifty classes distributed across six packages. Every class has a single, statable responsibility, and the object-oriented mechanisms are chosen to serve the domain rather than to satisfy a checklist. The concepts used are encapsulation, abstraction, inheritance (narrowly), polymorphism, composition, association, aggregation, constructors, access modifiers, interfaces, enums, static members, immutability, event-driven design, exception handling, collections, threads and monitors, the producer-consumer pattern, serialization, file handling, and JDBC. Abstract classes are not used. Figure 4.1 maps each concept to the component that realises it, and Table 4.1 is the master mapping.

[[FIG:fig4_1_oop_mapping.png|Figure 4.1: Mapping of object-oriented concepts to BasinWatch components.]]

| OOP / Java concept | BasinWatch component | Actual class / file | Purpose | Implementation explanation |
|---|---|---|---|---|
| Classes and objects | Whole application | 50 classes, 6 packages | Model the basin domain | Each class owns its state and behaviour |
| Encapsulation | Guarded domain state | `domain/BasinZone`, `domain/ResourceAllocator`, `io/SessionSnapshot` | Prevent invalid states | Private fields; package-private mutators; validating constructors |
| Abstraction | Event contract | `domain/BasinEvent` | Uniform event handling | Interface with `tick`, `zoneId`, `category`, `describe` |
| Inheritance | Threads and Swing components | `engine/SensorFeed`, `engine/ArchiveWorker`, `app/MainFrame`, `app/BasinMapPanel` | Adopt framework lifecycles | Seven `extends` sites |
| Polymorphism | Event, risk, and mission dispatch | `domain/BasinModel`, `app/MainFrame`, `db/DatabaseService` | Type-specific behaviour | `instanceof` dispatch; enum `switch`; overridden methods |
| Method overriding | 26 `@Override` methods | `SensorFeed.run`, `BasinMapPanel.paintComponent`, … | Adapt framework hooks | Override `run`, `paintComponent`, `toString` |
| Method overloading | Alternate constructors | `domain/ResponseMission`, `domain/ResourceAllocator` | Alternate construction | Two constructors each |
| Constructors | Validated creation | Records, enums, `BasinModel` | Enforce invariants at creation | Compact record constructors throw on invalid input |
| Access modifiers | Least privilege | All packages | Controlled exposure | One `protected` (`paintComponent`); private nested interfaces |
| Composition | Aggregate roots | `domain/BasinModel`, `engine/BasinEngine` | Lifecycle coupling | `final` fields; aggregate ownership |
| Association | Engine↔database, UI↔engine | `engine/BasinEngine`, `db/DatabaseService` | Collaborate without ownership | Listener callbacks and injected references |
| Aggregation | Shared vocabulary | `domain/MissionType.requirements`, `engine/SimulationSettings` | Shared data | `Map<ResourceType,Integer>`; shared settings object |
| Interfaces | Contracts | `domain/BasinEvent` and four functional interfaces | Decouple producers and consumers | Public domain interface; private functional interfaces |
| Abstract classes | Not used | — | Deliberate exclusion | Inheritance only for real framework contracts |
| Enums | Bounded vocabularies | `RiskLevel`, `MissionType`, `MissionStatus`, `ResourceType`, `DatabaseHistoryType` | Safe, readable states | Enum constructors carry labels, ranks, requirements |
| Static members | Constants and factories | `domain/ResourceAllocator`, `domain/BasinZone` | Shared values and utilities | 33 `static final` constants; `standard()`, `assessRisk()` |
| Immutable objects | 14 records | `domain/*`, `engine/ThreadDiagnostic`, `db/DatabaseHistoryEntry` | Safe cross-thread sharing | Records plus `List.copyOf`/`Map.copyOf` |
| Event-driven design | Pipeline and listeners | `engine/BasinEngine` | Decouple producer, consumer, UI | Immutable events; listener lists; EDT hand-off |
| Exception handling | Every boundary | `domain/*`, `io/*`, `db/*`, `engine/*` | Distinct visible outcomes | Validation, checked I/O, `SQLException`, interrupt preservation |
| Collections | Storage and queues | `domain/*`, `engine/*`, `db/*` | Order, dedupe, thread-safe queues | `LinkedHashMap`, `ArrayDeque`, `EnumMap`, `ArrayBlockingQueue`, `CopyOnWriteArrayList` |
| Multithreading | Seven threads and two executors | `engine/*`, `db/*`, `app/*` | Responsive concurrency | EDT, feed, intake, three workers, archive, control, database |
| Thread lifecycle | Controlled start and stop | `engine/BasinEngine`, `engine/SensorFeed` | Safe lifecycle | `start`, `interrupt`, `join`, `getState`, `sleep` |
| `Runnable` | Task versus execution | `engine/SensorIntake`, `ResponseWorker` | Separate task from thread | Runnable tasks scheduled on threads |
| Synchronization | Monitors | `engine/EventBuffer`, `domain/ResourceAllocator`, `domain/BasinModel` | Protect shared state | 28 `synchronized` members; short critical sections |
| Monitors | Intrinsic lock and conditions | `engine/EventBuffer` | Condition signalling | Condition checked in a `while` loop under one monitor |
| Inter-thread communication | `wait()` and `notifyAll()` | `engine/EventBuffer` | Sleep rather than spin | Signal after every state change |
| Producer-consumer | Bounded buffer | `engine/EventBuffer` | Decouple rates and apply back-pressure | 96-slot bounded buffer |
| Serialization | Session save | `io/SessionSnapshot`, `io/SnapshotStore` | Persist a session | `Serializable`, `serialVersionUID`, `ObjectOutputStream` |
| Deserialization | Safe restore | `io/SnapshotStore` | Recover a session | `ObjectInputFilter` allowlist and version/invariant checks |
| File handling | Local data management | `io/AppPaths`, `io/SaveCatalog` | Manage files | `Files.createDirectories`, `listFiles`, `lastModified` |
| JDBC and databases | Offline history | `db/*` | Durable, queryable history | `Connection`, `PreparedStatement`, `ResultSet`, `SQLException`, transactions |

*Table 4.1: Master mapping of object-oriented and Java concepts to the BasinWatch implementation.*

## 4.2 Encapsulation

**Definition.** Encapsulation is the bundling of state with the methods that guard it, so that an object's internals cannot be changed arbitrarily from outside.

**Where it appears.** Encapsulation is most visible in the domain aggregate. `BasinZone` keeps its water level, rainfall, exposed population, levee state, and risk private, and exposes only the operations that make sense — apply a reading, pump water out, reinforce the levee, evacuate — plus a read-only snapshot. `ResourceAllocator` keeps its available and capacity maps private and exposes only `tryReserve`, `release`, and `snapshot`. The persistence DTO `SessionSnapshot` keeps its arrays private and validates them before exposing a domain snapshot.

**Why it is needed.** A basin model in which any code could set a zone's water level to an impossible value, or decrement a resource count without checking availability, would be a model in which invariants are suggestions rather than guarantees. Encapsulation makes those invariants enforceable.

**How it works.** Fields are declared `private`. Mutating methods are package-private where only the domain needs them, so no code outside the package can alter a zone's water level directly. Where an object is constructed, the constructor validates its inputs; the immutable records validate in their compact constructors. Accessors return either primitives or immutable copies, never the mutable internal collection.

```java
// domain/BasinZone.java (fields, condensed)
private final String id;
private final String name;
private double waterLevelMeters;
private double lastRainMillimeters;
private int exposedResidents;
private boolean leveeReinforced;
private long lastReadingTick = -1;
private RiskLevel risk;
```

*Listing 4.1: Encapsulated zone state; only domain methods may change it.*

**Interaction with other classes.** `BasinModel` is the only class that calls `BasinZone`'s package-private mutators; the user interface never sees a `BasinZone` at all — it receives `ZoneSnapshot` records. This separation is what allows the UI to be updated from any thread safely.

**Practical benefit.** No external code can create an impossible zone or over-allocate a resource; the compiler and the constructor do the enforcing.

**Syllabus link.** Encapsulation, access modifiers, and the principle of information hiding.

## 4.3 Abstraction

**Definition.** Abstraction exposes the essential behaviour of a concept while hiding the details of its implementation.

**Where it appears.** The central abstraction is the `BasinEvent` interface. It declares four operations — the tick at which the event occurred, the zone it concerns, its category, and a human-readable description — and nothing else. Three concrete records implement it: `SensorReading`, `SimulationPulse`, and `DispatchRequest`. The persistence and engine layers also use small private functional interfaces (`IoAction`, `IoSupplier`, `SqlAction`, `SqlSupplier`) to abstract "an action that may fail".

```java
// domain/BasinEvent.java
public interface BasinEvent {
    long tick();
    String zoneId();
    String category();
    String describe();
}
```

*Listing 4.2: The event abstraction that the entire pipeline depends upon.*

**Why it is needed.** The buffer, the workers, the journal, and the archive all handle events, but they must not be rewritten every time a new kind of event is added. The abstraction lets the pipeline be written once against `BasinEvent` and remain closed to modification when new event types appear.

**How it works.** The buffer stores `BasinEvent` references. When a worker processes an event, `BasinModel` dispatches on the concrete type to apply the correct transition. The journal records `event.category()` and `event.describe()` without knowing the event's class.

**Interaction with other classes.** `EventBuffer` depends only on `BasinEvent`. `BasinEngine.process` records the category and description generically. `BasinModel.process` is the single place that knows the concrete types.

**Practical benefit.** The producer, the buffer, and the persistence side are decoupled from the catalogue of event types, which is exactly the kind of stability that object-oriented design is meant to provide.

**Syllabus link.** Abstraction, interfaces, and programming to a contract.

## 4.4 Inheritance

**Definition.** Inheritance derives a class from a superclass so that it reuses and extends the superclass's behaviour.

**Where it appears.** Inheritance is used narrowly and only where the application genuinely adopts a framework contract. `SensorFeed` and `ArchiveWorker` extend `Thread`, because each owns a long-lived lifecycle and a blocking endpoint. `MainFrame` extends `JFrame`, `BasinMapPanel` and `DatabaseHistoryPanel` extend `JPanel`, `MissionRenderer` extends `DefaultListCellRenderer`, and `HistoryTableModel` extends `AbstractTableModel`, because Swing's components and models are designed to be extended.

**Why it is needed.** A feed that owns its own timed lifecycle and a component that must paint itself are both naturally expressed as subclasses. The alternative — composition with an internal `Thread` — is possible but would add indirection without adding clarity for these specific cases.

**How it works.** The subclass overrides the superclass hook. `SensorFeed` overrides `run()`; `BasinMapPanel` overrides `paintComponent(Graphics)`; `MissionRenderer` overrides `getListCellRendererComponent`; `HistoryTableModel` implements the abstract table-model methods.

**Interaction with other classes.** The engine starts a `SensorFeed` as a `Thread`; the frame is displayed as a `JFrame`; the map panel is added to the frame as a `JPanel`.

**Practical benefit.** The application integrates with real platform facilities with very little code, and the overrides are exactly the hooks the frameworks intend developers to use.

**Syllabus link.** Inheritance, method overriding, and the `is-a` relationship. Note that the project deliberately avoids inheritance for the domain itself, where composition is more appropriate.

## 4.5 Polymorphism

**Definition.** Polymorphism allows one interface to stand for several concrete behaviours.

**Where it appears.** Polymorphism appears at three levels. First, event processing is polymorphic: `BasinModel.process` receives a `BasinEvent` and dispatches to the correct handler based on the concrete type. Second, mission effects are polymorphic over an enum: when a mission completes, a `switch` on the mission type decides whether to pump, reinforce, or evacuate. Third, presentation is polymorphic: risk categories map to colours through a `switch`, and history categories map to repository queries through a `switch`.

```java
// domain/BasinModel.java (process, line 44)
if (event instanceof SensorReading reading) {
    applyReading(reading, messages);
} else if (event instanceof SimulationPulse pulse) {
    applyPulse(pulse, messages);
} else if (event instanceof DispatchRequest request) {
    applyDispatch(request, messages);
} else {
    throw new IllegalArgumentException("Unsupported basin event: " + event.getClass().getName());
}
```

*Listing 4.3: Polymorphic event dispatch, with an explicit rejection of unknown event types.*

**Why it is needed.** Different events have genuinely different effects on the basin; different missions have genuinely different effects on a zone. Polymorphism keeps those differences in one place while allowing the surrounding pipeline to be uniform.

**How it works.** The runtime type of the event selects the handler. The `switch` on `MissionType` selects the effect. Because the enums are exhaustive, the compiler can help ensure every case is handled.

**Interaction with other classes.** The buffer, workers, and journal treat all events uniformly; only the model distinguishes them.

**Practical benefit.** New event types can be added with a single new handler and a single new branch, while the rest of the pipeline is untouched.

**Syllabus link.** Polymorphism, dynamic dispatch, and method overriding.

## 4.6 Composition

**Definition.** Composition is a strong whole-part relationship in which the whole owns its parts and controls their lifetime.

**Where it appears.** `BasinModel` is a composition root: it owns a `LinkedHashMap` of six zones, a `LinkedHashMap` of missions, an `ArrayDeque` of activity entries, and a `ResourceAllocator`. `BasinEngine` composes the `EventBuffer`, `SimulationSettings`, `SnapshotStore`, `OperationalJournal`, `DatabaseService`, and the worker threads. `BasinSnapshot` composes its lists of zone and mission snapshots.

**Why it is needed.** The parts of the model change together and must remain mutually consistent; making the aggregate own them keeps that consistency in one place. The engine's services likewise share a lifecycle and are started and stopped together.

**How it works.** The whole creates its parts in its constructor and holds them in `final` fields. The parts are not shared with unrelated code.

**Interaction with other classes.** The engine calls `model.process(...)` and `model.snapshot()`; it never reaches into the model's collections. The UI receives `BasinSnapshot`, which is a composed value.

**Practical benefit.** The model can guarantee that its zones and inventory always agree, because it is the only owner of both.

**Syllabus link.** Composition, aggregation, and the aggregate-root idea.

## 4.7 Association and Aggregation

**Definition.** Association is a general "uses" relationship; aggregation is a weaker whole-part relationship in which the part can outlive or be shared beyond the whole.

**Where it appears.** Association is visible between the engine and the database service, and between the UI and the engine: the UI holds a reference to the engine and registers listeners, but does not own the engine's threads. Aggregation appears in `MissionType`, whose `requirements()` returns a shared map from resource types to quantities, and in `SimulationSettings`, a single settings object shared by the feed and the engine.

**Why it is needed.** Not every relationship is ownership. The UI must observe the engine without owning it; the mission types must share a common resource vocabulary without each owning a private copy.

**How it works.** The UI registers a listener with the engine; the engine holds the settings and passes the same instance to the feed. The mission requirements map is created once and copied defensively on access.

**Practical benefit.** Collaboration without ownership keeps the design flexible and avoids accidental lifetime coupling.

**Syllabus link.** Association, aggregation, and the distinction between "has-a" and "owns-a".

## 4.8 Constructors

**Definition.** A constructor initialises an object and establishes its invariants.

**Where it appears.** Constructors are the primary guard rails of the domain. `SensorReading` and the other event records validate their inputs in compact constructors. `ResourceAllocator` validates that available stock lies within capacity. `BasinModel` has a public constructor that seeds the six zones and a private constructor used when restoring a saved model. `ResponseMission` has two constructors.

```java
// domain/SensorReading.java (compact constructor)
public SensorReading {
    if (tick < 0 || !validIdentifier(stationId) || !validIdentifier(zoneId)
            || !Double.isFinite(rainfallMillimeters) || rainfallMillimeters < 0
            || rainfallMillimeters > 500
            || !Double.isFinite(observedRiseCentimeters) || observedRiseCentimeters < 0
            || observedRiseCentimeters > 200) {
        throw new IllegalArgumentException("Invalid sensor reading.");
    }
}
```

*Listing 4.4: A compact record constructor rejects impossible readings before the object exists.*

**Why it is needed.** If an object can be constructed in an invalid state, every later method must defend against that state. Validating at construction removes an entire class of defensive checks.

**How it works.** The compact constructor runs before the record's fields are assigned, so an invalid record can never come into existence. The `BasinModel` constructors ensure the zone set is complete.

**Practical benefit.** The rest of the code can assume that any existing `SensorReading` or `BasinZone` is valid.

**Syllabus link.** Constructors, constructor overloading, and object initialisation.

## 4.9 Access Modifiers

**Definition.** Access modifiers control the visibility of classes, fields, and methods.

**Where it appears.** Throughout the codebase. Public API is limited to what callers need: the engine's lifecycle methods, the domain's snapshots and events, and the persistence entry points. Internal helpers are private. Mutators that only the domain needs are package-private. Exactly one member is `protected` — `BasinMapPanel.paintComponent` — because Swing requires subclasses to override it.

**Why it is needed.** A wide public surface invites misuse. Restricting visibility makes the intended use obvious and prevents accidental coupling.

**How it works.** `private` for implementation details, package-private for domain-internal collaboration, `public` for genuine API, and `protected` only where a framework requires an overridable hook.

**Practical benefit.** The compiler enforces the design's intent about who may change what.

**Syllabus link.** Access modifiers and encapsulation.

## 4.10 Interfaces and the Deliberate Absence of Abstract Classes

**Definition.** An interface declares a contract without implementation; an abstract class provides a partial implementation that subclasses complete.

**Where it appears.** The domain's `BasinEvent` is the project's central interface. Four small private functional interfaces abstract fallible actions in the engine and database layers. The application contains **no abstract classes**. This is a deliberate decision: the only inheritance in the project is the narrow, purposeful adoption of framework contracts, and none of those required a shared partial implementation. Introducing an abstract class would have added a layer without serving the domain.

**Why it is needed.** The interfaces decouple the pipeline from concrete types. The absence of abstract classes keeps the inheritance graph shallow and easy to reason about.

**Practical benefit.** Readers can hold the entire type hierarchy in their heads; there is no speculative abstraction to navigate.

**Syllabus link.** Interfaces, abstract classes, and the judgement to use the right tool.

## 4.11 Enums

**Definition.** An enum defines a fixed set of named constants, which may carry fields and behaviour.

**Where it appears.** Five enums give the domain a closed vocabulary: `RiskLevel` (with a label and a numeric rank), `MissionType` (with a label, a duration in ticks, a water effect, and a resource requirement map), `MissionStatus`, `ResourceType`, and `DatabaseHistoryType`.

```java
// domain/MissionType.java
PUMP_DEPLOYMENT("Deploy portable pump", 8, 0.62,
        Map.of(ResourceType.PUMP, 1, ResourceType.FIELD_CREW, 1)),
LEVEE_REINFORCEMENT("Reinforce levee", 10, 0.0,
        Map.of(ResourceType.LEVEE_CREW, 1, ResourceType.SUPPLY_TRUCK, 1)),
EVACUATION("Evacuate exposed residents", 6, 0.0,
        Map.of(ResourceType.EVAC_VEHICLE, 1, ResourceType.FIELD_CREW, 1));
```

*Listing 4.5: Mission types carry their own duration, effect, and resource requirements.*

**Why it is needed.** A risk level or mission type expressed as a string would permit typographical errors and invalid values. An enum makes the set closed and the values discoverable.

**How it works.** Enum constructors attach data to each constant. `EnumMap` uses the enum ordinals for compact, fast storage. `switch` over enums is exhaustive and readable.

**Practical benefit.** Invalid categories become impossible, and the code reads like the domain.

**Syllabus link.** Enumerations and their use in modelling fixed domains.

## 4.12 Immutable Objects

**Definition.** An immutable object cannot change after construction, so it can be shared freely between threads without locking.

**Where it appears.** The project defines fourteen record types, including the events, the snapshots (`ZoneSnapshot`, `MissionSnapshot`, `BasinSnapshot`), `ActivityEntry`, `DatabaseHistoryEntry`, `ThreadDiagnostic`, `EngineDiagnostics`, and `AppPaths`. Each record's components are final, and the snapshot records copy their collections defensively.

```java
// domain/BasinSnapshot.java (compact constructor)
public BasinSnapshot {
    zones = List.copyOf(zones);
    availableResources = Map.copyOf(availableResources);
    missions = List.copyOf(missions);
    activity = List.copyOf(activity);
}
```

*Listing 4.6: A snapshot copies its collections so that no later mutation can alter it.*

**Why it is needed.** This is the mechanism that makes the concurrency design safe. Background workers mutate the live model under a lock; the interface reads an immutable snapshot without a lock. Because the snapshot cannot change, there is no possibility of the interface observing a half-applied update.

**How it works.** The model builds a snapshot from copies of its state. The snapshot's collections are unmodifiable. The interface may hold the snapshot for as long as it likes.

**Practical benefit.** Thread-safe hand-off with no locks on the reading side — one of the most valuable outcomes of the entire design.

**Syllabus link.** Immutability, `final`, and defensive copying.

## 4.13 Event-Based Design

**Definition.** Event-based design structures a system around the production, transport, and consumption of events.

**Where it appears.** The whole pipeline is event-based. The sensor feed produces events; the intake task validates them; the buffer transports them; the workers consume them. The engine also exposes three listener lists (`snapshotListeners`, `statusListeners`, `databaseStatusListeners`) so that the interface can subscribe to state changes without polling.

**Why it is needed.** The domain is naturally event-shaped: things happen over time, and the system must react to each. Event-based design lets production and consumption proceed independently.

**How it works.** Events are immutable values carried by the buffer. Listeners are held in `CopyOnWriteArrayList` instances, which are safe to iterate while other threads modify them. The UI subscribes and receives updates on the EDT.

**Practical benefit.** Loose coupling between producer, consumer, and presentation; the UI never needs to ask "has anything changed?".

**Syllabus link.** Event-driven programming and the observer pattern.

## 4.14 Exception Handling

**Definition.** Exception handling is the language's mechanism for detecting and responding to abnormal conditions.

**Where it appears.** Every boundary in the system. Domain constructors throw `IllegalArgumentException`; invalid state transitions throw `IllegalStateException`; file operations throw `IOException`; database operations throw `SQLException`; the intake task catches malformed records and reports them without stopping.

**Why it is needed.** Malformed telemetry, corrupt saves, resource shortages, and database outages are different problems that must be distinguishable. Treating them all as "something went wrong" would make the system undiagnosable and would risk presenting failure as success.

**How it works.** Each boundary validates and throws a specific exception. Callers either handle the exception meaningfully or let it propagate with context. Try-with-resources guarantees that streams and connections are closed. Interrupted threads preserve their interrupt status so that the shutdown path behaves correctly.

**Practical benefit.** The operator sees an accurate account of what happened, and unrelated work continues when one part fails.

**Syllabus link.** Exception handling, checked versus unchecked exceptions, and resource management.

## 4.15 OOP Design Benefits

The benefits of this design are concrete and observable. Encapsulation means the domain cannot be driven into an invalid state from outside. Abstraction means the pipeline is stable against new event types. Narrow inheritance means the type graph is shallow and legible. Polymorphism localises the differences between events, missions, and risks. Composition gives the model a single owner for state that must remain consistent. Enums remove an entire class of stringly-typed errors. Immutability is what makes concurrent reads safe. Event-based design keeps producer, consumer, and interface decoupled. Disciplined exception handling keeps failures visible and local. Together these choices produce a program that is not merely written in an object-oriented language but is designed in an object-oriented way — which is the point of the exercise.
