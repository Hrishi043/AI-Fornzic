# Mini Project Report

Editable LaTeX source for the AI Forensic Insider Risk Review System report. The title and certificate pages are omitted. The report begins with Acknowledgement, Abstract, List of Tables, List of Figures, and Contents. Front matter uses centered italic Roman page numbers; numbered chapters from Introduction onward are left aligned and use Arabic page numbers. Guide and HOD names are formatted as Dr.Manu John and Dr.Sonia Abraham.

## Compile

Compile `Mini_Project_Report.tex` twice with pdfLaTeX from this folder to update the table of contents, lists, and citation links. The bibliography appears before the long source-code appendices so citation metadata is written before those listings are processed. Keep the `figures/`, `frontend/src/`, the plain-text React/CSS listings, research paper, and code listing files alongside the source. The report source reuses the literature review, project-specific diagrams, tables, equations, screenshots, and implementation listings from the supplied project materials.

The source has not yet been compiled in this environment because no LaTeX compiler is installed. Therefore, its final rendered page count and page-by-page layout have not been verified. The required count is 60 pages from the first page of Introduction through the last page of References; front matter and the appendix do not count toward this span. The last reference page is labeled `chap:last-reference-page` so its page can be checked in the generated `.aux` file after compilation. Inspect the page-number transitions, figure list, and page density before submission.
