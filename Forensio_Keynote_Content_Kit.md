# Forensio — Keynote presentation content kit

**Project:** AI Forensic Insider Risk Review System  
**Suggested format:** 16:9 widescreen, 10 slides, 7–9 minutes  
**Presenter details:** Add your name, course, guide, and presentation date to the cover.

## Visual direction

- Use a deep navy background with white text, cyan for data flow, and amber for items needing review.
- Keep diagrams and charts native/editable in Keynote. Use screenshots only when showing the interface.
- Use the generated cover artwork as a full-bleed background with a dark translucent panel behind the title.
- Avoid photos of employees or imagery that implies guilt. This project ranks records for review; it does not identify wrongdoers.

## Slide 1 — Forensio

**Subtitle:** AI Forensic Insider Risk Review System  
**Footer:** Mini Project · Department of Computer Applications · Mar Athanasius College of Engineering  
**Presenter line:** [Your name] · [Guide] · [Date]

**Visual:** Generated cover image, full bleed. Keep the title in the open left area.

**Speaker notes:**  
“Forensio is a local-first prototype that brings several kinds of activity records into one review workflow. It uses machine-learning scores to help an analyst decide what to inspect first. The project focuses on organising evidence and preserving human judgment, rather than automating conclusions.”

## Slide 2 — Why review is difficult

**Title:** Activity is spread across systems

- Logon, device, file, email, and web records are stored separately.
- Analysts must connect events across sources and days.
- Potentially relevant cases are rare, so a useful review process must manage a large volume of routine activity.

**Visual:** Five labeled source icons or simple shapes flowing into one timeline. Use a native Keynote diagram.

**Speaker notes:**  
“A single event rarely tells the whole story. The practical challenge is to put activity from separate systems into a consistent view, then make the review workload manageable. Forensio demonstrates that workflow using five activity sources.”

## Slide 3 — Project objective

**Title:** Turn raw logs into a review queue

**Main flow:**  
Five CSV logs → daily activity features → model scores → ranked queue → analyst review

- Score at the employee-day level.
- Show aggregated activity details beside the ranking.
- Keep the analyst responsible for interpreting and acting on a signal.

**Visual:** A five-step horizontal pipeline; use cyan for data processing and amber for the human review step.

**Speaker notes:**  
“The prototype accepts a local folder containing the five supported CSV files. It groups events by user and calendar day, applies a saved model bundle, and presents ranked results with supporting activity summaries. The result is a lead for review, not a finding.”

## Slide 4 — Data and feature preparation

**Title:** Five activity sources become daily features

- **Inputs:** logon, removable device, file, email, and HTTP activity.
- **Unit of analysis:** one employee-day.
- **Dataset:** CERT r4.2 synthetic activity; 330,452 employee-days across 1,000 synthetic users.
- **Labels:** 1,364 employee-days overlap a listed incident interval under the project’s labeling rule.

**Visual:** Five source cards feeding an employee-day feature card. Add a small “synthetic benchmark” label.

**Speaker notes:**  
“The model-development work uses the CERT r4.2 synthetic insider-threat dataset. The project aggregates event counts into employee-day rows. The positive label is created from overlap with a listed incident interval, so it is a benchmark proxy and not a confirmed real-world outcome.”

## Slide 5 — System architecture

**Title:** A local pipeline connects the dashboard to the models

- **React dashboard:** folder selection, progress, queue, search, and activity details.
- **FastAPI service:** validates uploads, reports progress, and returns analysis results.
- **Forensic core:** parses logs in chunks, builds features, scores records, and creates reports.
- **Model bundle:** four fitted models plus the ordered feature list.

**Visual:** Editable architecture diagram: Browser → FastAPI → Forensic core → model bundle; local CSVs feed the core. Use a return arrow from the API to the browser.

**Speaker notes:**  
“The React client communicates with a local FastAPI service. The service passes the accepted files to the scoring core, which aggregates the data and applies the saved feature contract. The app also retains a Streamlit interface as an alternative demonstration path.”

## Slide 6 — Model comparison

**Title:** Random Forest ranked best in this saved test

Create a horizontal bar chart for **test Average Precision**:

| Model | Test Average Precision |
|---|---:|
| Random Forest | 0.158 |
| Decision Tree | 0.104 |
| Logistic Regression | 0.027 |
| Isolation Forest | 0.027 |

**Callout:** One grouped holdout; users are kept separate across train, validation, and test partitions.

**Speaker notes:**  
“The notebook compares Logistic Regression, Decision Tree, Random Forest, and Isolation Forest. In the saved grouped test partition, Random Forest has the highest listed Average Precision. This is one split on synthetic data, so it should be presented as a result of this experiment rather than a general performance guarantee.”

## Slide 7 — What the one-percent queue found

**Title:** A small queue found 95 of 289 labeled days

- Test set: **66,118** employee-days, including **289** positive labels.
- One-percent queue: **662** employee-days.
- **95** labeled positives in the queue; **567** queued rows did not match the positive label.
- Precision: **0.144** · Recall: **0.329** · F1: **0.200**.

