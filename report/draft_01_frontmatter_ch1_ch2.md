
[[TITLEPAGE]]

[[CERTIFICATE]]

[[DECLARATION]]

%%% ACKNOWLEDGEMENT %%%
# ACKNOWLEDGEMENT

The team records its sincere gratitude to Chandigarh University for providing the academic environment, laboratory access, and library resources that made this project possible. We thank the faculty of the Department of Computer Science Engineering for the structured coverage of object-oriented programming that directly shaped the design of this application.

We are especially grateful to [SUPERVISOR NAME — TO BE PROVIDED], our project supervisor, for guidance on architectural separation, concurrency discipline, and the practice of validating every design claim against running code. The insistence on evidence over assumption influenced both the implementation and this report.

We acknowledge the Head of the Department, [HEAD OF DEPARTMENT — TO BE PROVIDED], and the departmental staff for administrative support and for maintaining the computing facilities used during development and testing. We also thank our classmates and peers who reviewed early demonstrations and offered candid feedback on the usability of the operations console.

Finally, we thank our families for their patience and encouragement during the weeks of design, coding, and documentation. Any errors that remain in the software or in this report are our own.

**Saumya Dwivedi — 25BCS12109**
**Rishabh Singh — 25BCS11466**
**Anshu Anand — 25BCS11475**
**Deepshikha Yadav — 25BCS10801**

%%% ABSTRACT %%%
# ABSTRACT

Floodplain operations present a genuine coordination problem: rainfall and water-level observations keep arriving while several threatened districts compete for a small, shared stock of pumps, crews, and evacuation vehicles. BasinWatch is an offline floodplain operations console that reproduces this coordination problem as a local desktop planning simulation. It is deliberately **not** a flood-forecasting service, a public warning system, or an emergency dispatch platform; it is an educational simulator whose purpose is to demonstrate, in a single runnable application, how object-oriented design and Java concurrency can keep a live operational picture coherent while independent work proceeds.

The application is written in Java 17 and built with Maven. The user interface uses standard Swing and is owned exclusively by the event-dispatch thread. Beneath the interface, a `BasinEngine` coordinates a small set of background services. A dedicated `SensorFeed` thread emits encoded rainfall and water-level observations through connected piped character streams; a `SensorIntake` task reads, parses, and validates each record and places accepted events into a bounded, monitor-protected event buffer. A small pool of response workers consumes events and applies them to a `BasinModel` that owns six schematic flood zones, the resource inventory, and active response missions. Immutable snapshots are published to the Swing event queue so that the map, inventory board, and activity timeline always reflect one consistent state.

The project deliberately exercises a broad portion of the object-oriented syllabus. Encapsulation keeps zone and inventory state valid; an abstract event contract and typed event records provide polymorphism at the processing boundary; enums give the domain a fixed vocabulary of risks, missions, resources, and statuses; composition binds zones, missions, and the resource allocator into an aggregate root; and immutable records make it safe to hand data across thread boundaries. Concurrency is treated as a first-class concern: `wait()` and `notifyAll()` coordinate a bounded producer-consumer buffer, a short synchronized critical section makes multi-resource reservation all-or-nothing, and shutdown interrupts and joins owned threads with a bounded timeout rather than abandoning file writes.

Persistence is equally deliberate. Operational events are appended to a UTF-8 text journal through a buffered writer; typed sensor measurements are stored in a versioned binary archive written with a data stream over a buffered byte stream; a versioned session snapshot is serialized to a temporary file and atomically moved into place, with an input filter that rejects unexpected classes; readable situation reports are generated as text; and an optional embedded SQLite database, accessed through raw JDBC with prepared statements and transactions, retains a queryable history without becoming a dependency for the simulation.

The implementation is supported by a dependency-free assertion suite that was executed during preparation of this report and reported seventy-six passing assertions. The suite stresses atomic concurrent resource reservation, bounded-buffer waiting and closing, mission progression and release, session save and restore with corrupt-input rejection, archive validation, JDBC history and transactions, and continued operation when the database is unavailable. The report documents the architecture, the object-oriented design, the concurrency model, the persistence and database layers, the user interface, and the testing approach, and it states clearly the limits of the simulation: the map is schematic, the parameters are illustrative rather than calibrated, and the application controls no real infrastructure.

**Keywords:** Object-Oriented Programming; Java 17; Java Swing; Multithreading; Producer-Consumer; wait/notifyAll; Synchronization; Resource Allocation; Serialization; Java I/O Streams; JDBC; SQLite; Immutable Snapshots; Offline Simulation; Maven.

%%% CHAPTER 1 %%%

