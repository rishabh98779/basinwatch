# BasinWatch — Phase 2 Consolidated Verified Technical Model
Repository: https://github.com/Rishu07368/basinwatch
HEAD: 45b40c0 ("db"), 2026-10-02, branch main
Verification: cloned, read every file, built with OpenJDK 21 + Maven 3.9.9,
ran InvariantSuite (76 assertions passed), captured 7 real UI screenshots under Xvfb.

Evidence grades: [A] verified in repo/executed; [B] visible in uploaded PDF;
[C] reasonable interpretation; [D] general technical background; [E] unavailable.

## 1. Verified technology stack [A]
- Java 17 (maven.compiler.release=17); Maven build.
- Plugins: compiler 3.13.0, jar 3.4.2 (Main-Class com.basinwatch.app.BasinWatchApp), shade 3.6.0.
- Sole runtime dependency: org.xerial:sqlite-jdbc:3.50.3.0.
- UI: Java Swing. Concurrency: java.util.concurrent + monitors.
- Tests: dependency-free assertion main() run with -ea via scripts/test.ps1.

## 2. Package/file/LOC inventory [A]
app 4 files 1260 LOC | domain 17/765 | engine 8/997 | io 10/583 | db 9/738 | learning 2/114
test 1/516. Main total 4457 LOC; grand total 4973 LOC. 50 main classes + 1 test class.

## 3. Exact line citations for code excerpts [A]
- app/BasinWatchApp.java: main=20, invokeLater=27, AppPaths.create=33, new BasinModel=40,
  last-session.bws=41, SnapshotStore().load=44, BasinModel.restore=45, new BasinEngine=59,
  new MainFrame=60, setVisible=61.
- engine/BasinEngine.java: WORKER_COUNT=41, JOIN_TIMEOUT_MILLIS=42, new EventBuffer(96)=45,
  start()=123, worker loop=132, dispatch=154, injectStorm=160, step=168, startFeed=279,
  stopFeed=305, closeEngine=340, awaitQuiescent=419, join()=435, process=441,
  persistDatabase=474, publishSnapshot=507, ResponseWorker=595, take()=601.
- engine/EventBuffer.java: put=23 (while=27, wait=30, notifyAll=39), offerAll=43,
  take=55 (while=56, wait=59), complete=73, close=81.
- engine/SensorFeed.java: extends Thread=12, run=33, write encode=42, flush=46,
  sleep(intervalMillis)=47, InterruptedException=49, requestStop=66.
- engine/SensorIntake.java: implements Runnable=11, run=26, readLine=29, PULSE=32,
  parse=35, malformed catch=37, put=42.
- domain/ResourceAllocator.java: tryReserve=36 (availability loop=39, decrement=43),
  release=47, snapshot=57, validateRequest=61, standard()=27.
- domain/BasinModel.java: process=44, applyReading=61, applyPulse=79, applyDispatch=103,
  snapshot=127, restore=151, requireZone=230, record=238.
- domain/ResponseMission.java: overloaded ctors=11/15, advance=25, snapshot=37.
- domain/MissionType.java: PUMP=6, LEVEE=8, EVAC=10, fields=14-16, ctor=18.
- io/SensorArchive.java: MAGIC=15, FORMAT_VERSION=16, ctor=19, append=40, close=49.
- io/SnapshotStore.java: MAX_SAVE_BYTES=21, save=23, ATOMIC_MOVE=42, load=55,
  readNBytes=65, encode=78, decode=87, setObjectInputFilter=89, filter=100.
- io/SessionSnapshot.java: serialVersionUID=23, CURRENT_VERSION=24, transient hint=33,
  from=38, toBasinSnapshot=66.
- io/OperationalJournal.java: append=22, newBufferedWriter=18, pendingLines=29, flush=32.
- io/ReportWriter.java: write=26, newBufferedWriter=30, sections=38/46/54/63.
- io/AppPaths.java: record=8, resolveDataRoot=10, --data-dir=14, defaultDataRoot=22,
  APPDATA=26, .basinwatch=32, create=36, database=42.
- db/DatabaseManager.java: jdbc:sqlite=17, openConnection=24, busy_timeout=36, foreign_keys=37.
- db/DatabaseInitializer.java: 4 CREATE TABLE (10/20/30/39), 4 indexes (47-50), initialize=56.
- db/MissionRepository.java: recordDispatch=31, setAutoCommit(false)=35, commit=48,
  rollback=50, updateStatus=56, findRecent=86, rollback helper=115.
- db/SensorReadingRepository.java: INSERT=16, findRecent=45, executeQuery=56, deleteBefore=73.
- db/DatabaseService.java: QUEUE_CAPACITY=2048 (25), HISTORY_LIMIT=200 (26),
  SENSOR_RETENTION=30d (27), ThreadPoolExecutor(1,1)=59, AbortPolicy=61,
  recordSensor=77, recordDispatch=89, recordCompletion=95, loadHistory=99, close=128,
  initializeAndPrune=151, ensureInitialized=161, enqueue=185.

