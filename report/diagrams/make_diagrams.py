#!/usr/bin/env python3
"""Generate BasinWatch report diagrams as editable PlantUML sources.

Every diagram is derived from verified repository classes/relationships.
"""
import os

OUT = os.path.dirname(os.path.abspath(__file__))

SKIN = """
skinparam shadowing false
skinparam defaultFontName "Segoe UI"
skinparam defaultFontSize 12
skinparam rectangleBackgroundColor #F7FAFC
skinparam rectangleBorderColor #2B5876
skinparam rectangleFontColor #16324F
skinparam componentBackgroundColor #EAF2F8
skinparam componentBorderColor #2B5876
skinparam databaseBackgroundColor #FDECEA
skinparam databaseBorderColor #A93226
skinparam classBackgroundColor #F4F9F9
skinparam classBorderColor #1F5C6B
skinparam classFontColor #123B47
skinparam actorBackgroundColor #FFF7E6
skinparam actorBorderColor #B7791F
skinparam noteBackgroundColor #FFFDF0
skinparam noteBorderColor #C9A227
skinparam arrowColor #33566B
"""

DIAGRAMS = {}

DIAGRAMS["fig1_1_context"] = SKIN + """
title BasinWatch System Context and Boundary
left to right direction
actor "Operator\\n(planner / student)" as OP
rectangle "BasinWatch - offline desktop application" as APP {
  usecase "Operations console\\n(Swing UI)" as UI
  usecase "Simulation engine\\n(threads, events, resources)" as ENG
  usecase "Local persistence\\n(streams + JDBC)" as PER
}
database "Local files\\nlogs / archive / saves / reports" as FILES
database "SQLite\\nbasinwatch.db" as DB
OP --> UI
UI --> ENG
ENG --> PER
PER --> FILES
PER --> DB
note bottom of DB
  Optional local history.
  No network, no external service,
  no real sensor, no real dispatch.
end note
@enduml
"""

DIAGRAMS["fig2_1_usecase"] = SKIN + """
title BasinWatch Use-Case Diagram
left to right direction
actor Operator as OP
rectangle BasinWatch {
  usecase "Start / pause\\nobservations" as UC1
  usecase "Advance one\\ninterval" as UC2
  usecase "Inject storm\\ncell" as UC3
  usecase "Select a\\nbasin zone" as UC4
  usecase "Dispatch a\\nresponse mission" as UC5
  usecase "Review active\\noperations" as UC6
  usecase "Inspect background\\nactivity" as UC7
  usecase "Save / restore\\nsession" as UC8
  usecase "Export situation\\nreport" as UC9
  usecase "View database\\nhistory" as UC10
}
OP --> UC1
OP --> UC2
OP --> UC3
OP --> UC4
OP --> UC5
OP --> UC6
OP --> UC7
OP --> UC8
OP --> UC9
OP --> UC10
UC5 ..> UC4 : <<include>>
UC8 ..> UC6 : <<include>>
@enduml
"""

DIAGRAMS["fig3_1_highlevel_arch"] = SKIN + """
title BasinWatch High-Level System Architecture
skinparam componentStyle rectangle
package "Presentation layer (Swing, EDT-owned)" {
  [MainFrame]
  [BasinMapPanel]
  [DatabaseHistoryPanel]
}
package "Application / Engine layer" {
  [BasinEngine]
  [SensorFeed]
  [SensorIntake]
  [EventBuffer]
  [ResponseWorker]
  [ArchiveWorker]
  [SimulationSettings]
}
package "Domain layer (aggregate + values)" {
  [BasinModel]
  [BasinZone]
  [ResourceAllocator]
  [ResponseMission]
  [BasinEvent <<interface>>]
}
package "Persistence layer" {
  [OperationalJournal]
  [SensorArchive]
  [SnapshotStore]
  [ReportWriter]
  [DatabaseService]
}
[MainFrame] --> [BasinEngine] : listens to snapshots
[BasinEngine] --> [BasinModel] : owns / processes
[BasinEngine] --> [EventBuffer]
[BasinEngine] --> [SensorFeed]
[BasinEngine] --> [SensorIntake]
[BasinEngine] --> [ResponseWorker]
[BasinEngine] --> [ArchiveWorker]
[BasinEngine] --> [OperationalJournal]
[BasinEngine] --> [SnapshotStore]
[BasinEngine] --> [ReportWriter]
[BasinEngine] --> [DatabaseService]
[BasinModel] --> [BasinZone]
[BasinModel] --> [ResourceAllocator]
[BasinModel] --> [ResponseMission]
[BasinModel] ..> [BasinEvent]
[ResponseWorker] ..> [BasinModel]
@enduml
"""

