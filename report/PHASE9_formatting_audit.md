# PHASE 9 — FORMATTING / LAYOUT AUDIT

Deliverable: `report/BasinWatch_Project_Report.docx` (editable Word file) with a
rendered proof at `report/BasinWatch_Project_Report.pdf` (114 pages).

## Toolchain
- python-docx 1.2.0 (DOCX authoring)
- Pillow (image sizing / CU banner preparation)
- LibreOffice 25.2 Writer headless (`LD_LIBRARY_PATH=/usr/lib/libreoffice/program`)
- PyMuPDF (fitz) for page-level raster QA

## Page geometry
- A4 (8.27 x 11.69 in); left 1.1 in, right 0.9 in, top 0.8 in, bottom 0.8 in
- Body: Times New Roman 12 pt, justified, 1.4 line spacing
- Headings: H1 17 pt, H2 14 pt, H3 12.5 pt, maroon; captions 10 pt italic
- Header distance 0.35 in, footer distance 0.4 in

## Chandigarh University header
- Banner image `assets/cu_banner.png` (cropped from the CU assignment PDF,
  aspect preserved at 5.77:1, red rule removed from the raster so it is drawn
  once as a real Word bottom border).
- Applied to every page except the title page
  (`different_first_page_header_footer = True`).
- Single red rule (colour #C01B22) beneath the banner on all body pages.
- Verified: 0 of 113 body pages are missing the header rule; title page has no
  banner.

## Page numbering
- Centred PAGE field in the footer on all pages.
- Verified present on title, body, and final page.

## Table of contents / lists
- Static, page-accurate TOC, List of Figures (28) and List of Tables (27),
  produced by a two-pass build: pass 1 renders placeholder lines so pagination
  matches, the PDF is scanned to locate each heading and caption, then pass 2
  renders the real page numbers.
- All 236 TOC/LOF/LOT entries were located and numbered (no "00" placeholders).

## Figures and tables
- 28 figures embedded at their correct locations (all 28 image files resolve;
  0 "[IMAGE MISSING]").
- Figure image + caption share a single paragraph, so a caption can never be
  orphaned from its figure. Verified: 0 orphan captions.
- Tall diagrams are height-capped (<= 6.9 in) so they do not push captions or
  overflow the text block.
- 30 tables rendered with a shaded, repeating header row and Table Grid borders.

## Automated layout checks (final PDF)
- Blank pages: 0
- Pages with horizontal overflow beyond the text block: 0
- Pages with orphaned captions: 0
- Body pages missing the CU header rule: 0
- TOC/LOF/LOT: pages 10–16; chapter 1 starts page 17

## Content integrity spot-checks
- All four team members and UIDs appear (4 occurrences each).
- Subject code 25CSH-208 present.
- No sample-report names leaked.
- No unresolved markup literals (`[red rule]`, `IMAGE MISSING`) in the rendered
  text.

## Result
PASS. The document is a professionally paginated, editable DOCX with consistent
CU branding, accurate navigation aids, non-orphaned figures/tables, and clean
page layout.
