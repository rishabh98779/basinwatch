%%% CHAPTER 7 %%%

# CHAPTER 7: DATABASE AND JDBC

## 7.1 Need for Database History

The file journal and binary archive preserve what happened, but they are not convenient to query. An operator who wants to see the twenty most recent readings in a particular zone, or to list every completed mission, would otherwise have to read and parse files. A relational database provides indexed, structured queries for exactly this purpose. BasinWatch therefore adds an **optional** embedded database as a supplementary history store. It is deliberately supplementary: the archive, journal, reports, and session snapshots remain the primary persistence mechanisms, and the database is never a dependency for the simulation.

## 7.2 SQLite

SQLite is an embedded, file-based relational database. There is no server process to install, start, or connect to; the database is a single file, and the JDBC driver links the database engine directly into the application. This makes SQLite an excellent fit for an offline desktop application: it provides real SQL and real transactions without any operational infrastructure. In BasinWatch the database file is `data/basinwatch.db`, placed beside the application's other data folders.

## 7.3 JDBC Architecture

JDBC is Java's standard API for relational databases. An application uses the same `Connection`, `PreparedStatement`, and `ResultSet` types regardless of the underlying database, while a driver translates those standard calls into the database's own protocol. BasinWatch uses the Xerial SQLite JDBC driver, declared in `pom.xml` and bundled into the shaded JAR so that the run command works without a separate classpath. Figure 7.1 shows the layer.

[[FIG:fig7_1_jdbc_arch.png|Figure 7.1: JDBC architecture of the BasinWatch database layer.]]

| JDBC concept | BasinWatch implementation |
|---|---|
| JDBC driver | Xerial `sqlite-jdbc` declared in `pom.xml` |
| `Connection` | `DatabaseManager.openConnection()` opens and configures a connection |
| `PreparedStatement` | Repositories bind values with `setString`, `setDouble`, `setInt` |
| `ResultSet` | Repository `findRecent` methods read rows into immutable entries |
| `SQLException` | `DatabaseService` reports failures; the simulation continues |
| Transaction | `MissionRepository` commits a mission with its resources and event together |

*Table 7.1: JDBC concepts and their BasinWatch implementations.*

## 7.4 Connection

Connections are opened per repository operation and closed with try-with-resources. The manager builds the JDBC URL from the database path and configures two pragmas: a busy timeout of five seconds, so a brief lock contention does not fail immediately, and foreign-key enforcement, so the reference from `resource_usage` to `missions` is honoured.

```java
// db/DatabaseManager.java (openConnection, line 24)
public Connection openConnection() throws SQLException {
    Path parent = databasePath.getParent();
    if (parent == null) {
        throw new SQLException("SQLite database needs a parent directory.");
    }
    Files.createDirectories(parent);
    Connection connection = DriverManager.getConnection(jdbcUrl);
    try (Statement statement = connection.createStatement()) {
        statement.execute("PRAGMA busy_timeout = 5000");
        statement.execute("PRAGMA foreign_keys = ON");
    }
    return connection;
}
```

*Listing 7.1: Opening and configuring a SQLite connection.*

## 7.5 PreparedStatement

Every value written or queried is bound through a `PreparedStatement` parameter rather than concatenated into a string. This has two benefits: it prevents SQL injection through recorded values, and it lets the database reuse the compiled statement.

```java
// db/SensorReadingRepository.java (findRecent, line 45, condensed)
String sql = """
        SELECT timestamp, zone, water_level, rainfall, risk_level
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT ?
        """;
try (Connection connection = database.openConnection();
     PreparedStatement statement = connection.prepareStatement(sql)) {
    statement.setInt(1, limit);
    try (ResultSet results = statement.executeQuery()) {
        // map rows to immutable DatabaseHistoryEntry values
    }
}
```

*Listing 7.2: A parameterized query with try-with-resources for the connection, statement, and result set.*

## 7.6 ResultSet

A `ResultSet` is a cursor over the rows a query returned. Repositories read each row and map it into an immutable `DatabaseHistoryEntry`, so that no JDBC type leaks into the interface. The history panel then displays these entries in a table.

## 7.7 SQLException