DIAGRAMS["fig3_2_package"] = SKIN + """
title Package Diagram
package com.basinwatch {
  package app
  package domain
  package engine
  package io
  package db
  package learning
}
app ..> engine
app ..> domain
app ..> io
app ..> db
app ..> learning
engine ..> domain
engine ..> io
engine ..> db
db ..> domain
io ..> domain
@enduml
"""

DIAGRAMS["fig3_3_dfd"] = SKIN + """
title Data-Flow Diagram (Level 1)
skinparam componentStyle rectangle
actor Operator as OP
rectangle "1.0\\nSensor emission" as P1
rectangle "2.0\\nIntake & validation" as P2
rectangle "3.0\\nEvent buffering" as P3
rectangle "4.0\\nResponse processing\\n(model + resources)" as P4
rectangle "5.0\\nSnapshot publishing\\n(EDT)" as P5
rectangle "6.0\\nPersistence\\n(files + SQLite)" as P6
database "D1 Event buffer" as D1
database "D2 Operational journal" as D2
database "D3 Sensor archive" as D3
database "D4 Session saves" as D4
database "D5 SQLite history" as D5
OP --> P1 : start/step
P1 --> P2 : encoded readings
P2 --> P3 : validated events
P3 --> P4 : accepted events
P4 --> P5 : immutable snapshot
P5 --> OP : updated console
P4 --> P6
P6 --> D2
P6 --> D3
P6 --> D4
P6 --> D5
P3 --> D1
@enduml
"""

DIAGRAMS["fig3_4_runtime_workflow"] = SKIN + """
title BasinWatch Runtime Workflow
skinparam componentStyle rectangle
[Operator] as OP
[Operations console\\n(MainFrame, EDT)] as UI
[SensorFeed\\nThread basin-sensor-feed] as FEED
[PipedWriter] as PW
[PipedReader +\\nBufferedReader] as PR
[SensorIntake\\nRunnable basin-sensor-intake] as INTAKE
[EventBuffer\\ncapacity 96\\nwait()/notifyAll()] as BUF
[ResponseWorker x3\\nbasin-response-1..3] as WK
[BasinModel.process\\nsynchronized] as MODEL
[ResourceAllocator\\ntryReserve / release] as RES
[ResponseMission\\nprogress on pulse] as MIS
[Immutable BasinSnapshot] as SNAP
[OperationalJournal] as J
[ArchiveWorker ->\\nsensors.bin] as ARC
[DatabaseService ->\\nSQLite] as DB
OP --> UI
UI --> FEED : start / pause
FEED --> PW : write encoded record
PW --> PR
PR --> INTAKE
INTAKE --> BUF : put (waits if full)
BUF --> WK : take (waits if empty)
WK --> MODEL
MODEL --> RES
MODEL --> MIS
MODEL --> SNAP
SNAP --> UI : invokeLater
WK --> J
WK --> ARC
WK --> DB
@enduml
"""

DIAGRAMS["fig3_5_domain_class"] = SKIN + """
title Domain Class Diagram
skinparam classAttributeIconSize 0
interface BasinEvent {
  +tick() : long
  +zoneId() : String
  +category() : String
  +describe() : String
}
class SensorReading <<record>>
class SimulationPulse <<record>>
class DispatchRequest <<record>>
class BasinModel {
  -zones : LinkedHashMap
  -missions : LinkedHashMap
  -activity : ArrayDeque
  -resources : ResourceAllocator
  +process(BasinEvent) : List
  +snapshot() : BasinSnapshot
  +{static} restore(BasinSnapshot) : BasinModel
}
class BasinZone {
  -waterLevelMeters : double
  -risk : RiskLevel
  +apply(SensorReading) : boolean
  +pump(double)
  +reinforceLevee()
  +evacuate()
  +snapshot() : ZoneSnapshot
}
class ResourceAllocator {
  -available : EnumMap
  -capacity : EnumMap
  +tryReserve(Map) : boolean
  +release(Map)
  +snapshot() : Map
}
class ResponseMission {
  -id : String
  -type : MissionType
  -status : MissionStatus
  +advance() : boolean
  +snapshot() : MissionSnapshot
}
enum ResourceType
enum MissionType
enum MissionStatus
enum RiskLevel
class ZoneSnapshot <<record>>
class MissionSnapshot <<record>>
class BasinSnapshot <<record>>
class ActivityEntry <<record>>
BasinEvent <|.. SensorReading
BasinEvent <|.. SimulationPulse
BasinEvent <|.. DispatchRequest
BasinModel "1" *-- "6" BasinZone : zones
BasinModel "1" *-- "0..500" ResponseMission : missions
BasinModel "1" *-- "1" ResourceAllocator : resources
BasinModel "1" o-- "*" ActivityEntry : activity
ResponseMission --> MissionType
ResponseMission --> MissionStatus
BasinZone --> RiskLevel
ResourceAllocator --> ResourceType
BasinModel ..> BasinSnapshot : returns
BasinSnapshot *-- ZoneSnapshot
BasinSnapshot *-- MissionSnapshot
@enduml
"""