# CHAPTER 1: INTRODUCTION

## 1.1 Background

River basins concentrate people, farmland, and infrastructure on low-lying ground that is periodically inundated. When rainfall intensifies, water levels rise unevenly across a basin: an upstream weir, a densely populated market quarter, and a downstream marsh may each cross a different danger threshold at a different moment. Operations teams respond by reading station observations, ranking the threatened districts, and committing a limited set of physical resources — portable pumps, levee crews, supply trucks, and evacuation vehicles — to the districts that need them most. The difficulty is not a single calculation; it is sustained coordination under change. New observations continue to arrive while earlier decisions are still being carried out, and several districts may be competing for the same scarce equipment at the same time.

Software that supports this kind of work therefore has two obligations that pull in different directions. It must keep updating its picture of the world as fresh data arrives, and it must keep that picture coherent enough that a decision made on it is trustworthy. A program that freezes while it processes an observation is useless to an operator; a program that lets two operations claim the same pump is worse than useless, because it produces confident but false information. Reconciling responsiveness with consistency is precisely the problem that threads and synchronization are designed to solve, which is why this project uses a floodplain operations scenario as the setting for a study of object-oriented programming and Java concurrency.

It is important to state the boundary of the project at the outset. BasinWatch is an offline, single-user, desktop planning simulation. It is an educational artefact built to demonstrate programming concepts; it is not a hydrological model, not a certified forecasting tool, and not a real dispatch system. Its rainfall values, water levels, equipment capacities, and risk thresholds are transparent scenario parameters chosen to make the simulation instructive, not calibrated constants derived from a real basin. This report returns to that boundary repeatedly, because an honest description of what a program is *not* is part of a serious engineering account.

## 1.2 Problem Statement

The problem that BasinWatch addresses can be stated in one paragraph. *A basin operations team must interpret a continuously arriving stream of rainfall and water-level observations, identify which districts are becoming dangerous, and coordinate a limited inventory of response resources across several districts that may need those resources simultaneously — all without the software either freezing under load or corrupting its own shared state.* Three distinct sub-problems follow from this statement.

The first is **data-arrival concurrency**. Observations are produced on a cadence that is independent of how quickly the operator reads the screen and independent of how quickly earlier observations have been processed. If the arrival of data is handled on the same thread that paints the interface, the interface stutters; if it is handled without a bounded queue, memory can grow without limit; if the queue is unbounded and consumers are slow, the backlog is invisible.

The second is **shared-state integrity**. Zones, resource stock, and mission progress are genuinely shared: several background workers may touch them, and the interface reads them. Two dispatches that run at the same moment must not both observe the same final pump as available. A partially applied change — a mission recorded but its equipment not yet deducted — must never be visible.

The third is **durability and recovery**. An operations picture that evaporates when the window closes is not useful for planning. The system must retain a readable audit of what happened, preserve typed measurements for later review, allow a session to be saved and reopened, and generate a report that a human can read after the simulation ends.

Each sub-problem maps naturally onto object-oriented concepts. Concurrency maps onto threads, monitors, and the producer-consumer pattern. Integrity maps onto encapsulation, composition, and synchronized critical sections. Durability maps onto streams, serialization, and JDBC. This is the sense in which the project is an object-oriented programming project rather than merely a program that happens to be written in Java: the syllabus concepts are the instruments used to solve the domain's problems, not decorations added afterwards.

## 1.3 Motivation

Three motivations shaped the choice of this project.

First, **a domain that makes concurrency unavoidable**. It is possible to build a Java application in which threads are decorative. BasinWatch is not such an application. The simulation is inherently concurrent: observations arrive on their own schedule while the operator dispatches work and while previously dispatched work progresses. Removing threads would not simplify the design; it would break the behaviour the design is meant to exhibit. The project therefore demonstrates `Thread`, `Runnable`, `wait()`, `notifyAll()`, synchronization, and interruption because the scenario genuinely needs them.

Second, **the value of a bounded, offline artefact**. An offline desktop application can be built and understood end to end with nothing more than a JDK and Maven. There is no server to install, no network dependency, and no external service whose behaviour must be guessed. This makes every claim in this report verifiable: the reader can compile the project, run its tests, and observe the interface. The optional SQLite history uses an embedded database precisely so that the "database" chapter is real without introducing an operational dependency.

Third, **the opportunity to connect the syllabus to something whole**. Object-oriented courses often teach concepts through small isolated exercises: a class hierarchy here, a thread example there. Building a single application that must simultaneously respect encapsulation, use polymorphism meaningfully, coordinate threads safely, persist data through several stream families, and talk to a relational database through JDBC forces the student to confront how these ideas interact. The result is a richer understanding than any single exercise can provide.

