# Mini-project report

`Project_Report.tex` is the editable LaTeX report for the AI Forensic
Insider Risk Review System. Its front matter, academic tone, typography,
and page furniture follow the supplied Techmaghi internship report;
the chapter sequence follows the supplied mini-project format. The
internship company and internship-work claims are not carried into this
project report.

The report content is based on the project source, the CERT r4.2
synthetic activity data, and saved outputs in `sprint1_output/`. The
dashboard and notebook listings are snapshots of the code at report
preparation time. The four notebook plots are extracted from saved
notebook outputs. `ui_landing.png` is a local capture of the dashboard
before selecting an activity folder; it is not an end-to-end test.

## Compile

The report expects the files in this folder to retain their relative
paths. From this directory, run pdfLaTeX twice so the contents and
automatically generated lists of tables and figures receive page
numbers:

```sh
pdflatex Project_Report.tex
pdflatex Project_Report.tex
```

For Overleaf, upload `Project_Report.tex`, `app_code_listing.txt`,
`notebook_code_listing.txt`, `ui_landing.png`, and the complete
`figures/` folder, preserving these names and paths. Select pdfLaTeX as
the compiler.

To refresh the source listings after project-code changes, run from the
repository root. The first command renders the app's Unicode string
literals as equivalent Python escapes for pdfLaTeX:

```sh
jq -r ' .cells | to_entries[] | select(.value.cell_type == "code") |
  select((.value.source | if type == "array" then join("") else . end) | length > 0) |
  "# Notebook code cell \(.key + 1)\n" +
  ((.value.source | if type == "array" then join("") else . end) + "\n")' \
  notebook/forensic.ipynb > report/notebook_code_listing.txt
{ printf '%s\n' '# LaTeX-safe listing derived from app.py; Unicode string literals use equivalent Python escapes.'; \
  perl -CSDA -pe 's/\x{1F50E}/\\U0001F50E/g; s/\x{00B7}/\\u00B7/g' app.py; \
} > report/app_code_listing.txt
```

The notebook figures and UI screenshot are evidence snapshots. Re-capture
them when the corresponding UI or notebook visualizations change.

## Before submission

The template specifies a **minimum of 60 pages**. This source has been
expanded with verified notebook plots, a local UI capture, and complete
code-cell listings, but the resulting PDF page count has not been
verified because no LaTeX engine is available in the current
environment. Compile the report and check the page count and layout.
If the result is below the department's minimum, add genuine, approved
project evidence (for example, documented test runs or original
screenshots); do not repeat content or invent results to reach the
minimum.

Confirm that Prof. Nisha Markose is the correct mini-project guide and
verify all academic signatories with the department. The student,
register number, college, department, programme, HOD, and academic year
are carried over from the supplied internship report and should also be
confirmed before submission. Review the generated contents, page
numbering, certificate wording, references, image quality, and code
listing page breaks.