`SQLException` is the checked exception JDBC uses to report database problems. The project never swallows it silently: `DatabaseService` catches it, marks the database as uninitialized so that a later operation can retry, and reports the failure to the engine, which records it in the operational journal and surfaces it in the interface.

## 7.8 Transactions

A transaction groups several statements so that they either all take effect or none do. This matters for mission dispatch, where three things must stay consistent: the mission row, the resource-usage rows, and the dispatch event. `MissionRepository.recordDispatch` performs all three on one connection with auto-commit disabled, commits them together, and rolls back if any statement fails.

```java
// db/MissionRepository.java (recordDispatch, line 31, condensed)
try (Connection connection = database.openConnection()) {
    connection.setAutoCommit(false);
    try {
        // INSERT mission
        resourceUsage.insert(connection, mission.id(), resources, createdAt);
        operationalEvents.insert(connection, createdAt, "MISSION DISPATCH",
                mission.zoneId(), message);
        connection.commit();
    } catch (SQLException ex) {
        rollback(connection, ex);
        throw ex;
    }
}
```

*Listing 7.3: A transaction that keeps the mission, its resources, and its event consistent.*

## 7.9 Database Schema

The schema is created at startup by `DatabaseInitializer` using `CREATE TABLE IF NOT EXISTS` statements, followed by four indexes on the timestamp columns. Figure 3.9 in Chapter 3 shows the entity-relationship diagram; Table 7.2 lists the columns.

| Table | Columns | Notes |
|---|---|---|
| `sensor_readings` | id, timestamp, zone, water_level, rainfall, risk_level | id autoincrement primary key |
| `missions` | id, mission_type, zone, status, created_at, completed_at | id is the mission identifier |
| `resource_usage` | id, resource_type, amount, mission_id, timestamp | amount `CHECK (amount > 0)`; `mission_id` references `missions(id)` |
| `operational_events` | id, timestamp, event_type, zone, message | id autoincrement primary key |

*Table 7.2: SQLite schema.*

## 7.10 Repository Layer

Each table has a repository that owns the SQL for that table. This keeps query text in one place and lets the service layer work with domain values rather than with SQL. `SensorReadingRepository` inserts readings and reads recent ones; `MissionRepository` records dispatch and completion inside transactions; `ResourceUsageRepository` inserts batched resource rows and reads recent allocations; `OperationalEventRepository` inserts and reads events.

| Repository | Responsibility |
|---|---|
| `SensorReadingRepository` | Insert readings; read recent readings; delete readings older than the retention cutoff |
| `MissionRepository` | Transactional dispatch and completion; read recent missions |
| `ResourceUsageRepository` | Insert a mission's resource allocations; read recent allocations |
| `OperationalEventRepository` | Insert and read operational events |

*Table 7.3: Repository responsibilities.*

## 7.11 Database Service

`DatabaseService` is the single point of contact between the simulation and the database. It owns a single-threaded executor with a bounded queue of two thousand and forty-eight tasks and an abort policy. Every database operation is enqueued as a task, so all SQL runs on the `basin-database` thread and never on the Swing EDT. At startup the service initializes the schema and prunes sensor readings older than thirty days.

## 7.12 Asynchronous Database Operations

Because the service runs on its own thread, the response workers that call `recordSensor`, `recordDispatch`, and `recordCompletion` do not block on SQL. They enqueue immutable values and continue. Reads are returned as `CompletableFuture` instances, so the history panel can request data without freezing and update its table when the future completes on the EDT. If the queue is full, the service reports that the update was not accepted rather than blocking the caller.

## 7.13 Database Failure Handling

The database is optional, and the code treats it as such. If initialization fails, the service records the failure and continues to report an unavailable status; later operations retry initialization after a short delay. Crucially, a database failure never stops the simulation and never affects the file-based persistence: the journal, archive, reports, and session saves continue to work. The test suite demonstrates this directly by making the database path unusable and confirming that the simulation still processes events and that the file archive, session save, and journal are all written, with the failure recorded as a `DATABASE WARNING` in the journal.

%%% CHAPTER 8 %%%

# CHAPTER 8: USER INTERFACE

## 8.1 Swing Architecture

