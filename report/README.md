# Mini-project report

`AI_Forensic_Insider_Risk_Review_Report.tex` is the new editable LaTeX
report for the AI Forensic Insider Risk Review System. It follows the
supplied MCA mini-project chapter sequence and formatting requirements:
A4 paper, one-inch margins, Times-style text, 12-point body text,
1.5-line spacing, left-aligned sentence-case chapter headings, bordered
tables, a project-title header, and department/page footer.

The title and certificate pages are unnumbered. Small Roman page numbers
start with Acknowledgement and continue through the lists of tables and
figures. The contents pages have no displayed page numbers. Arabic
numbering restarts at 1 on Introduction. The appendix ends at the label
`app:end-content`; count from the page labelled `chap:introduction` to
that page to check the 60-page minimum. The attached PDF was reviewed,
but the updated source has not been recompiled because a LaTeX compiler
is not installed in the current environment.

## Compile

From the `report` directory, run pdfLaTeX twice so the table of
contents, generated lists, and citations receive their final values:

```sh
pdflatex AI_Forensic_Insider_Risk_Review_Report.tex
pdflatex AI_Forensic_Insider_Risk_Review_Report.tex
```

For Overleaf, upload the latest
`AI_Forensic_Insider_Risk_Review_Report.tex`, set it as the Main
document, and select pdfLaTeX. If the project currently compiles
`mai2.tex` or another older copy, replace that file's contents with the
latest source or change the Main document setting.

Keep the `figures/` folder and upload these files beside the main
document:

- `logo.png`, `ui_react_landing.png`, and `ui_react_model_guide.png`
- `api_code_listing.txt`, `app_code_listing.txt`,
  `forensic_core_code_listing.txt`, and `notebook_code_listing.txt`
- `App.jsx`, `styles.css`, and `premium.css`

The React source listings may instead be kept in `frontend/src/`; the
source checks both locations. Compile twice to refresh citations,
contents, and generated lists.

The report uses the saved CERT r4.2 cleaning and model-evaluation
artifacts, current project code, and React dashboard screenshots. The
notebook, scoring core, API, Streamlit interface, React application,
and style files are included as appendices. The literature review
discusses the supplied papers on unintentional insiders, Isolation
Forest-based detection, and digital-forensics-based attack detection;
their full citations and DOIs are in the References chapter. Test cases are identified
as a verification plan unless an execution result is explicitly stated;
they should not be presented as tests that passed.

## Before submission

Confirm the guide, HOD, student name, register number, college,
department, programme, academic year, certificate wording, and
signatories with the department. Compile the document and verify that
the content from Introduction through the end of the appendix meets the
60-page minimum, and inspect the page-number transitions, contents,
figure and table lists, source-listing breaks, image quality, and
references. If the compiled appendix page is fewer than 60 pages after
Introduction, add genuine approved project evidence or deeper
project-specific analysis; do not repeat content or invent results.