DIAGRAMS["fig3_6_engine_ui_class"] = SKIN + """
title Engine and UI Class Diagram
skinparam classAttributeIconSize 0
class BasinEngine <<AutoCloseable>> {
  -eventBuffer : EventBuffer
  -settings : SimulationSettings
  -databaseService : DatabaseService
  -responseThreads : List<Thread>
  +start() : CompletableFuture
  +pause() : CompletableFuture
  +dispatch(String, MissionType) : boolean
  +save(Path) / load(Path)
  +exportReport() : CompletableFuture<Path>
  +closeAsync()
}
class EventBuffer {
  -events : ArrayDeque
  -capacity : int
  +put(BasinEvent) : boolean
  +take() : BasinEvent
  +close()
}
class SensorFeed <<Thread>> {
  +run()
  +requestStop()
}
class SensorIntake <<Runnable>> {
  +run()
}
class ResponseWorker <<Runnable>> {
  +run()
}
class ArchiveWorker <<Thread>> {
  +submit(SensorReading)
  +finish()
}
class SimulationSettings
class DatabaseService
class MainFrame <<JFrame>> {
  +updateSnapshot(BasinSnapshot)
  +refreshDiagnostics()
}
class BasinMapPanel <<JPanel>> {
  #paintComponent(Graphics)
}
class DatabaseHistoryPanel <<JPanel>>
class OperationalJournal
class SnapshotStore
class SensorArchive
class ReportWriter
BasinEngine *-- EventBuffer
BasinEngine *-- SimulationSettings
BasinEngine *-- DatabaseService
BasinEngine *-- SensorFeed
BasinEngine *-- SensorIntake
BasinEngine *-- ArchiveWorker
BasinEngine *-- "3" ResponseWorker
BasinEngine --> OperationalJournal
BasinEngine --> SnapshotStore
BasinEngine --> SensorArchive
BasinEngine --> ReportWriter
MainFrame --> BasinEngine : snapshot/status listeners
MainFrame *-- BasinMapPanel
MainFrame ..> DatabaseHistoryPanel
SensorFeed ..> EventBuffer : via pipe+intake
ResponseWorker ..> EventBuffer
@enduml
"""

DIAGRAMS["fig3_7_thread_map"] = SKIN + """
title Thread and Concurrency Map
skinparam componentStyle rectangle
rectangle "Swing Event Dispatch Thread (EDT)" as EDT
rectangle "basin-sensor-feed (Thread)" as FEED
rectangle "basin-sensor-intake (Runnable on Thread)" as INTAKE
rectangle "basin-response-1..3 (Runnable on Threads)" as WK
rectangle "basin-sensor-archive (Thread)" as ARC
rectangle "basin-control (daemon ExecutorService)" as CTRL
rectangle "basin-database (daemon ThreadPoolExecutor, 1 thread)" as DB
EDT --> CTRL : submits start/pause/save/load/report
CTRL --> FEED : startFeed()
FEED --> INTAKE : PipedWriter -> PipedReader
INTAKE --> WK : EventBuffer (bounded, monitor)
WK --> EDT : immutable snapshot via invokeLater
WK --> ARC : submit(SensorReading)
WK --> DB : enqueue immutable records
note right of WK
  wait()/notifyAll() coordinate
  buffer emptiness/fullness.
  ResourceAllocator uses one
  short synchronized monitor.
end note
@enduml
"""