The user interface is built with standard Swing. Swing follows a model-view-controller philosophy: components hold a model, render a view, and respond to events. BasinWatch uses this structure directly. Lists are backed by `DefaultListModel` instances, and the database history table is backed by a custom `AbstractTableModel`. The basin map is a custom component that paints itself.

## 8.2 Event Dispatch Thread

All Swing components are created and modified on the event-dispatch thread. The engine's workers never touch a component; instead they publish immutable snapshots, and the frame subscribes with a listener that hands each snapshot to the EDT.

```java
// app/MainFrame.java (constructor, line 112)
engine.addSnapshotListener(snapshot ->
        SwingUtilities.invokeLater(() -> updateSnapshot(snapshot)));
engine.addStatusListener(message ->
        SwingUtilities.invokeLater(() -> statusLabel.setText(message)));
```

*Listing 8.1: The frame marshals every engine update onto the event-dispatch thread.*

This is the interface's side of the immutability contract: because the snapshot is immutable, it can be captured in a lambda and applied later on the EDT without any risk that the model has changed underneath it.

## 8.3 Main Operations Console

The main console is a single frame with a header, a toolbar, a central work area, and a footer. The toolbar offers the primary actions — start or pause observations, advance one interval, inject a storm cell, save a session, restore a session, and export a situation report. The central area is split horizontally between the basin map and a tabbed panel, and vertically between that work area and the operations timeline.

[[FIG:assets/screenshots/00_startup.png|Figure 8.1: The main BasinWatch console at startup, with observations paused.]]

| Component | Type | Responsibility |
|---|---|---|
| `MainFrame` | `JFrame` | Hosts the toolbar, work area, and footer; marshals updates to the EDT |
| `BasinMapPanel` | `JPanel` (custom paint) | Draws the schematic basin and zones; handles zone selection |
| `DatabaseHistoryPanel` | `JPanel` | Displays database history in a table |
| `HistoryTableModel` | `AbstractTableModel` | Backs the history table |
| `MissionRenderer` | `DefaultListCellRenderer` | Renders mission rows in the mission list |

*Table 8.1: Swing UI components.*

| Tab | Purpose |
|---|---|
| Response | Selected zone summary, mission selector, dispatch, and field-unit counts |
| Operations | Active and completed field missions with progress |
| Insights | Systems inspector: thread states, queue depth, processed events |
| Learn | In-application architecture notes |
| Database history | Recent records from the embedded database |

*Table 8.2: Console tabs and their purpose.*

| Control | Action |
|---|---|
| Start / Pause observations | Begin or suspend the synthetic feed |
| Advance one interval | Emit one interval and advance missions |
| Inject storm cell | Queue a marked high-rainfall reading for the selected zone |
| Save session | Persist the current session to a named file |
| Restore session | Load a saved session |
| Export situation report | Write a readable text report |
| Dispatch | Reserve resources and start the chosen mission |

*Table 8.3: Operator controls.*

## 8.4 Basin Map

The basin map is a custom-painted panel. It draws a schematic river and six zone tiles, each showing the zone name, its risk category in a risk-coloured badge, its water level, its latest rainfall, and its exposed population, together with a small water-level bar. The panel is explicitly labelled as an illustrative basin layout rather than a geographic forecast. Zones are selectable by mouse click, and the panel exposes an accessible name so that the zone selector can be used for keyboard navigation.

```java
// app/BasinMapPanel.java (paintComponent, line 59, condensed)
protected void paintComponent(Graphics graphics) {
    super.paintComponent(graphics);
    Graphics2D g = (Graphics2D) graphics.create();
    g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
    paintRiver(g);
    hitTargets.clear();
    for (ZoneSnapshot zone : snapshot.zones()) {
        Rectangle bounds = /* computed tile rectangle */;
        hitTargets.put(zone.id(), bounds);
        paintZone(g, zone, bounds, zone.id().equals(selectedZone));
    }
    g.dispose();
}
```

*Listing 8.2: The map panel paints the river and each zone, and records hit targets for mouse selection.*

[[FIG:assets/screenshots/01_console_live.png|Figure 8.2: The console during a live simulation with active response missions.]]

## 8.5 Systems Inspector