**Visual:** A large “662 reviewed” tile beside a 2-part bar: 95 positive labels / 567 other labels. Below, show 194 positive labels outside the queue. Label all counts as test-set, synthetic benchmark results.

**Speaker notes:**  
“At the selected one-percent capacity, the queue contains 662 employee-days. Of those, 95 overlap the benchmark incident windows; 194 of the 289 positive labels remain outside the queue. The queue reduces the set to inspect, but it includes many records without a positive benchmark label and misses many positive labels. The labels are not ground truth about misconduct.”

## Slide 8 — Analyst experience

**Title:** Review the ranking with activity context

- Select a local dataset folder and run the analysis.
- Search or filter the ranked employee queue.
- Open an employee to inspect daily activity aggregates.
- Export the analysis report for follow-up.

**Visual assets from the repository:**

- Landing / folder-selection view: `Mini Project/ui_react_landing.png`
- Flagged employee summary: `Mini Project/ui_flagged_employee.png`
- Employee activity details: `Mini Project/ui_employee_activity.png`
- Model score view: `Mini Project/ui_model_scores.png`

Use one large screenshot per slide or crop two related views. Keep a clear caption: **“Prototype interface; ranks are relative to the selected dataset.”**

**Speaker notes:**  
“The dashboard gives the reviewer a queue, filters, and activity detail in one workflow. The scores are relative ranks within the selected batch. A high rank is neither a probability nor evidence of wrongdoing.”

## Slide 9 — Limits and responsible use

**Title:** A model rank is a lead for human review

- The benchmark is synthetic; labels are incident-window proxies.
- Queue membership depends on the selected dataset and review capacity.
- Current features do not account for job roles, schedules, or context.
- The saved test result does not establish performance in a real organisation.
- Any real-world use would need appropriate validation, privacy and security controls, governance, and human oversight.

**Visual:** Three-column boundary graphic: **Signal** → **Context check** → **Human decision**. Place “No automated employment action” as a small governance principle only if the project’s presentation rubric permits policy language.

**Speaker notes:**  
“The project is a research and demonstration prototype. Synthetic data cannot establish performance on real workplace data. Event patterns can have legitimate explanations, and the current features do not model those contexts. Any operational use would require local validation and formal safeguards, with a human reviewer able to reject a model lead.”

## Slide 10 — Conclusion and next steps

**Title:** Forensio demonstrates a review workflow

- Combines five activity sources into employee-day features.
- Compares four model families using user-grouped evaluation.
- Connects a local scoring service to a review dashboard.
- Next: test temporal and cross-release generalisation; add data-quality reporting; version model bundles; evaluate the employee-level queue rule; define governance before any pilot.

**Closing line:** **The score prioritises attention; the analyst makes the judgment.**

**Speaker notes:**  
“Forensio shows how data preparation, model evaluation, a local API, and an analyst dashboard can fit together. The main contribution is a bounded, review-oriented workflow. The next step is stronger evaluation and governance, not treating a higher rank as a conclusion.”

## Image prompts

The cover artwork was generated for this project. For additional original illustrations, use these prompts with the same navy, cyan, and amber palette. Keep the illustrations text-free so Keynote labels remain editable.

1. **Data pipeline illustration:** “16:9 landscape editorial technology illustration for an academic presentation, five distinct streams of abstract event data converging into daily timeline cards and a review queue, dark navy background, thin cyan lines, restrained amber highlights, clean vector-meets-3D style, generous negative space, no text, no logos, no people, no hacker clichés.”
2. **Architecture illustration:** “Clean isometric software architecture illustration on a pale neutral background: browser dashboard, local API service, data-processing engine, model bundle, and five CSV inputs connected with clear arrows; restrained navy/cyan/amber palette; simple geometric forms; no words, no logos, no people; designed to sit beside editable Keynote labels.”
3. **Human review illustration:** “Minimal editorial illustration showing a magnified activity timeline being reviewed by a neutral analyst silhouette at a desk, focus on careful evidence review and uncertainty, no identifiable person, no surveillance camera, no alarm imagery, navy and soft cyan with a small amber highlight, no text, no logos, wide 16:9 composition.”

## Keynote assembly checklist

1. Create a **Widescreen (16:9)** presentation and choose a restrained dark technology theme.
2. Add the cover artwork to Slide 1. Import the four repository UI screenshots on Slide 8; crop to the relevant panels.
3. Build slides 3, 5, 6, and 7 with editable Keynote shapes, arrows, and chart objects.
4. Put the speaker notes under each slide and keep the visible copy concise.
5. Add the source note on the model-results slides: **Source: project report, CERT r4.2 saved grouped test partition.**
6. Replace presenter placeholders and confirm your institution’s required title-slide wording.

## Source basis

Project facts and saved metrics are drawn from `Mini Project/report_part1.tex`, `Mini Project/report_part2.tex`, and `Mini Project/report_part3.tex`; interface references are the screenshots listed above. The primary report states that scores are relative ranks and that the system is a research and demonstration prototype.
