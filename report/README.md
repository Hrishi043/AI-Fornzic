# Mini-project report

`Project_Report.tex` is the editable LaTeX report for the AI Forensic
Insider Risk Review System. Its front matter, academic tone, typography,
and page furniture follow the supplied Techmaghi internship report;
the chapter sequence follows the supplied mini-project format. The
internship company and internship-work claims are not carried into this
project report.

The report content is based on the project source, the CERT r4.2
synthetic activity data, and saved outputs in `sprint1_output/`. The
notebook, API, model-core, and alternative Streamlit source snapshots
provide selected excerpts and complete source listings in the appendix.
The four notebook plots are extracted from saved notebook outputs.
`ui_react_landing.png` and `ui_react_model_guide.png`
are saved captures of the React dashboard. The local API reported the
saved model bundle as ready, but no folder analysis was run for these
screenshots.

## Compile

The source follows the supplied MCA mini-project format: A4 paper,
one-inch margins, Times-style type, 12-point body text, 1.5 line spacing,
16/14/12-point heading levels, a project-title header, and the
department/page footer. The title and college certificate pages are
embedded in `Project_Report.tex`. Declaration pages are
unnumbered; small Roman page numbers begin with Acknowledgement and
continue through the lists. Contents pages are unnumbered and the main
report uses Arabic numbering from Introduction.

The supplementary project record is embedded in `Project_Report.tex`.
Keep the source listings and figures beside the report, preserving their
relative paths. From this directory, run pdfLaTeX twice so the contents
and automatically generated lists of tables and figures receive page
numbers:

```sh
pdflatex Project_Report.tex
pdflatex Project_Report.tex
```

For Overleaf, upload `Project_Report.tex`, `api_code_listing.txt`,
`forensic_core_code_listing.txt`, `notebook_code_listing.txt`,
`app_code_listing.txt`,
`logo.png`, `ui_react_landing.png`, `ui_react_model_guide.png`, and the complete
`figures/` folder, preserving these names and paths. Select pdfLaTeX as
the compiler.

Body leading is set to 1.5 spacing; chapter titles are displayed without
chapter numbers and the gap below the running header is reduced. Headers
and footers begin on the Introduction page; chapter-opening pages from
that point use the same page style. Title and certificate pages have no
page furniture. The system and data-flow figures are drawn as diagrams,
including Random Forest and Isolation Forest flow diagrams.
Data tables use visible row and column borders and fitted text widths;
the long requirements and test tables repeat their headings across
pages. Code listings use a smaller fixed-width font to preserve
readability within the appendix.
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

The template specifies a **minimum of 60 pages**. The report has been
expanded with implementation detail, evaluation methodology, privacy
and operational considerations, an expanded feature dictionary and
data-lineage checkpoints, model-scoring concepts, implementation
trade-offs, API contract, deployment risk review, troubleshooting guide,
React interaction states, accessibility notes, glossary, reproducibility
checklist, development roadmap, and full source listings.
The resulting PDF page count has not been verified
because no LaTeX compiler is installed in this environment. Compile the
report and check the page count, code listing breaks, and layout. If it
remains below the department's minimum, add genuine, approved project
evidence (for example, documented test runs or original screenshots);
do not repeat content or invent results to reach the minimum.

Confirm that Dr. Manu John is the mini-project guide and Dr. Sonia
Abraham is the HOD, and verify all academic signatories with the
department. The student, register number, college, department,
programme, and academic year are carried over from the supplied
internship report and should also be confirmed before submission.
Review the generated contents, page
numbering, certificate wording, references, image quality, and code
listing page breaks.