The systems inspector is the "Insights" tab. It reports the state, name, and priority of every background thread, the current queue depth against its capacity, the number of processed events, and the archive backlog and waiting counts. It also hosts the optional archive-priority experiment. This view is diagnostic: the application works perfectly without it, but it makes the concurrency of the system visible, which is valuable in an educational tool.

[[FIG:assets/screenshots/04_insights.png|Figure 8.8: The systems inspector showing background thread states and queue metrics.]]

## 8.6 Response Desk

The "Response" tab is the response desk. It shows the selected zone's name, risk, water level, and rainfall; a mission-type selector and a dispatch button; and the available field units with their committed counts. The dispatch button is enabled only once the simulation has started. A short clarification reminds the operator that levels and exposure are scenario estimates, not live forecasts.

[[FIG:fig8_4_sequence_dispatch.png|Figure 8.3: Sequence diagram of resource dispatch and mission completion.]]

## 8.7 Activity Feed

The operations timeline at the bottom of the console is the activity feed. It shows the most recent activity entries in reverse order, colour-coded by category, so the operator can follow risk updates, allocations, completions, and system events as they occur.

## 8.8 Database History

The "Database history" tab presents a table of recent records drawn from the SQLite database. The operator selects a category — sensor readings, missions, operational events, or resource usage — and the panel requests the data asynchronously, updating the table on the EDT when the future completes. The panel also shows the database status and the number of pending database writes.

[[FIG:assets/screenshots/05_database.png|Figure 8.4: The database history tab displaying recent records.]]

## 8.9 User Interaction Flow

Figure 8.5 shows the operator's workflow: launch, restore or start fresh, start observations, read the map, select an at-risk zone, choose and dispatch a mission, follow progress, optionally inspect background activity and database history, export a report, and close cleanly.

[[FIG:fig8_6_operator_activity.png|Figure 8.5: Activity diagram of the operator workflow.]]

## 8.10 UI State Updates

The interface is refreshed by a single `updateSnapshot` method that the EDT runs whenever a new snapshot arrives. That method updates the map, the selected-zone summary, the risk tally, the resource labels, the mission list, and the activity list. A separate timer refreshes the diagnostic labels. Because both paths run on the EDT, there is no concurrent access to any component.

## 8.11 Error Presentation

Errors are surfaced in two ways. Non-fatal conditions, such as a rejected dispatch, appear as a status banner and, where appropriate, a warning dialog. Failures of an asynchronous operation — a save, a restore, a report, or a close — are reported when the operation's future completes, with the underlying cause unwrapped for the operator. In every case the interface preserves the last valid state rather than leaving the display inconsistent with the model.

## 8.12 Screenshots

The screenshots in this chapter were produced by running the application and capturing the real interface. They are evidence of the implemented design rather than illustrations.

[[FIG:assets/screenshots/03_operations.png|Figure 8.6: The Operations tab listing active and completed field missions.]]

[[FIG:assets/screenshots/06_learn.png|Figure 8.7: The Learn tab presenting the in-application architecture notes.]]

%%% CHAPTER 9 %%%

# CHAPTER 9: IMPLEMENTATION

## 9.1 Project Structure

The project follows a conventional Maven layout. Production code lives under `src/main/java` in the six packages described in Chapter 3; tests live under `src/test/java`; helper scripts live under `scripts`; and the build is described by `pom.xml`. The application's working data is created outside the project, in the per-user data folder.

## 9.2 Application Startup

Startup selects the system look and feel, then schedules the real work on the EDT. It resolves the data folder, restores the last session if one exists, constructs the engine and frame, and shows the frame. If the previous session cannot be restored, the operator is asked whether to start fresh, and the saved file is retained until a later clean shutdown.

```java
// app/BasinWatchApp.java (main and openApplication, condensed from line 20)
public static void main(String[] arguments) {
    try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); }
    catch (ReflectiveOperationException | UnsupportedLookAndFeelException ex) { /* fallback */ }
    SwingUtilities.invokeLater(() -> openApplication(arguments.clone()));
}
// ... in openApplication ...
paths = AppPaths.create(AppPaths.resolveDataRoot(arguments));
BasinModel model = new BasinModel();
Path lastSession = paths.saves().resolve("last-session.bws");
if (Files.exists(lastSession)) { /* load and restore, or ask to start fresh */ }
BasinEngine engine = new BasinEngine(paths, model);
MainFrame frame = new MainFrame(engine, paths);
frame.setVisible(true);
```

