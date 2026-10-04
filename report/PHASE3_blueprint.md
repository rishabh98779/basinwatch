# BasinWatch Report — PHASE 3 BLUEPRINT (section-by-section spec)

## Global design
- Page: A4; margins L 1.15", R 0.9", T 0.8", B 0.8".
- Font: Times New Roman; body 12 pt justified; line spacing 1.15 (body) / 1.5 (front matter).
- Headings: H1 chapter 16 pt bold caps; H2 14 pt bold; H3 12 pt bold italic.
- Header (all pages except cover): CU banner image (1073x233) full width + red rule +
  running title "BasinWatch | Object Oriented Programming (25CSH-208)" + page no. right.
- Footer: "Chandigarh University" left, page number right.
- Numbering: Figure C.S, Table C.S, Listing C.S (chapter.serial).
- Captions: figure below, table above. Code in Consolas 9.5 pt, shaded.
- Target total: ~95-115 pages.

## FRONT MATTER (~10 pp)
1. Cover / Title Page (1) - CU branding, title, subtitle, degree block, 4 students + UIDs.
2. Bonafide Certificate (1) - placeholders for supervisor/HOD/examiners.
3. Declaration (1) - originality + no-plagiarism statement, 4 signatures.
4. Acknowledgement (1) - placeholders for faculty.
5. Abstract (~450-550 words) + Keywords (1-2).
6. Table of Contents (2).
7. List of Figures (1) - ~19 figures.
8. List of Tables (1) - ~26 tables.
9. List of Abbreviations (1).

## CHAPTER 1 INTRODUCTION (~7 pp)
1.1 Background - floodplain operations context; simulation as a learning/planning tool.
1.2 Problem Statement - concurrent observations vs finite resources; why OOP+concurrency.
1.3 Motivation - educational OOP project; offline, no network.
1.4 Project Overview - BasinWatch = offline floodplain operations console; desktop.
1.5 Objectives - O1..O7 (each tied to a verifiable feature).
1.6 Scope - in-scope / out-of-scope (NOT a forecast or dispatch system).
1.7 Target Users - planning/teaching audience (fictional operator).
1.8 Problem-to-Solution Mapping (Table 1.1).
1.9 Limitations - schematic map, illustrative parameters.
1.10 Organization of the Report.
Fig 1.1 BasinWatch context/boundary diagram. Table 1.1 problem->solution.

## CHAPTER 2 REQUIREMENTS AND SYSTEM ANALYSIS (~7 pp)
2.1 Existing Problem; 2.2 Proposed Solution; 2.3 Functional Requirements FR-1..FR-18;
2.4 Non-Functional Requirements NFR-1..NFR-10; 2.5 Hardware/Software Requirements;
2.6 User Roles; 2.7 Use Cases (Table + Fig use-case); 2.8 Constraints; 2.9 Feasibility
(technical/economic/operational); 2.10 Assumptions.
Tables 2.1 FR, 2.2 NFR, 2.3 HW/SW, 2.4 use cases. Fig 2.1 use-case.

## CHAPTER 3 SYSTEM ARCHITECTURE AND DESIGN (~12 pp)
3.1 Overall Architecture; 3.2 High-Level System Architecture (Fig 3.1); 3.3 Layer/Package
Architecture (Fig 3.2 package diagram); 3.4 Component Responsibilities (Table 3.1);
3.5 Data Flow (Fig 3.3 DFD); 3.6 Runtime Workflow (Fig 3.4 pipeline); 3.7 Class
Relationships (Fig 3.5/3.6 class diagrams); 3.8 Concurrency Architecture (Fig 3.7 thread
map); 3.9 Persistence Architecture (Fig 3.8); 3.10 Database Architecture (Fig 3.9 ER);
3.11 Error Boundaries (Table 3.2); 3.12 Security/Safe Persistence (ObjectInputFilter);
3.13 Design Decisions and Rationale (Table 3.3).
Listings: 3.1 BasinEngine.startFeed; 3.2 BasinEngine.process.

## CHAPTER 4 OBJECT ORIENTED DESIGN (~16 pp) [strongest]
4.1 OOP Principles Used; 4.2 Encapsulation; 4.3 Abstraction; 4.4 Inheritance; 4.5
Polymorphism; 4.6 Composition; 4.7 Association/Aggregation; 4.8 Constructors; 4.9 Access
Modifiers; 4.10 Interfaces (no abstract classes - deliberate exclusion); 4.11 Enums;
4.12 Immutable Objects; 4.13 Event-Based Design; 4.14 Exception Handling; 4.15 OOP
Design Benefits.
Master Table 4.1 OOP/Java concept -> component -> class/file -> purpose -> explanation.
Per-concept record template (Concept, Definition, Where, Class/File, Why, How,
Interaction, excerpt, benefit, syllabus link).
Listings: 4.1 BasinEvent; 4.2 records; 4.3 enums; 4.4 tryReserve; 4.5 ResponseMission ctors.

