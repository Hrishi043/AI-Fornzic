# Mini Project Report

Editable LaTeX source for the AI Forensic Insider Risk Review System report. The title and certificate pages are omitted. The report begins with Acknowledgement, Abstract, List of Tables, List of Figures, and Contents. Front matter uses centered italic Roman page numbers; numbered chapters from Introduction onward are left aligned and use Arabic page numbers. Guide and HOD names are formatted as Dr.Manu John and Dr.Sonia Abraham.

## Compile in Overleaf

1. Upload `Mini_Project_Report.tex`, `report_part1.tex` through `report_part4.tex`, the images, and the code-listing files to Overleaf. The provided ZIP contains all required files in one folder.
2. Set `Mini_Project_Report.tex` as the main document and select **pdfLaTeX** in Menu → Settings.
3. If you previously had a failed or timed-out build, use **Recompile from scratch** (or **Clear cached files** in the Logs panel), then click **Recompile**. This removes stale `.aux` and `.toc` files that can produce many cascading errors after an interrupted run.
4. Recompile once more so the contents and figure/table lists update.

The four `report_part*.tex` files contain the report body; keep them in the project root beside `Mini_Project_Report.tex`. The report also uses the image files and seven `*_code_listing.txt` files in the ZIP. The `research_papers/` and `frontend/` folders are not needed to compile it.

## Compile locally

From this folder, run `pdflatex Mini_Project_Report.tex` twice. If the source file is in a folder with a space in its name, quote the folder path when changing directories, for example `cd "Mini Project"`.

The source has not yet been compiled in this environment because no LaTeX compiler is installed. Therefore, its final rendered page count and page-by-page layout have not been verified. The required count is 60 pages from the first page of Introduction through the last page of References; front matter and the appendix do not count toward this span. The last reference page is labeled `chap:last-reference-page` so its page can be checked in the generated `.aux` file after compilation. Inspect the page-number transitions, figure list, and page density before submission.