DIAGRAMS["fig3_8_persistence_arch"] = SKIN + """
title Persistence Architecture
skinparam componentStyle rectangle
[BasinEngine] as ENG
[OperationalJournal\\nBufferedWriter UTF-8] as J
[ArchiveWorker\\nDataOutputStream] as A
[SnapshotStore\\nObjectOutputStream] as S
[ReportWriter\\nBufferedWriter UTF-8] as R
[DatabaseService\\nJDBC single thread] as D
database "operations.log" as F1
database "sensors.bin\\n(MAGIC 0x42574152 v1)" as F2
database "*.bws\\n(temp -> ATOMIC_MOVE)" as F3
database "*.txt reports" as F4
database "basinwatch.db\\nSQLite (4 tables)" as F5
ENG --> J
ENG --> A
ENG --> S
ENG --> R
ENG --> D
J --> F1
A --> F2
S --> F3
R --> F4
D --> F5
note bottom of F3
  5 MB limit; ObjectInputFilter
  allowlist on load.
end note
@enduml
"""

DIAGRAMS["fig3_9_er"] = SKIN + """
title SQLite Database ER Diagram
skinparam classAttributeIconSize 0
entity "sensor_readings" as SR {
  * id : INTEGER <<PK>>
  --
  timestamp : TEXT
  zone : TEXT
  water_level : REAL
  rainfall : REAL
  risk_level : TEXT
}
entity "missions" as MI {
  * id : TEXT <<PK>>
  --
  mission_type : TEXT
  zone : TEXT
  status : TEXT
  created_at : TEXT
  completed_at : TEXT
}
entity "resource_usage" as RU {
  * id : INTEGER <<PK>>
  --
  resource_type : TEXT
  amount : INTEGER
  mission_id : TEXT <<FK>>
  timestamp : TEXT
}
entity "operational_events" as OE {
  * id : INTEGER <<PK>>
  --
  timestamp : TEXT
  event_type : TEXT
  zone : TEXT
  message : TEXT
}
MI ||--o{ RU : "mission_id references id"
@enduml
"""

DIAGRAMS["fig5_2_save_restore"] = SKIN + """
title Session Save and Restore Flow
skinparam activityDiamondBackgroundColor #FFF3CD
start
:Operator selects "Save session";
:BasinEngine.save(path);
:stopFeed() if observations are live;
:awaitQuiescent() - drain accepted events;
:SessionSnapshot.from(snapshot) - validate via BasinModel.restore;
:encode() to ByteArrayOutputStream (ObjectOutputStream);
if (payload > 5 MB?) then (yes)
  :IOException - session too large;
  stop
else (no)
  :write to temporary file;
  :Files.move ATOMIC_MOVE (fallback REPLACE_EXISTING);
  :resume feed if it was running;
  :status "Session saved";
endif
:On relaunch: SnapshotStore.load(path);
:size check, ObjectInputFilter allowlist;
:readObject -> SessionSnapshot;
:version + domain invariant checks;
:BasinModel.restore -> fresh runtime primitives;
stop
@enduml
"""

DIAGRAMS["fig6_1_thread_lifecycle"] = SKIN + """
title Java Thread Lifecycle as Used by BasinWatch
skinparam stateBackgroundColor #F4F9F9
skinparam stateBorderColor #1F5C6B
[*] --> NEW : new Thread(...)
NEW --> RUNNABLE : start()
RUNNABLE --> BLOCKED : waiting to enter synchronized
BLOCKED --> RUNNABLE : monitor acquired
RUNNABLE --> WAITING : wait() on EventBuffer
WAITING --> RUNNABLE : notifyAll() / interrupt()
RUNNABLE --> TIMED_WAITING : Thread.sleep(intervalMillis)
TIMED_WAITING --> RUNNABLE : delay elapsed / interrupt
RUNNABLE --> TERMINATED : run() returns
note right of WAITING
  Java reports RUNNABLE, not a
  separate RUNNING state.
  wait() releases the monitor;
  sleep() does not.
end note
@enduml
"""