## CHAPTER 5 JAVA I/O AND PERSISTENCE (~12 pp)
5.1 Java I/O Overview; 5.2 Byte Streams; 5.3 Character Streams; 5.4 Buffered Streams;
5.5 Data Streams; 5.6 Filter/Wrapper Streams; 5.7 Byte-Array Streams; 5.8 File and File
Metadata; 5.9 Serialization; 5.10 Deserialization; 5.11 transient/runtime state; 5.12
Session Snapshot; 5.13 Sensor Archive; 5.14 Operational Journal; 5.15 Report Generation;
5.16 Save/Restore Workflow.
Table 5.1 artefact->stream map; 5.2 stream hierarchy. Fig 5.1 persistence architecture;
5.2 save/restore flow.
Listings: 5.1 SensorArchive; 5.2 SnapshotStore.save; 5.3 SnapshotStore.filter;
5.4 OperationalJournal.append; 5.5 ReportWriter.write.

## CHAPTER 6 MULTITHREADING AND CONCURRENCY (~16 pp) [strongest]
6.1 Need for Concurrency; 6.2 Process vs Thread; 6.3 Thread Lifecycle (Fig 6.1);
6.4 Thread; 6.5 Runnable; 6.6 Sensor Feed; 6.7 Sensor Intake; 6.8 Event Buffer;
6.9 Producer-Consumer (Fig 6.2); 6.10 wait(); 6.11 notifyAll(); 6.12 Synchronization;
6.13 Monitor Locks; 6.14 Resource Reservation; 6.15 Atomic Resource Allocation (Fig 6.3);
6.16 Concurrent Missions; 6.17 Deadlock Risk; 6.18 Deadlock Prevention; 6.19 Thread
Interruption; 6.20 Graceful Shutdown (Fig 6.4 lifecycle); 6.21 Thread Priority /
Experimental Diagnostics; 6.22 Concurrency Safety.
Tables 6.1 concurrent components; 6.2 EventBuffer ops; 6.3 resource catalogue;
6.4 mission requirements.
Listings: 6.1 SensorFeed.run; 6.2 SensorIntake.run; 6.3 EventBuffer.put; 6.4
EventBuffer.take; 6.5 ResourceAllocator.tryReserve; 6.6 ResponseWorker.run;
6.7 closeEngine (condensed).

## CHAPTER 7 DATABASE AND JDBC (~10 pp)
7.1 Need; 7.2 SQLite; 7.3 JDBC Architecture (Fig 7.1); 7.4 Connection; 7.5
PreparedStatement; 7.6 ResultSet; 7.7 SQLException; 7.8 Transactions; 7.9 Database
Schema (Fig 7.2 ER); 7.10 Repository Layer; 7.11 Database Service; 7.12 Asynchronous
Database Operations; 7.13 Database Failure Handling.
Tables 7.1 JDBC term->impl; 7.2 schema; 7.3 repositories.
Listings: 7.1 DatabaseManager.openConnection; 7.2 DatabaseInitializer DDL;
7.3 SensorReadingRepository.findRecent; 7.4 MissionRepository.recordDispatch.

## CHAPTER 8 USER INTERFACE (~9 pp)
8.1 Swing Architecture; 8.2 Event Dispatch Thread; 8.3 Main Operations Console (Fig 8.1);
8.4 Basin Map (Fig 8.2); 8.5 Systems Inspector (Fig 8.4); 8.6 Response Desk;
8.7 Activity Feed; 8.8 Database History (Fig 8.5); 8.9 User Interaction Flow (Fig 8.6
activity); 8.10 UI State Updates; 8.11 Error Presentation; 8.12 Screenshots (Fig 8.7 Learn).
Tables 8.1 components; 8.2 tabs; 8.3 controls.
Listings: 8.1 EDT hand-off; 8.2 paintComponent.