*Listing 9.1: Startup resolves data paths, restores a session if possible, and shows the frame on the EDT.*

| Step | Action |
|---|---|
| 1 | Select the system look and feel |
| 2 | Schedule `openApplication` on the EDT |
| 3 | Resolve the data root and create data directories |
| 4 | Restore `last-session.bws` if present, or start fresh |
| 5 | Construct the `BasinEngine` (services and workers, not yet started) |
| 6 | Construct and display the `MainFrame` |
| 7 | Operator starts observations or advances a single interval |

*Table 9.1: Application startup sequence.*

## 9.3 Engine Lifecycle

The engine exposes its lifecycle as `CompletableFuture`-returning methods — `start`, `pause`, `save`, `load`, `exportReport`, and `closeAsync` — all of which run on a single daemon control thread. This serialises lifecycle actions so that, for example, a save cannot run concurrently with a restore. Listing 3.1 (Chapter 3) shows the feed startup; Listing 6.5 (Chapter 6) shows shutdown.

## 9.4 Sensor Feed Implementation

The feed's implementation is shown in Listing 6.1. Its design points are that it uses a shared atomic tick counter, that it writes a pulse after each interval's readings, that it flushes the pipe so the reader sees complete lines, and that it sleeps interruptibly between intervals.

## 9.5 Sensor Intake

The intake implementation is shown in Listing 6.2. Its design points are that it reads whole lines, that it distinguishes pulses from readings, that it validates each record and discards malformed ones with a warning, and that it enqueues accepted events into the bounded buffer.

## 9.6 Event Processing

A worker's processing method captures the model state before and after the transition under the model lock, then performs journal writes, archive submission, and database enqueueing outside the lock. The generic processing is shown in Listing 3.2. The engine also computes, from the before-and-after snapshots, exactly which database records should be written — a sensor row when a reading was accepted and escalated or not, a dispatch record for a new mission, and a completion record when a mission's status changes to completed.

## 9.7 Basin Model

The model applies three kinds of event. A reading updates a zone's water level and risk; a pulse advances missions and completes those that finish; a dispatch reserves resources and creates a mission.

```java
// domain/BasinModel.java (applyReading, line 61, condensed)
BasinZone zone = requireZone(reading.zoneId());
RiskLevel previousRisk = zone.snapshot().risk();
if (!zone.apply(reading)) {
    messages.add("Ignored stale station reading from " + reading.stationId());
    return;
}
tick = Math.max(tick, reading.tick());
RiskLevel currentRisk = zone.snapshot().risk();
// record a SENSOR or RISK UPDATE entry and return a message
```

*Listing 9.2: Applying a reading updates the zone and detects a risk escalation.*

```java
// domain/BasinModel.java (applyPulse, line 79, condensed)
if (pulse.tick() <= lastPulseTick) {
    return;
}
lastPulseTick = pulse.tick();
tick = Math.max(tick, pulse.tick());
for (ResponseMission mission : missions.values()) {
    if (!mission.advance()) {
        continue;
    }
    BasinZone zone = requireZone(mission.snapshot().zoneId());
    switch (mission.snapshot().type()) {
        case PUMP_DEPLOYMENT -> zone.pump(mission.snapshot().type().waterEffectMeters());
        case LEVEE_REINFORCEMENT -> zone.reinforceLevee();
        case EVACUATION -> zone.evacuate();
    }
    resources.release(mission.snapshot().type().requirements());
    String message = mission.snapshot().type().label() + " complete · " + zone.name();
    record("MISSION COMPLETE", message);
    messages.add(message);
}
```

*Listing 9.3: A pulse advances each mission, applies its effect on completion, and releases its resources.*

