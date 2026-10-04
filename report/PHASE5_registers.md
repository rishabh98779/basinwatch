# BasinWatch Report — PHASE 5 DIAGRAM, TABLE, LISTING & SCREENSHOT REGISTERS

All diagrams authored as editable PlantUML (.puml) and rendered to PNG at dpi=200.
Sources + PNGs live in report/diagrams/. Regenerate with: python3 make_diagrams.py && plantuml -tpng *.puml

## FIGURE REGISTER (21 figures)
| Figure | Title | File | Placement |
|---|---|---|---|
| 1.1 | BasinWatch System Context and Boundary | fig1_1_context.png | Ch.1 |
| 2.1 | BasinWatch Use-Case Diagram | fig2_1_usecase.png | Ch.2 |
| 3.1 | BasinWatch High-Level System Architecture | fig3_1_highlevel_arch.png | Ch.3 |
| 3.2 | Package Diagram | fig3_2_package.png | Ch.3 |
| 3.3 | Data-Flow Diagram (Level 1) | fig3_3_dfd.png | Ch.3 |
| 3.4 | BasinWatch Runtime Workflow | fig3_4_runtime_workflow.png | Ch.3 |
| 3.5 | Domain Class Diagram | fig3_5_domain_class.png | Ch.3 |
| 3.6 | Engine and UI Class Diagram | fig3_6_engine_ui_class.png | Ch.3 |
| 3.7 | Thread and Concurrency Map | fig3_7_thread_map.png | Ch.3 |
| 3.8 | Persistence Architecture | fig3_8_persistence_arch.png | Ch.3 |
| 3.9 | SQLite Database ER Diagram | fig3_9_er.png | Ch.3 (referenced again in Ch.7) |
| 4.1 | OOP Concept Mapping to BasinWatch Components | fig4_1_oop_mapping.png | Ch.4 |
| 5.1 | Persistence Architecture (stream detail) | reuse fig3_8 (or fig5_1) | Ch.5 |
| 5.2 | Session Save and Restore Flow | fig5_2_save_restore.png | Ch.5 |
| 6.1 | Java Thread Lifecycle as Used by BasinWatch | fig6_1_thread_lifecycle.png | Ch.6 |
| 6.2 | Bounded Producer-Consumer Event Buffer | fig6_2_producer_consumer.png | Ch.6 |
| 6.3 | Atomic Resource Reservation | fig6_3_resource_allocation.png | Ch.6 |
| 6.4 | Application Lifecycle | fig6_4_app_lifecycle.png | Ch.6 |
| 7.1 | JDBC Architecture | fig7_1_jdbc_arch.png | Ch.7 |
| 8.3 | Sequence Diagram - Sensor / Event Pipeline | fig8_3_sequence_sensor.png | Ch.8 |
| 8.4 | Sequence Diagram - Resource Dispatch | fig8_4_sequence_dispatch.png | Ch.8 |
| 8.6 | Activity Diagram - Operator Workflow | fig8_6_operator_activity.png | Ch.8 |
Figures 8.1, 8.2, 8.5, 8.7 are screenshots (below). Total figure count 21 diagrams + 7 screenshots = 28 figures.

## SCREENSHOT REGISTER (real captures, 1440x900)
| Figure | Title | File | Placement |
|---|---|---|---|
| 8.1 | Main BasinWatch console at startup | assets/screenshots/00_startup.png | Ch.8 |
| 8.2 | Live console with active missions | assets/screenshots/01_console_live.png | Ch.8 |
| 8.5 | Database history view | assets/screenshots/05_database.png | Ch.8 |
| 8.7 | Learn (architecture cards) view | assets/screenshots/06_learn.png | Ch.8 |
| 11.1 | Basin map and operations timeline | assets/screenshots/02_basin_map.png | Ch.11 |
| 11.2 | Operations tab (field missions) | assets/screenshots/03_operations.png | Ch.11 |
| 6.5 | Systems inspector (background activity) | assets/screenshots/04_insights.png | Ch.6 |

## TABLE REGISTER (26 tables)
1.1 Problem-to-Solution Mapping
2.1 Functional Requirements (FR-1..FR-18)
2.2 Non-Functional Requirements (NFR-1..NFR-10)
2.3 Hardware and Software Requirements
2.4 Use Cases
3.1 Component Responsibilities
3.2 Error Boundaries
3.3 Design Decisions and Rationale
4.1 Master OOP/Java Concept Mapping (the flagship table)
5.1 Persistence Artefacts and Stream APIs
5.2 Java I/O Stream Hierarchy in BasinWatch
6.1 Concurrent Components and Responsibilities
6.2 EventBuffer Operations and Conditions
6.3 Response Resource Catalogue
6.4 Mission Types, Requirements and Effects
7.1 JDBC Term to BasinWatch Implementation
7.2 SQLite Database Schema
7.3 Repository Responsibilities
8.1 Swing UI Components
8.2 Console Tabs and Purpose
8.3 Operator Controls
9.1 Application Startup Sequence
9.2 Mission Processing Steps
10.1 Test-Case Table (10 suites)
10.2 Executed Evidence Summary
11.1 Requirement Achievement
11.2 Verified Runtime Observations
12.1 Future Extensions
Total 26 tables.

## LISTING REGISTER (~34 code excerpts, verbatim, line-referenced)
3.1 BasinEngine.startFeed (BasinEngine.java:279)
3.2 BasinEngine.process (441)
4.1 BasinEvent interface (BasinEvent.java)
4.2 Records with validation (SensorReading compact ctor)
4.3 Enum with fields (MissionType)
4.4 ResourceAllocator.tryReserve (36)
4.5 ResponseMission overloaded constructors (11/15)
5.1 SensorArchive header + append (19/40)
5.2 SnapshotStore.save (23)
5.3 SnapshotStore.filter (100)
5.4 OperationalJournal.append (22)
5.5 ReportWriter.write (26)
6.1 SensorFeed.run (33)
6.2 SensorIntake.run (26)
6.3 EventBuffer.put (23)
6.4 EventBuffer.take (55)
6.5 ResourceAllocator.tryReserve (36)
6.6 ResponseWorker.run (597)
6.7 BasinEngine.closeEngine (340, condensed)
7.1 DatabaseManager.openConnection (24)
7.2 DatabaseInitializer DDL (10-50)
7.3 SensorReadingRepository.findRecent (45)
7.4 MissionRepository.recordDispatch (31)
8.1 EDT hand-off (MainFrame:112)
8.2 BasinMapPanel.paintComponent (59)
9.1 BasinWatchApp.main (20)
9.2 BasinModel.applyReading (61)
9.3 BasinModel.applyPulse (79)
9.4 BasinModel.applyDispatch (103)
9.5 ResponseMission.advance (25)
9.6 BasinModel.restore (151)
10.1 Assertion harness (InvariantSuite check/expect/await)
Total ~34 listings.

## Screenshot availability note
All 7 screenshots are REAL captures produced by running the application under a virtual
display (Xvfb) with a Robot-based harness. No fabricated screenshots. No placeholders needed.

## Diagram quality note
Every diagram is derived from verified repository classes/relationships; none is decorative.
Editable sources retained for future correction.