## CHAPTER 9 IMPLEMENTATION (~11 pp)
9.1 Project Structure; 9.2 Application Startup; 9.3 Engine Lifecycle; 9.4 Sensor Feed
Implementation; 9.5 Sensor Intake; 9.6 Event Processing; 9.7 Basin Model; 9.8 Resource
Allocation; 9.9 Mission Processing; 9.10 Persistence; 9.11 Database; 9.12 Report Writer;
9.13 Session Restore; 9.14 Error Handling; 9.15 Important Code Excerpts.
Tables 9.1 startup sequence; 9.2 mission processing; 9.3 project tree.
Listings: 9.1 BasinWatchApp.main; 9.2 applyReading; 9.3 applyPulse; 9.4 applyDispatch;
9.5 ResponseMission.advance; 9.6 BasinModel.restore.

## CHAPTER 10 TESTING AND VALIDATION (~8 pp)
10.1 Testing Strategy; 10.2 Unit/Invariant Tests; 10.3 Concurrency Tests; 10.4 Resource
Contention Tests; 10.5 Buffer Tests; 10.6 Persistence Tests; 10.7 Database Tests; 10.8
Session Round-Trip Tests; 10.9 Failure Tests; 10.10 Shutdown Tests; 10.11 UI Testing;
10.12 Test Case Table; 10.13 Results; 10.14 Observed Limitations.
Table 10.1 test-case table (10 suites -> assertions); 10.2 executed evidence.
Wording rule: "Implemented test coverage includes..." / "76 assertions passed".
Listing 10.1 assertion harness.

## CHAPTER 11 RESULTS AND DISCUSSION (~7 pp)
11.1 Functional Results; 11.2 Runtime Workflow; 11.3 Resource Allocation Results;
11.4 Persistence Results; 11.5 Database Results; 11.6 Concurrency Results; 11.7 OOP
Learning Outcomes; 11.8 Requirement Achievement (Table 11.1); 11.9 Discussion.
Tables 11.1 requirement achievement; 11.2 verified runtime observations.
Fig 11.1 live console; 11.2 operations.

## CHAPTER 12 CONCLUSION AND FUTURE SCOPE (~5 pp)
12.1 Conclusion; 12.2 Achievements; 12.3 Current Limitations; 12.4 Future Improvements;
12.5 Possible Extensions (repo-documented + technically justified).
Table 12.1 future extensions.

## REFERENCES (~1-2 pp)
Real, verifiable official sources only (Oracle Java SE/JDK docs, Java Swing tutorial,
java.io/Serialization specs, java.util.concurrent docs, Maven docs, SQLite docs,
Xerial sqlite-jdbc docs). No fabricated papers/DOIs.

## APPENDICES (~10 pp)
A Important Source Code; B Test Results (76 assertions, suite list); C Database Schema
(real DDL); D Configuration/Build (pom.xml, commands, data dirs); E Additional
Screenshots (real); F Additional Diagrams.

## Figure list (19)
1.1 context; 2.1 use case; 3.1 high-level arch; 3.2 package; 3.3 DFD; 3.4 runtime
workflow; 3.5 domain class; 3.6 engine/UI class; 3.7 thread map; 3.8 persistence;
3.9 ER; 5.1 persistence architecture; 5.2 save/restore flow; 6.1 thread lifecycle;
6.2 producer-consumer; 6.3 resource allocation; 6.4 application lifecycle; 7.1 JDBC
architecture; 7.2 ER (dup of 3.9, keep one); 8.1 console; 8.2 basin map; 8.3 sequence
sensor pipeline; 8.4 inspector; 8.5 database history; 8.6 operator activity; 8.7 learn.
(Consolidate to ~19 unique; avoid duplicates.)

## Table list (~26)
1.1 problem->solution; 2.1 FR; 2.2 NFR; 2.3 HW/SW; 2.4 use cases; 3.1 components;
3.2 error boundaries; 3.3 design decisions; 4.1 OOP master map; 5.1 artefact->stream;
5.2 stream hierarchy; 6.1 concurrent components; 6.2 EventBuffer ops; 6.3 resource
catalogue; 6.4 mission requirements; 7.1 JDBC map; 7.2 schema; 7.3 repositories;
8.1 UI components; 8.2 tabs; 8.3 controls; 9.1 startup sequence; 9.2 mission processing;
10.1 test cases; 11.1 requirement achievement; 12.1 future extensions.

## Code excerpt list (~34 listings)
As enumerated per chapter above; all verbatim from repo with line references.

## Page-flow checks
No orphan headings; each chapter starts on a new page; figures/tables referenced in text
before appearance; captions consistent; no clipped tables (font 10 pt in wide tables);
diagrams inserted at >=200 dpi.