## 4. Runtime pipeline [A]
SensorFeed(Thread basin-sensor-feed) -> PipedWriter -> PipedReader(8192)+BufferedReader ->
SensorIntake(Runnable basin-sensor-intake) -> EventBuffer(96) [wait/notifyAll] ->
3x ResponseWorker(basin-response-1..3) -> BasinModel.process [synchronized] +
ResourceAllocator [synchronized] + mission progress -> immutable BasinSnapshot ->
snapshotListeners -> SwingUtilities.invokeLater -> EDT -> UI.
Side channels: OperationalJournal (BufferedWriter), ArchiveWorker(basin-sensor-archive)
-> SensorArchive DataOutputStream->sensors.bin, DatabaseService(basin-database single
thread)->JDBC->SQLite, ReportWriter, SnapshotStore. Control plane: single daemon
basin-control executor via CompletableFuture.

## 5. Constants/parameters [A]
Buffer capacity 96; workers 3; join timeout 8000 ms; default interval 1500 ms
(range 350-8000); storm intensity 0.2-2.5; save limit 5 MB; DB queue 2048; history
limit 200; sensor retention 30 days; activity limit 160; mission history cap 500;
resource standard stock PUMP 3, LEVEE_CREW 3, SUPPLY_TRUCK 2, EVAC_VEHICLE 2,
FIELD_CREW 4; risk thresholds 1.7/2.6/3.6 m; 6 zones UPR/MIL/NOR/OLD/MAR/SOU.
Mission durations/effects: PUMP 8 ticks/0.62 m; LEVEE 10 ticks/0.0 m; EVAC 6 ticks/0.0 m.

## 6. Persistence artefacts [A]
logs/operations.log (UTF-8 BufferedWriter append; flush every 12 lines or on
WARNING/COMPLETE/ALLOCATED); archive/sensors.bin (MAGIC 0x42574152, version 1,
typed long/UTF/UTF/double/double); saves/*.bws (Serializable SessionSnapshot,
temp+ATOMIC_MOVE, ObjectInputFilter allowlist depth<=12 refs<=2000);
reports/*.txt (UTF-8 BufferedWriter); data/basinwatch.db (SQLite, 4 tables).

## 7. SQLite schema [A]
sensor_readings(id PK AI, timestamp TEXT, zone TEXT, water_level REAL, rainfall REAL,
risk_level TEXT); missions(id TEXT PK, mission_type, zone, status, created_at,
completed_at); resource_usage(id PK AI, resource_type, amount CHECK>0, mission_id
REFERENCES missions(id), timestamp); operational_events(id PK AI, timestamp,
event_type, zone, message). Indexes on the four time columns.

## 8. Testing [A] (executed)
InvariantSuite -> "BasinWatch invariant suite passed (76 assertions)."
10 suites: parsesAndValidatesSensorEvents; reservesSharedResourcesAtomically
(24 contenders, exactly 1 accepted); coordinatesBoundedEventBuffer (wait/back-pressure/
close); advancesAndReleasesResponseMissions; savesRestoresAndRejectsUnsafeSnapshots;
validatesArchiveHeaders; resolvesPerUserDataLocations; persistsJdbcHistoryAndTransactions;
runsACompleteOfflineEngineSession; continuesWhenDatabaseIsUnavailable.

## 9. Runtime evidence captured by us [A]
Report exported 10867 bytes; SQLite rows: sensor_readings 158, missions 3,
resource_usage 6, operational_events 8. Screenshots: 00_startup, 01_console_live,
02_basin_map, 03_operations, 04_insights, 05_database, 06_learn (1440x900 each).

## 10. Discrepancies (docs vs code) [A]
ARCHITECTURE.md uses FloodZone/SensorStation/ResponseWorker-as-file; code has BasinZone
(no SensorStation); ResponseWorker is a private inner class of BasinEngine.
Docs' "FloodZone" == code "BasinZone". Report uses code names.

## 11. Deliberate exclusions [A]
No abstract classes (0); no Thread.stop/suspend/resume; no "RUNNING" state
(Thread.State reported verbatim); priority never a correctness mechanism;
wait() != sleep(); synchronization alone does not prevent all deadlocks.

## 12. Source-of-truth matrix
Technical implementation -> repository [A]; executed results -> our run [A];
report structure -> sample PDF [B, structure only]; CU header -> CU PDF [B];
Java/JDBC/Swing semantics -> official docs [D]; supervisor/class/date -> [E] placeholders.

## 13. Placeholders to use [E]
[SUPERVISOR NAME - TO BE PROVIDED], [HOD NAME - TO BE PROVIDED],
[INTERNAL EXAMINER - TO BE PROVIDED], [EXTERNAL EXAMINER - TO BE PROVIDED],
[CLASS/SECTION/GROUP - TO BE PROVIDED], [ACADEMIC SESSION - TO BE PROVIDED],
[DATE OF SUBMISSION - TO BE PROVIDED].
Authoritative students: Saumya Dwivedi 25BCS12109; Rishabh Singh 25BCS11466;
Anshu Anand 25BCS11475; Deepshikha Yadav 25BCS10801. Subject OOP 25CSH-208, 3rd Sem, BE CSE.
