"""Local API for the React interface; run with `uvicorn api:app --reload`."""

from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from threading import Lock

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from forensic_core import MODEL_NAMES, REQUIRED_FILES, friendly_activity_table, load_model_bundle, score_folder


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "sprint1_output" / "insider_investigation_model.joblib"
RESULTS_DIR = PROJECT_DIR / "sprint1_output"

app = FastAPI(title="Insider Risk Review API", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

analysis_lock = Lock()
employee_days: pd.DataFrame | None = None
ranking: pd.DataFrame | None = None


class AnalyzeRequest(BaseModel):
    folder: str


class EmployeeRequest(BaseModel):
    user: str


def _records(frame: pd.DataFrame) -> list[dict]:
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def _analyze_folder(folder: Path) -> dict:
    global employee_days, ranking
    if not MODEL_PATH.is_file():
        raise HTTPException(status_code=503, detail="The four-model bundle is missing. Run notebook Cell 31 first.")
    try:
        with analysis_lock:
            bundle = load_model_bundle(MODEL_PATH)
            days, report = score_folder(folder, bundle)
            RESULTS_DIR.mkdir(exist_ok=True)
            days.to_csv(RESULTS_DIR / "dashboard_day_scores.csv", index=False)
            report.to_csv(RESULTS_DIR / "dashboard_report.csv", index=False)
            employee_days, ranking = days, report
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Analysis could not be completed: {error}") from error

    suspicious = report[report["status"] == "SUSPICIOUS"]
    return {
        "employees": _records(report),
        "summary": {
            "employees": int(len(report)),
            "flagged": int(len(suspicious)),
            "review": int(len(report) - len(suspicious)),
            "activeDays": int(days["day"].nunique()),
        },
        "models": MODEL_NAMES,
    }


@app.get("/api/health")
def health():
    return {
        "ready": MODEL_PATH.is_file(),
        "message": "Model bundle is ready." if MODEL_PATH.is_file() else "Model bundle is missing. Run notebook Cell 31.",
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    folder = Path(request.folder).expanduser()
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail="That folder could not be found on this computer.")
    return _analyze_folder(folder)


@app.post("/api/analyze-upload")
def analyze_upload(files: list[UploadFile] = File(...)):
    expected = set(REQUIRED_FILES)
    selected: dict[str, UploadFile] = {}
    optional = {"employees.csv", "employee.csv", "users.csv", "user.csv"}
    for upload in files:
        name = Path(upload.filename or "").name.lower()
        if name in expected or name in optional:
            if name in selected:
                raise HTTPException(status_code=400, detail=f"The selected folder contains duplicate {name} files.")
            selected[name] = upload
    missing = sorted(expected - selected.keys())
    if missing:
        raise HTTPException(status_code=400, detail="The selected folder is missing: " + ", ".join(missing))

    try:
        with TemporaryDirectory(prefix="insider-risk-") as temporary:
            folder = Path(temporary)
            for name, upload in selected.items():
                with (folder / name).open("wb") as target:
                    copyfileobj(upload.file, target, length=1024 * 1024)
            return _analyze_folder(folder)
    finally:
        for upload in files:
            upload.file.close()


@app.post("/api/employee")
def employee_detail(request: EmployeeRequest):
    if ranking is None or employee_days is None:
        raise HTTPException(status_code=409, detail="Run an analysis before opening employee details.")
    selected = ranking[ranking["user"].astype(str) == request.user]
    if selected.empty:
        raise HTTPException(status_code=404, detail="Employee was not found in this report.")
    report_row = selected.iloc[0]
    days = employee_days[employee_days["user"].astype(str) == request.user]
    activity = friendly_activity_table(days)
    score_names = {
        "isolation_forest_rank": "Isolation Forest",
        "logistic_regression_rank": "Logistic Regression",
        "decision_tree_rank": "Decision Tree",
        "random_forest_rank": "Random Forest",
    }
    scores = [
        {"model": label, "score": round(float(report_row[column]) * 100, 1)}
        for column, label in score_names.items()
        if column in report_row
    ]
    name = report_row.get("name")
    return {
        "user": request.user,
        "name": None if pd.isna(name) else str(name),
        "status": str(report_row["status"]),
        "whyFlagged": str(report_row["why_flagged"]),
        "modelAgreement": int(report_row["model_agreement"]),
        "activeDays": int(report_row["active_days"]),
        "scores": scores,
        "activity": _records(activity),
    }