## 1.4 Project Overview

BasinWatch presents a schematic basin of six monitored zones and lets an operator watch conditions evolve, dispatch responses, and review the consequences. The application is organised into six packages: `app` for the Swing user interface, `domain` for the model and its values, `engine` for the simulation's lifecycle and threading, `io` for file persistence and reporting, `db` for the optional SQLite history, and `learning` for short in-application architecture notes.

At runtime the operator can start a live observation feed or advance the simulation one interval at a time; inject a deliberately marked storm cell into a selected zone; select any zone and read its water level, latest rainfall, exposed population, and risk category; dispatch one of three response missions; follow the progress of active missions; inspect background service health; browse a typed database history; save a session, close the application, and restore that session later; and export a readable situation report.

Behind the interface, the engine runs a small, deliberately chosen set of background services. One producer thread emits sensor observations. One intake task reads and validates them. A bounded event buffer decouples production from consumption. Three response workers apply events to the model and advance missions. An archive worker writes typed measurements to a binary file, and a single-threaded database service writes history through JDBC. The Swing event-dispatch thread never blocks on this work; it receives immutable snapshots and repaints.

[[FIG:fig1_1_context.png|Figure 1.1: BasinWatch system context and boundary, showing the operator, the offline application, and the local file and database stores.]]

## 1.5 Objectives

The project set the following objectives. Each is written so that its achievement can be checked against the running program rather than asserted in prose.

- **O1 — Concurrent observation pipeline.** Build a producer-consumer pipeline in which a sensor producer, a validating intake task, a bounded event buffer, and response workers operate concurrently without the user interface blocking. *Verified by:* the engine session test, which observes the feed, pipe, and workers processing real events.
- **O2 — Atomic resource allocation.** Ensure that a multi-resource dispatch is all-or-nothing, so two simultaneous dispatches can never reserve the same unit. *Verified by:* the concurrent reservation test, in which twenty-four contenders attempt to reserve the final pump and crew and exactly one succeeds.
- **O3 — Bounded, safe buffering.** Provide a bounded event buffer that applies back-pressure to producers and drains accepted work on shutdown. *Verified by:* the buffer test, which exercises waiting, back-pressure, and close wake-up.
- **O4 — Multi-format persistence.** Implement an operational text journal, a typed binary sensor archive, a versioned session snapshot, and readable reports, each using the stream family appropriate to its purpose. *Verified by:* the persistence and archive tests.
- **O5 — Safe session recovery.** Save a session and restore it so that zone state, inventory, active missions, and recent activity survive a restart, while rejecting corrupt or unexpected files. *Verified by:* the snapshot round-trip test and the engine save/restore test.
- **O6 — Optional relational history.** Retain a queryable history in an embedded database through raw JDBC with prepared statements and transactions, without making the database a dependency for the simulation. *Verified by:* the JDBC test and the database-unavailable test.
- **O7 — Demonstrate the object-oriented syllabus.** Show, through the actual implementation, the use of encapsulation, abstraction, inheritance, polymorphism, composition, enums, immutability, exception handling, collections, threads, synchronization, serialization, and JDBC.

## 1.6 Scope

**In scope.** A single-user, offline desktop simulation of a six-zone schematic basin; synthetic sensor observations; three response mission types; a shared, finite resource inventory; a Swing interface; local file persistence; an optional embedded SQLite history; and a dependency-free invariant test suite.

**Out of scope.** Any connection to real sensors, gauges, or telemetry; any hydrological or hydrodynamic modelling; any real dispatch, warning, or infrastructure control; any networked or multi-user operation; any cloud service; and any claim that simulated values correspond to a real geographic basin. The schematic map is illustrative and is labelled as such inside the application.

## 1.7 Target Users

The intended users are students and instructors studying object-oriented programming and Java concurrency, and, secondarily, planners who wish to explore the *shape* of a resource-coordination problem without any operational consequence. The application assumes a single local operator. It presents itself explicitly as an offline planning simulation, and its interface carries that label so that no user mistakes it for an operational tool.

## 1.8 Problem-to-Solution Mapping

Table 1.1 relates each sub-problem from Section 1.2 to the concrete BasinWatch mechanism that addresses it.

