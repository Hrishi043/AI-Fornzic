# Forensio

The project includes a React review dashboard and a Python API. The existing
Streamlit interface remains available as an alternative.

## Run the React dashboard

Install Python dependencies if needed, then start both the API and React app
from the frontend directory:

```sh
./.forensic/bin/python -m pip install -r requirements.txt
cd frontend
npm install
npm run dev
```

`npm run dev` starts the API on `127.0.0.1:8000` and Vite on
`127.0.0.1:5173`. If an API is already running on port 8000, it reuses it.
Keep this terminal open while using the app; press Ctrl+C to stop the services.

Open the URL printed by Vite (normally `http://127.0.0.1:5173`). Choose the
folder containing `logon.csv`, `device.csv`, `file.csv`, `email.csv`, and
`http.csv`. The browser sends those files to the local API, which stages them
in a temporary folder for analysis and removes that folder when analysis ends.
The analysis runs locally. The API writes
`sprint1_output/dashboard_day_scores.csv` and
`sprint1_output/dashboard_report.csv`, as the Streamlit app does.

The model bundle must be present at
`sprint1_output/insider_investigation_model.joblib`; run notebook Cell 31 to
create it if it is missing. The local API stays bound to `127.0.0.1`.

## Run the Streamlit interface

```sh
./.forensic/bin/streamlit run app.py
```

The React app reviews model-ranked signals; flags are prompts for human review,
not proof of wrongdoing. Scores are relative ranks within the selected data,
not probabilities.