DIAGRAMS["fig6_2_producer_consumer"] = SKIN + """
title Bounded Producer-Consumer Event Buffer
skinparam componentStyle rectangle
rectangle "Producer: SensorIntake" as P
queue "EventBuffer (capacity 96)\\nArrayDeque + intrinsic monitor" as Q
rectangle "Consumers: ResponseWorker x3" as C
P --> Q : put(event)\\nwait() while full
Q --> C : take()\\nwait() while empty
Q --> Q : notifyAll() after add/remove/close
note bottom of Q
  close() sets closed=true and notifyAll();
  waiters re-check the condition in a while loop,
  so a closed buffer drains accepted work then
  returns null (end of stream).
end note
@enduml
"""

DIAGRAMS["fig6_3_resource_allocation"] = SKIN + """
title Atomic Resource Reservation
skinparam activityDiamondBackgroundColor #FFF3CD
start
:DispatchRequest for (zone, missionType);
:validateRequest(requirements);
if (all required units available?) then (no)
  :return false (typed rejection);
  :record RESOURCE LIMIT;
  stop
else (yes)
  :decrement every required type;
  :return true;
  :create ResponseMission (ACTIVE);
  :record UNIT ALLOCATED;
endif
:Mission advances on each SimulationPulse;
if (progressTicks == durationTicks?) then (yes)
  :status = COMPLETED;
  :resources.release(requirements);
  :record MISSION COMPLETE;
else (no)
  :remain ACTIVE;
endif
stop
note right
  tryReserve/release are synchronized:
  check-and-decrement is all-or-nothing,
  so two dispatches cannot claim the
  same final unit.
end note
@enduml
"""

DIAGRAMS["fig6_4_app_lifecycle"] = SKIN + """
title Application Lifecycle
skinparam stateBackgroundColor #F4F9F9
skinparam stateBorderColor #1F5C6B
[*] --> Starting : main() -> invokeLater
Starting --> Restoring : last-session.bws exists?
Restoring --> Ready : restore OK / user starts fresh
Ready --> Running : start() -> feed + intake + 3 workers
Running --> Paused : pause() -> stopFeed()
Paused --> Running : resume
Running --> Running : dispatch / step / inject storm / save / report
Running --> Closing : window close -> closeAsync()
Closing --> Closing : stopFeed, close buffer, join workers,\\ndrain archive, close DB
Closing --> Saved : write last-session.bws
Saved --> [*] : journal close, EDT dispose
@enduml
"""

DIAGRAMS["fig7_1_jdbc_arch"] = SKIN + """
title JDBC Architecture
skinparam componentStyle rectangle
[BasinWatch simulation\\n(engine + workers)] as SIM
[DatabaseService\\nsingle-thread executor\\nqueue 2048, AbortPolicy] as SVC
[SensorReadingRepository] as R1
[MissionRepository\\ntransactions] as R2
[ResourceUsageRepository] as R3
[OperationalEventRepository] as R4
[DatabaseManager\\nConnection, PRAGMAs] as MGR
[DatabaseInitializer\\nCREATE TABLE/INDEX] as INIT
database "SQLite basinwatch.db" as DB
[SIM] --> [SVC] : enqueue immutable values
[SVC] --> R1
[SVC] --> R2
[SVC] --> R3
[SVC] --> R4
R1 --> MGR
R2 --> MGR
R3 --> MGR
R4 --> MGR
MGR --> DB
INIT --> DB
note bottom of DB
  Embedded, offline, no server.
  SQLException is reported and isolated;
  the simulation and file persistence continue.
end note
@enduml
"""

DIAGRAMS["fig8_3_sequence_sensor"] = SKIN + """
title Sequence Diagram - Sensor / Event Pipeline
skinparam sequenceMessageAlign center
participant "SensorFeed\\n(Thread)" as FEED
participant "PipedWriter/\\nReader" as PIPE
participant "SensorIntake\\n(Runnable)" as INTAKE
participant "EventBuffer\\n(96)" as BUF
participant "ResponseWorker" as WK
participant "BasinModel" as MODEL
participant "EDT / UI" as UI
loop every intervalMillis (default 1500 ms)
  FEED -> FEED : tickSequence.incrementAndGet()
  FEED -> PIPE : write(reading.encode()) + '\\n'
  FEED -> PIPE : write("PULSE|" + tick)
  PIPE -> INTAKE : readLine()
  INTAKE -> INTAKE : SensorReading.parse / SimulationPulse
  alt malformed
    INTAKE -> INTAKE : report warning, discard
  else valid
    INTAKE -> BUF : put(event)
    BUF -> BUF : wait() if full
    WK -> BUF : take()
    BUF -> BUF : wait() if empty; notifyAll()
    WK -> MODEL : process(event) [synchronized]
    MODEL -> MODEL : applyReading / applyPulse / applyDispatch
    WK -> UI : invokeLater(immutable snapshot)
    WK -> BUF : complete()
  end
end
@enduml
"""