| # | Sub-problem | BasinWatch mechanism | Where it is implemented |
|---|---|---|---|
| 1 | Observations arrive independently of the interface | Dedicated producer thread + piped character streams | `engine/SensorFeed`, `engine/SensorIntake` |
| 2 | Slow consumption could grow memory without limit | Bounded, monitor-protected event buffer (capacity 96) | `engine/EventBuffer` |
| 3 | Interface must not freeze under load | Immutable snapshots handed to the EDT | `engine/BasinEngine`, `app/MainFrame` |
| 4 | Two dispatches must not claim the same unit | Atomic, synchronized all-or-nothing reservation | `domain/ResourceAllocator` |
| 5 | Partially applied changes must not be visible | Synchronized model transitions + immutable snapshots | `domain/BasinModel`, `domain/BasinSnapshot` |
| 6 | Decisions must be auditable | UTF-8 operational journal | `io/OperationalJournal` |
| 7 | Typed measurements must survive the run | Versioned binary archive | `io/SensorArchive`, `engine/ArchiveWorker` |
| 8 | A session must be reopened later | Versioned, filtered object serialization | `io/SnapshotStore`, `io/SessionSnapshot` |
| 9 | A human must be able to read outcomes | Text situation report | `io/ReportWriter` |
| 10 | History must be queryable | Embedded SQLite via JDBC | `db/*` |

*Table 1.1: Problem-to-solution mapping.*

## 1.9 Limitations

The simulation's honesty depends on stating its limits. The basin map is schematic and is not geospatially accurate. Rainfall, water-level rise, mission durations, equipment capacities, and risk thresholds are illustrative scenario parameters, not calibrated hydrology. The application is single-user and local. It does not ingest real sensors, does not issue alerts, and does not control any gate, pump, vehicle, or crew. Java thread priority is treated only as a best-effort scheduling hint and never as a correctness or ordering mechanism. The session save format is private to this application and versioned; only locally created saves should be loaded. Finally, the exact hydrological realism of the scenario is explicitly not a project objective.

## 1.10 Organization of the Report

Chapter 2 states the requirements and analyses the system. Chapter 3 describes the architecture and design, including the runtime workflow. Chapter 4 examines the object-oriented design concept by concept, with code excerpts. Chapter 5 covers Java I/O and persistence. Chapter 6 treats multithreading and concurrency in depth. Chapter 7 documents the database and JDBC layer. Chapter 8 describes the user interface. Chapter 9 presents the implementation. Chapter 10 documents testing and validation. Chapter 11 reports results and discusses them. Chapter 12 concludes and outlines future scope. References and appendices follow.

%%% CHAPTER 2 %%%

# CHAPTER 2: REQUIREMENTS AND SYSTEM ANALYSIS

## 2.1 Existing Problem

In the absence of a dedicated tool, basin coordination is performed with a patchwork of documents, spreadsheets, and verbal updates. Such an approach struggles with three realities of the domain. First, observations and decisions have different rhythms: readings arrive continuously, while decisions are made at human speed, so any tool must buffer the difference. Second, resources are finite and shared, so the same pump or crew must not be promised twice. Third, the reasoning behind a decision is easily lost, so a durable record matters. These realities are not unique to flood operations — they recur wherever a changing situation is observed while limited resources are committed — which is what makes the scenario a good vehicle for studying concurrency and object-oriented design.

## 2.2 Proposed Solution

BasinWatch proposes a single, self-contained desktop application that models the coordination problem and makes its mechanics visible. The operator watches a schematic basin evolve, dispatches responses from a finite inventory, and reviews the consequences in a timeline. Under the surface, the application separates *producing* observations from *consuming* them with a bounded buffer, protects shared inventory with a short synchronized transaction, and persists its state through several complementary mechanisms. The solution is deliberately bounded: it demonstrates the mechanics faithfully while making no operational claims.

## 2.3 Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | The system shall present a schematic basin of six monitored zones. |
| FR-2 | Each zone shall expose a water level, latest rainfall, exposed population, and a risk category. |
| FR-3 | The system shall generate synthetic rainfall and water-level observations on a configurable interval. |
| FR-4 | The system shall allow the operator to advance the simulation one interval at a time. |
| FR-5 | The system shall allow the operator to inject a marked storm-cell observation into a selected zone. |
| FR-6 | The system shall validate every observation and discard malformed records with a visible warning. |
| FR-7 | The system shall rank zones by risk and highlight escalating risk. |
| FR-8 | The system shall maintain a finite inventory of pumps, levee crews, supply trucks, evacuation vehicles, and field crews. |
| FR-9 | The system shall allow the operator to dispatch pump, levee-reinforcement, and evacuation missions to a selected zone. |
| FR-10 | A dispatch shall reserve all of a mission's required resources atomically or be rejected. |
| FR-11 | Active missions shall advance deterministically with simulation intervals. |
| FR-12 | Completed missions shall return their resources to the shared inventory. |
| FR-13 | The system shall display available and committed units and active operations. |
| FR-14 | The system shall record operational events to a readable journal. |
| FR-15 | The system shall archive typed sensor measurements to a binary file. |
| FR-16 | The system shall save and restore a session, rejecting corrupt or unsupported files. |
| FR-17 | The system shall export a readable situation report. |
| FR-18 | The system shall retain an optional queryable history in an embedded database and shall continue operating when that database is unavailable. |