```java
// domain/BasinModel.java (applyDispatch, line 103, condensed)
BasinZone zone = requireZone(request.zoneId());
MissionType type = request.missionType();
pruneMissionHistory();
if (!resources.tryReserve(type.requirements())) {
    String message = "Insufficient available units for " + type.label();
    record("RESOURCE LIMIT", message + " · " + zone.name());
    messages.add(message);
    return;
}
String id = "BW-" + String.format("%04d", missionSequence.incrementAndGet());
ResponseMission mission = new ResponseMission(id, type, zone.id(), tick);
missions.put(id, mission);
String message = id + " dispatched · " + type.label() + " · " + zone.name();
record("UNIT ALLOCATED", message);
messages.add(message);
}
```

*Listing 9.4: A dispatch reserves resources atomically and creates an active mission.*

## 9.8 Resource Allocation

Resource allocation is implemented in `ResourceAllocator` (Listing 6.4). The standard stock is three pumps, three levee crews, two supply trucks, two evacuation vehicles, and four field crews. Release validates that the released quantity cannot exceed what is actually reserved, so a double release is detected rather than silently inflating the inventory.

## 9.9 Mission Processing

A mission advances one tick at a time and completes when its progress reaches its type's duration. The advance method is deliberately small and returns whether the mission just completed.

```java
// domain/ResponseMission.java (advance, line 25)
boolean advance() {
    if (status != MissionStatus.ACTIVE) { return false; }
    progressTicks = Math.min(type.durationTicks(), progressTicks + 1);
    if (progressTicks == type.durationTicks()) {
        status = MissionStatus.COMPLETED;
        return true;
    }
    return false;
}
```

*Listing 9.5: Deterministic mission progression, one tick at a time.*

| Step | Action | Class |
|---|---|---|
| 1 | Operator selects a zone and a mission type | `MainFrame` |
| 2 | Engine enqueues a `DispatchRequest` | `BasinEngine` |
| 3 | Worker reserves all requirements atomically | `ResourceAllocator.tryReserve` |
| 4 | Model creates an ACTIVE mission | `BasinModel.applyDispatch` |
| 5 | Each pulse advances every ACTIVE mission by one tick | `ResponseMission.advance` |
| 6 | On completion, the type's effect is applied to the zone | `BasinZone.pump/reinforceLevee/evacuate` |
| 7 | Requirements are released back to the inventory | `ResourceAllocator.release` |
| 8 | Completion is persisted and the snapshot updated | `DatabaseService`, `BasinEngine` |

*Table 9.2: Mission processing steps.*

## 9.10 Persistence

The persistence implementations are described in Chapter 5. Each mechanism uses the stream family appropriate to its data, and each is wrapped in try-with-resources or closed explicitly during shutdown.

## 9.11 Database

The database implementations are described in Chapter 7. The service runs on a single daemon thread, repositories use prepared statements and transactions, and failures are isolated from the simulation.

## 9.12 Report Writer

The report writer produces a four-section text report (Listing 5.5 shows the structure; the implementation uses a UTF-8 buffered writer and a timestamped filename).

## 9.13 Session Restore

Restoring a session reads the snapshot, validates it, and rebuilds the model with fresh runtime primitives. The restore method re-checks every domain invariant: that there are exactly six zones, that resource counts are within range, that missions are valid, and that the saved stock plus the resources committed to active missions equals the standard capacity.

```java
// domain/BasinModel.java (restore, line 151, condensed)
if (saved == null || saved.tick() < 0 || saved.zones().size() != 6) {
    throw new IllegalArgumentException("Saved basin state is incomplete.");
}
// validate resource counts, zones, and missions ...
for (ResourceType type : ResourceType.values()) {
    if (stock.get(type) + commitments.get(type) != standardCapacity.get(type)) {
        throw new IllegalArgumentException(
                "Saved stock and active reservations do not balance for " + type + ".");
    }
}
```

*Listing 9.6: Restoring a session re-validates the domain invariants, including the resource balance.*

## 9.14 Error Handling

Error handling is applied at every boundary, as described in Section 3.11. The recurring principles are: validate at the boundary; throw the most specific exception; report with context; never present a failure as a success; and preserve the interrupt status when a thread is interrupted.

## 9.15 Important Code Excerpts

The excerpts in this report are drawn verbatim from the project source and are listed with their file and line references so that the reader can locate them. They are representative rather than exhaustive; the complete source is provided with the project and, in part, in Appendix A.
