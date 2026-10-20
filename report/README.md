# Mini-project report

`Project_Report.tex` is the editable LaTeX report for the AI Forensic
Insider Risk Review System. Its front matter, academic tone, typography,
and page furniture follow the supplied Techmaghi internship report;
the chapter sequence follows the supplied mini-project format. The
internship company and internship-work claims are not carried into this
project report.

The report content is based on the project source, the CERT r4.2
synthetic activity data, and saved outputs in `sprint1_output/`. The
notebook, API, and model-core listings are source snapshots prepared for
the report; `app_code_listing.txt` is retained for the alternative
Streamlit interface. The four notebook plots are extracted from saved
notebook outputs. `ui_react_landing.png` and `ui_react_model_guide.png`
are saved captures of the React dashboard. The local API reported the
saved model bundle as ready, but no folder analysis was run for these
screenshots.

## Compile

The source uses A4 paper, one-inch margins, Times-style type, 12-point body
text, 1.3 line spacing, a project-title header, and the department/page
footer requested in the supplied format. The title and college certificate
pages are omitted as requested. The declaration, acknowledgement, abstract,
and lists before the contents use italic Roman page numbers without headers
or footer rules; the contents pages are unnumbered and the main report uses
Arabic numbering with the project header and department/page footer.

The report expects the files in this folder to retain their relative
paths. From this directory, run pdfLaTeX twice so the contents and
automatically generated lists of tables and figures receive page
numbers:

```sh
pdflatex Project_Report.tex
pdflatex Project_Report.tex
```

For Overleaf, upload `Project_Report.tex`, `api_code_listing.txt`,
`forensic_core_code_listing.txt`, `notebook_code_listing.txt`,
`ui_react_landing.png`, `ui_react_model_guide.png`, and the complete
`figures/` folder, preserving these names and paths. Select pdfLaTeX as
the compiler.

Body leading is set to 1.3 spacing, with compact paragraph lists and
float spacing; chapter titles are displayed without chapter numbers and
the gap below the running header is reduced. Headers and footers begin
on the Introduction page; chapter-opening pages from that point use the
same page style. The system and data-flow figures are drawn as diagrams,
including a sequence diagram.
Data tables use
visible row and column borders, single-spaced rows, and fitted text
widths; the long requirements and test tables repeat their headings
across pages. Code listings use a smaller fixed-width font to reduce
appendix page count while preserving the required report content.
Selected excerpts cover feature aggregation, incident labels, employee-
grouped splits, model-score normalization, and dashboard consensus.
The grouped-split excerpt retains both split stages and the index
mapping.

To refresh the source listings after project-code changes, run from the
repository root. These commands refresh the notebook, primary API/model
core, and alternative Streamlit source snapshots. The Streamlit listing
renders its Unicode string literals as equivalent Python escapes for
pdfLaTeX:

```sh
jq -r ' .cells | to_entries[] | select(.value.cell_type == "code") |
  select((.value.source | if type == "array" then join("") else . end) | length > 0) |
  "# Notebook code cell \(.key + 1)\n" +
  ((.value.source | if type == "array" then join("") else . end) + "\n")' \
  notebook/forensic.ipynb > report/notebook_code_listing.txt
cp api.py report/api_code_listing.txt
cp forensic_core.py report/forensic_core_code_listing.txt
{ printf '%s\n' '# LaTeX-safe listing derived from app.py; Unicode string literals use equivalent Python escapes.'; \
  perl -CSDA -pe 's/\x{1F50E}/\\U0001F50E/g; s/\x{00B7}/\\u00B7/g' app.py; \
} > report/app_code_listing.txt
```

The notebook figures and UI screenshots are evidence snapshots.
Re-capture them when the corresponding UI or notebook visualizations
change. The React captures in this report predate the animated analysis
card, live progress bar, remaining-time estimate, and review-queue model
agreement note; these interactions are described in the UI design text
but are not shown in the captured screens.

## Before submission

The template specifies a **minimum of 60 pages**. This source includes
notebook plots, two React UI captures, and selected code excerpts, but
the resulting PDF page count has not been verified. The LaTeX source was
updated to document the current React analysis progress display and its
approximate ETA, and the source-code snapshots were refreshed. Compile
the report and check the page count and layout.
If the result is below the department's minimum, add genuine, approved
project evidence (for example, documented test runs or original
screenshots); do not repeat content or invent results to reach the
minimum.

Confirm that Dr. Manu John is the mini-project guide and Dr. Sonia
Abraham is the HOD, and verify all academic signatories with the
department. The student, register number, college, department,
programme, and academic year are carried over from the supplied
internship report and should also be confirmed before submission.
Review the generated contents, page
numbering, certificate wording, references, image quality, and code
listing page breaks.