*Table 2.1: Functional requirements.*

## 2.4 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | The user interface shall remain responsive while observations and operations are processed. |
| NFR-2 | Shared state shall never be observed in a partially applied form. |
| NFR-3 | The event buffer shall be bounded so that memory cannot grow without limit. |
| NFR-4 | Shutdown shall stop new work, drain accepted work, and close files within a bounded time. |
| NFR-5 | Persistence failures shall be reported and shall not corrupt existing state. |
| NFR-6 | A corrupt or unexpected save file shall be rejected with an actionable message. |
| NFR-7 | The database shall be optional; its failure shall not stop the simulation or file persistence. |
| NFR-8 | The application shall run offline with no network dependency. |
| NFR-9 | The build shall be reproducible with Maven and shall bundle its single runtime dependency. |
| NFR-10 | The codebase shall be testable without an external test framework. |

*Table 2.2: Non-functional requirements.*

## 2.5 Hardware and Software Requirements

| Category | Requirement |
|---|---|
| Processor | Any modern 64-bit CPU (the workload is light and CPU-bound only briefly) |
| Memory | 2 GB or more (the application and its buffers are small) |
| Display | 1100×720 minimum window; 1440×860 typical |
| Operating system | Windows (primary deployment), Linux or macOS (development) |
| Runtime | JDK 17 or newer; the packaged Windows app image bundles a private runtime |
| Build tool | Maven 3.8 or newer |
| Database | None to install — SQLite is embedded |
| Network | Not required |

*Table 2.3: Hardware and software requirements.*

## 2.6 User Roles

BasinWatch defines a single role, the **operator**, who observes the basin, selects zones, dispatches responses, and manages sessions. There is no separate administrator role, no authentication, and no multi-user access, because the application is a local single-user simulation. The in-application "Learn" content is available to the same operator and requires no separate privilege.

## 2.7 Use Cases

| ID | Use case | Actor | Summary |
|---|---|---|---|
| UC-1 | Start/pause observations | Operator | Begin or suspend the synthetic observation feed |
| UC-2 | Advance one interval | Operator | Emit one interval of observations and advance missions |
| UC-3 | Inject storm cell | Operator | Queue a marked high-rainfall observation for a zone |
| UC-4 | Select a zone | Operator | Choose a zone from the map or the selector |
| UC-5 | Dispatch a response | Operator | Reserve resources and start a mission |
| UC-6 | Review active operations | Operator | Follow mission progress |
| UC-7 | Inspect background activity | Operator | View worker states and queue metrics |
| UC-8 | Save/restore session | Operator | Persist or recover the simulation |
| UC-9 | Export situation report | Operator | Write a readable report |
| UC-10 | View database history | Operator | Browse recent readings and records |

UC-5 includes UC-4, because a dispatch requires a selected zone.

*Table 2.4: Use cases.*

[[FIG:fig2_1_usecase.png|Figure 2.1: BasinWatch use-case diagram for the single operator role.]]

## 2.8 Constraints

The project is constrained to the standard JDK and Swing; no JavaFX runtime, web server, or external service is used. The only third-party runtime dependency is the SQLite JDBC driver. The simulation must run offline. The design must not rely on thread priority for correctness. The session format is application-private and versioned. Finally, the project must be demonstrable on a single machine without specialised hardware.

## 2.9 Feasibility

**Technical feasibility.** The application uses only standard, well-documented Java facilities: Swing for the interface, `java.io` for persistence, the language's built-in threading and monitor support for concurrency, and JDBC for the embedded database. Every mechanism used is part of the standard platform, so the project is technically feasible without bespoke infrastructure.

**Economic feasibility.** The software requires no licences, no server, and no cloud spend. The only cost is development time and the hardware already available to students.

**Operational feasibility.** Because the application is offline and self-contained, it can be demonstrated and graded on a single machine. Its data lives in a per-user folder and can be relocated with a single command-line option, so it does not interfere with the host system.

## 2.10 Assumptions

The design assumes that observations are synthetic and that their parameters are illustrative; that a single operator interacts with the application at a time; that the local file system is writable; that the embedded database may be absent or unusable, in which case the simulation must continue; and that thread scheduling is nondeterministic, so correctness must never depend on the order in which threads run.
