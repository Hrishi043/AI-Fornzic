# Forensio

The project includes a React review dashboard and a Python API. The existing
Streamlit interface remains available as an alternative.

## Run the React dashboard

Open two terminals from the project root. Install Python dependencies if
needed, then start the API:

```sh
./.forensic/bin/python -m pip install -r requirements.txt
./.forensic/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

```sh
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally `http://127.0.0.1:5173`). Choose the
folder containing `logon.csv`, `device.csv`, `file.csv`, `email.csv`, and
`http.csv`. The browser sends those files to the local API, which stages them
in a temporary folder for analysis and removes that folder when analysis ends.
The analysis runs locally. The API writes
`sprint1_output/dashboard_day_scores.csv` and
`sprint1_output/dashboard_report.csv`, as the Streamlit app does.

The model bundle must be present at
`sprint1_output/insider_investigation_model.joblib`; run notebook Cell 31 to
create it if it is missing. Keep the API bound to `127.0.0.1` when using this
path-based local data workflow.

## Run the Streamlit interface

```sh
./.forensic/bin/streamlit run app.py
```

The React app reviews model-ranked signals; flags are prompts for human review,
not proof of wrongdoing. Scores are relative ranks within the selected data,
not probabilities.