DIAGRAMS["fig8_4_sequence_dispatch"] = SKIN + """
title Sequence Diagram - Resource Dispatch and Mission Completion
skinparam sequenceMessageAlign center
actor Operator as OP
participant "MainFrame\\n(EDT)" as UI
participant "BasinEngine" as ENG
participant "EventBuffer" as BUF
participant "ResponseWorker" as WK
participant "BasinModel" as MODEL
participant "ResourceAllocator" as RES
participant "DatabaseService" as DB
OP -> UI : choose zone + mission, click Dispatch
UI -> ENG : dispatch(zoneId, missionType)
ENG -> BUF : offerAll(DispatchRequest)
BUF -> WK : take()
WK -> MODEL : process(DispatchRequest)
MODEL -> RES : tryReserve(requirements)
alt units unavailable
  RES --> MODEL : false
  MODEL --> WK : "Insufficient available units"
else units available
  RES --> MODEL : true (decremented)
  MODEL -> MODEL : new ResponseMission ACTIVE
  WK -> DB : recordDispatch (transaction)
end
WK -> UI : snapshot (inventory + mission list)
note over MODEL, RES
  Each SimulationPulse advances ACTIVE missions;
  on completion, requirements are released back
  to the allocator and completion is persisted.
end note
@enduml
"""

DIAGRAMS["fig8_6_operator_activity"] = SKIN + """
title Activity Diagram - Operator Workflow
skinparam activityDiamondBackgroundColor #FFF3CD
start
:Launch BasinWatch;
if (last-session.bws exists?) then (yes)
  :Restore previous session;
else (no)
  :Start fresh scenario (6 zones);
endif
:Start observations (or Advance one interval);
:Read basin map risk colours;
if (a zone shows elevated risk?) then (yes)
  :Select the zone;
  :Review water level, rain, exposure, stock;
  :Choose a mission type;
  :Dispatch response (atomic reservation);
  if (reservation accepted?) then (no)
    :See RESOURCE LIMIT message;
  else (yes)
    :Follow mission progress in Operations tab;
  endif
else (no)
  :Monitor observations;
endif
:Inspect background activity / database history (optional);
:Export situation report;
:Save session / close cleanly (auto-save last-session.bws);
stop
@enduml
"""

DIAGRAMS["fig4_1_oop_mapping"] = SKIN + """
title OOP Concept Mapping to BasinWatch Components
skinparam componentStyle rectangle
package "OOP / Java concept" {
  [Encapsulation] as C1
  [Abstraction] as C2
  [Inheritance] as C3
  [Polymorphism] as C4
  [Composition] as C5
  [Enums & Immutability] as C6
  [Exceptions] as C7
  [Threads & Monitors] as C8
  [Producer-Consumer] as C9
  [Serialization] as C10
  [JDBC] as C11
}
package "BasinWatch component" {
  [domain/BasinZone, ResourceAllocator] as P1
  [domain/BasinEvent] as P2
  [engine/SensorFeed, app/MainFrame] as P3
  [domain/BasinModel.process] as P4
  [domain/BasinModel, engine/BasinEngine] as P5
  [domain/* enums, *Snapshot records] as P6
  [domain/*, io/*, db/*] as P7
  [engine/EventBuffer, ResourceAllocator] as P8
  [engine/EventBuffer] as P9
  [io/SessionSnapshot, SnapshotStore] as P10
  [db/* repositories] as P11
}
C1 --> P1
C2 --> P2
C3 --> P3
C4 --> P4
C5 --> P5
C6 --> P6
C7 --> P7
C8 --> P8
C9 --> P9
C10 --> P10
C11 --> P11
@enduml
"""

count = 0
for name, body in DIAGRAMS.items():
    with open(os.path.join(OUT, name + ".puml"), "w", encoding="utf-8") as fh:
        fh.write("@startuml\n" + body.strip() + "\n")
    count += 1
print(f"wrote {count} .puml files")
