# BasinWatch Report — PHASE 8 ORIGINALITY / PLAGIARISM AUDIT

Method: the sample report PDF text was extracted and compared with the drafts using
normalised n-gram overlap. The sample was used only as a structural reference.

## A. N-gram overlap vs sample report
Sample report words: 3203. Draft words: 21717.
- Shared 7-grams: 0
- Shared 6-grams: 1  -> "in computer science engineering chandigarh university"
- Shared 5-grams: 3  -> the above plus "computer science engineering chandigarh university"
                        and "chapter 1 introduction 1 1"

All overlaps are the institution's official name and a generic chapter heading,
which are unavoidable and not original content. RESULT: no sentence-level or
paragraph-level overlap with the sample. [A]

## B. Sample-content non-reuse
The sample's project (an Arduino hand-gesture system) shares no subject matter with
BasinWatch. None of its project-specific technical content, wording, or unique
explanations appears in the drafts. No sentence-by-sentence paraphrasing was used;
all BasinWatch explanations were written independently from the repository. [A]

## C. Internal repetition (anti-filler)
- Repeated sentences (>=8 words): 0
- Repeated 12-grams: 19, all benign boilerplate:
  * student names/UIDs (cover, certificate, declaration)
  * the formal submission sentence ("...submitted in partial fulfilment of the
    requirements for the subject Object Oriented Programming")
  * Oracle documentation URLs in the References list
  * one deliberate recap sentence ("the model a single owner for state that must
    remain consistent"), used once in Ch.4 and once in Ch.11 as intended cross-linking
No filler paragraphs were detected. [A]

## D. Attribution
External technical material (Java, Swing, JDBC, SQLite, Maven, serialization) is
general platform knowledge and is attributed to official documentation in the
References list. BasinWatch-specific content is original team work. [A]

## Phase 8 verdict: PASS — original, no plagiarism, no filler.
