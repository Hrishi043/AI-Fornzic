"""Shared processing and four-model scoring for the insider review dashboard."""

from pathlib import Path
import subprocess

import joblib
import numpy as np
import pandas as pd


REQUIRED_FILES = ["logon.csv", "device.csv", "file.csv", "email.csv", "http.csv"]
MODEL_NAMES = [
    "Isolation Forest",
    "Logistic Regression",
    "Decision Tree",
    "Random Forest",
]
CHUNK_SIZE = 25_000


def choose_data_folder():
    """Show a macOS folder picker. Data stays in the selected local folder."""
    script = (
        'POSIX path of (choose folder with prompt '
        '"Choose the folder containing the five activity CSV files")'
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    selected = result.stdout.strip()
    return Path(selected) if selected else None


def load_model_bundle(model_path):
    """Load and check the bundle created by notebook Cell 31."""
    bundle = joblib.load(model_path)
    if not isinstance(bundle, dict) or "models" not in bundle:
        raise ValueError(
            "This model file does not contain all four models. "
            "Run notebook Cell 31, then restart the dashboard."
        )
    missing_models = [name for name in MODEL_NAMES if name not in bundle["models"]]
    if missing_models:
        raise ValueError("Model file is missing: " + ", ".join(missing_models))
    if not bundle.get("feature_columns"):
        raise ValueError("The model file is missing its feature column list.")
    return bundle


def process_activity_file(file_path):
    """Aggregate one source log into the same employee-day features as the notebook."""
    file_path = Path(file_path)
    source = file_path.stem.lower()
    headers = [str(c).strip().lower() for c in pd.read_csv(file_path, nrows=0).columns]
    useful = ["date", "user", "activity", "attachments"]
    selected = [column for column in useful if column in headers]

    if "date" not in selected or "user" not in selected:
        raise ValueError(f"{file_path.name} must contain 'date' and 'user' columns.")

    daily = None
    for chunk in pd.read_csv(
        file_path,
        usecols=lambda c: str(c).strip().lower() in selected,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        chunk.columns = [str(c).strip().lower() for c in chunk.columns]
        chunk["user"] = chunk["user"].astype("string").str.strip()
        dates = pd.to_datetime(chunk["date"], errors="coerce", format="mixed")
        missing_user = chunk["user"].isna() | chunk["user"].eq("")
        keep = ~(missing_user | dates.isna() | chunk.duplicated())
        chunk = chunk.loc[keep].copy()
        dates = dates.loc[keep]
        if chunk.empty:
            continue

        chunk["day"] = dates.dt.strftime("%Y-%m-%d").to_numpy()
        hour = dates.dt.hour
        chunk["after_hours_count"] = ((hour < 6) | (hour >= 18)).astype("int8").to_numpy()
        chunk["event_count"] = 1
        columns = ["event_count", "after_hours_count"]

        if source == "device" and "activity" in chunk:
            chunk["device_connect_count"] = (
                chunk["activity"].astype("string").str.lower().eq("connect").astype("int8")
            )
            columns.append("device_connect_count")

        if source == "email" and "attachments" in chunk:
            chunk["attachment_count"] = (
                pd.to_numeric(chunk["attachments"], errors="coerce").fillna(0)
            )
            columns.append("attachment_count")

        part = chunk.groupby(["user", "day"])[columns].sum()
        part = part.rename(columns={c: f"{source}_{c}" for c in columns})
        daily = part if daily is None else daily.add(part, fill_value=0)

    if daily is None:
        return pd.DataFrame()
    return daily


def _load_optional_names(data_folder):
    """Read names only when a small, separate employee lookup file is present."""
    candidates = ["employees.csv", "employee.csv", "users.csv", "user.csv"]
    for filename in candidates:
        path = Path(data_folder) / filename
        if not path.is_file():
            continue
        lookup = pd.read_csv(path, low_memory=False)
        normalized = {str(c).strip().lower(): c for c in lookup.columns}
        user_col = next(
            (normalized[c] for c in ("user", "employee", "employee_id", "user_id") if c in normalized),
            None,
        )
        name_col = next(
            (normalized[c] for c in ("name", "employee_name", "full_name") if c in normalized),
            None,
        )
        if user_col and name_col:
            result = lookup[[user_col, name_col]].copy()
            result.columns = ["user", "name"]
            result["user"] = result["user"].astype("string").str.strip()
            result["name"] = result["name"].astype("string").str.strip()
            return result.dropna(subset=["user"]).drop_duplicates("user")
    return None


def _score(model, model_name, values):
    """Return larger values for higher risk or more unusual activity."""
    if model_name == "Isolation Forest":
        return -np.asarray(model.decision_function(values), dtype=float)
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(values)[:, 1], dtype=float)
    return np.asarray(model.decision_function(values), dtype=float)


def score_folder(data_folder, bundle):
    """Build employee-day features, score with all four models, and rank employees."""
    data_folder = Path(data_folder)
    missing = [name for name in REQUIRED_FILES if not (data_folder / name).is_file()]
    if missing:
        raise FileNotFoundError("Selected folder is missing: " + ", ".join(missing))

    sources = [process_activity_file(data_folder / name) for name in REQUIRED_FILES]
    sources = [frame for frame in sources if not frame.empty]
    if not sources:
        raise ValueError("The selected activity files contained no usable records.")

    employee_days = pd.concat(sources, axis=1).fillna(0)
    employee_days = employee_days.groupby(level=["user", "day"]).sum().reset_index()

    feature_columns = bundle["feature_columns"]
    for column in feature_columns:
        if column not in employee_days.columns:
            employee_days[column] = 0
    model_input = employee_days[feature_columns].apply(pd.to_numeric, errors="coerce").fillna(0)

    score_columns = []
    for name in MODEL_NAMES:
        scores = _score(bundle["models"][name], name, model_input)
        # Percentiles put the four different score scales on a comparable rank scale.
        column = name.lower().replace(" ", "_") + "_rank"
        employee_days[column] = pd.Series(scores).rank(pct=True, method="average").to_numpy()
        score_columns.append(column)

    employee_days["consensus_score"] = employee_days[score_columns].mean(axis=1)

    # Rank each employee by their highest-risk day for each model.
    aggregations = {
        "consensus_score": ("consensus_score", "max"),
        "active_days": ("day", "nunique"),
    }
    aggregations.update({column: (column, "max") for column in score_columns})
    ranking = employee_days.groupby("user").agg(**aggregations).reset_index()

    # This is a review-priority rule, not a probability or proof of wrongdoing.
    for column in score_columns:
        ranking[column + "_top_10"] = ranking[column].rank(pct=True, method="average") >= 0.90
    agreement_columns = [column + "_top_10" for column in score_columns]
    ranking["model_agreement"] = ranking[agreement_columns].sum(axis=1).astype(int)
    queue_size = max(1, int(np.ceil(len(ranking) * 0.05)))
    consensus_cutoff = ranking["consensus_score"].nlargest(queue_size).min()
    ranking["status"] = np.where(
        (ranking["consensus_score"] >= consensus_cutoff)
        | (ranking["model_agreement"] >= 2),
        "SUSPICIOUS",
        "REVIEW",
    )

    # Summarize activity signals on each employee's highest-consensus day.
    signals = [
        ("After-hours activity", "logon_after_hours_count"),
        ("USB connections", "device_device_connect_count"),
        ("File activity", "file_event_count"),
        ("Email activity", "email_event_count"),
        ("Web activity", "http_event_count"),
    ]
    reasons = {}
    for user, group in employee_days.groupby("user", sort=False):
        row = group.loc[group["consensus_score"].idxmax()]
        unusual = []
        for label, column in signals:
            if column not in employee_days.columns:
                continue
            value = float(row[column])
            cutoff = float(employee_days[column].quantile(0.95))
            if value > 0 and cutoff > 0 and value >= cutoff:
                unusual.append(f"{label} ({value:g} events on {row['day']})")
        reasons[user] = "; ".join(unusual[:3]) or (
            f"Activity ranked highly across the four models on {row['day']}"
        )

    ranking["why_flagged"] = ranking["user"].map(reasons)
    names = _load_optional_names(data_folder)
    if names is not None:
        ranking = ranking.merge(names, on="user", how="left")
        ranking["name"] = ranking["name"].replace("", pd.NA)
    else:
        ranking["name"] = pd.NA

    ranking["_status_order"] = ranking["status"].map({"SUSPICIOUS": 0, "REVIEW": 1})
    ranking = ranking.sort_values(
        ["_status_order", "consensus_score"], ascending=[True, False]
    ).drop(columns="_status_order").reset_index(drop=True)

    employee_days = employee_days.merge(
        ranking[["user", "name", "status"]], on="user", how="left"
    )
    return employee_days, ranking


def friendly_activity_table(user_days):
    labels = {
        "day": "Date",
        "consensus_score": "Combined rank",
        "logon_event_count": "Logins",
        "logon_after_hours_count": "After-hours",
        "device_device_connect_count": "USB connects",
        "file_event_count": "Files",
        "email_event_count": "Emails",
        "http_event_count": "Web visits",
    }
    columns = [column for column in labels if column in user_days.columns]
    return (
        user_days[columns]
        .sort_values("consensus_score", ascending=False)
        .head(20)
        .rename(columns=labels)
    )

# Streamlit dashboard
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "sprint1_output" / "four_model_bundle.joblib"
RESULTS_DIR = PROJECT_DIR / "sprint1_output"

st.set_page_config(page_title="Insider Risk Review", page_icon="🔎", layout="wide")
st.markdown("""
<style>
.stApp { background: #f3f6fb; color: #172338; }
[data-testid="stSidebar"] { background: #142238; }
[data-testid="stSidebar"] * { color: #eff6ff !important; }
.block-container { max-width: 1380px; padding-top: 1.8rem; }
h1, h2, h3 { color: #15243a; letter-spacing: -.02em; }
[data-testid="stMetric"] { background: white; border: 1px solid #dce5ef;
  border-radius: 14px; padding: 1rem; box-shadow: 0 3px 12px #1720330c; }
[data-testid="stMetricValue"] { color: #087e8b; }
.stButton > button[kind="primary"] { background: #087e8b; border: 0;
  border-radius: 9px; font-weight: 650; }
[data-testid="stDataFrame"] { border: 1px solid #dce5ef; border-radius: 10px; }
.report-card { background: white; border: 1px solid #dce5ef;
  border-left: 5px solid #d97706; border-radius: 12px; padding: 1rem 1.2rem;
  margin: .65rem 0; }
.report-status { color: #b45309; font-weight: 750; letter-spacing: .04em; }
</style>
""", unsafe_allow_html=True)

st.title("Insider Risk Review")
st.caption("Four-model results prioritize investigation. A flag is not proof of wrongdoing.")
st.sidebar.markdown("### 🔎 Risk Review")
st.sidebar.caption("Decision Tree · Random Forest · Logistic Regression · Isolation Forest")

if not MODEL_PATH.is_file():
    st.error("The four-model file is missing. Run notebook Cell 31, then restart this app.")
    st.stop()

try:
    bundle = load_model_bundle(MODEL_PATH)
except Exception as error:
    st.error(str(error))
    st.stop()

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

st.subheader("Choose activity folder")
st.write("Choose the folder containing logon.csv, device.csv, file.csv, email.csv, and http.csv.")

if st.button("Choose folder", type="primary"):
    folder = choose_data_folder()
    if folder:
        st.session_state.data_folder = str(folder)
    else:
        st.info("No folder selected.")

folder_text = st.session_state.get("data_folder")
if folder_text:
    folder = Path(folder_text)
    st.success(f"Selected folder: {folder.name}")
    if st.button("Analyze folder", type="primary"):
        try:
            with st.spinner("Reading activity logs and scoring records with all four models..."):
                days, report = score_folder(folder, bundle)
            st.session_state.employee_days = days
            st.session_state.ranking = report
            st.session_state.analysis_done = True
            RESULTS_DIR.mkdir(exist_ok=True)
            days.to_csv(RESULTS_DIR / "daily_dashboard_scores.csv", index=False)
            report.to_csv(RESULTS_DIR / "investigation_report.csv", index=False)
            st.success("Analysis complete. The report files were saved in sprint1_output.")
        except Exception as error:
            st.error(f"Analysis could not be completed: {error}")

if st.session_state.analysis_done:
    ranking = st.session_state.ranking
    employee_days = st.session_state.employee_days
    flagged = ranking[ranking["status"] == "SUSPICIOUS"].copy()

    st.divider()
    st.header("Investigation Report")
    st.caption(
        "The combined score is a relative rank, not a probability. SUSPICIOUS "
        "means prioritized for human review based on the four-model review rule."
    )

    top_ten = flagged.head(10)
    if top_ten.empty:
        st.info("No employee crossed the review rule for this dataset.")
    else:
        st.markdown("### Top 10 employees flagged for review")
        for _, row in top_ten.iterrows():
            name_line = (
                f"<p><b>Name:</b> {row['name']}</p>"
                if "name" in row and row["name"] is not None and str(row["name"]).strip()
                and str(row["name"]).lower() != "<na>"
                else ""
            )
            st.markdown(
                f"""
                <div class="report-card">
                  <div class="report-status">Status: SUSPICIOUS</div>
                  <p><b>Employee:</b> {row['user']}</p>
                  {name_line}
                  <p><b>Flagged for:</b> {row['why_flagged']}</p>
                  <p><b>Model agreement:</b> {int(row['model_agreement'])} / 4</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Other employees")
    top_ten_ids = set(top_ten["user"].tolist())
    table = ranking[~ranking["user"].isin(top_ten_ids)].head(25).copy()
    table["Combined rank"] = (table["consensus_score"] * 100).round(1)
    table["Model agreement"] = table["model_agreement"].astype(str) + " / 4"
    table = table.rename(columns={
        "user": "Employee",
        "name": "Name",
        "status": "Status",
        "why_flagged": "Flagged for",
        "active_days": "Active days",
    })
    shown = [
        column for column in
        ["Status", "Employee", "Name", "Combined rank", "Model agreement", "Active days", "Flagged for"]
        if column in table.columns
    ]
    if table.empty:
        st.caption("There are no additional employees to list.")
    else:
        st.dataframe(table[shown], hide_index=True, use_container_width=True)

    selected = st.selectbox("Review employee activity", ranking["user"].tolist())
    selected_days = employee_days[employee_days["user"] == selected].copy()
    selected_report = ranking.loc[ranking["user"] == selected].iloc[0]
    st.subheader(f"Activity details: {selected}")
    st.write(f"**Status:** {selected_report['status']}")
    st.write(f"**Flagged for:** {selected_report['why_flagged']}")
    if selected_report["name"] is not None and str(selected_report["name"]).strip() not in ("", "<NA>"):
        st.write(f"**Name:** {selected_report['name']}")

    model_columns = [
        "isolation_forest_rank",
        "logistic_regression_rank",
        "decision_tree_rank",
        "random_forest_rank",
    ]
    model_scores = selected_report[model_columns].rename({
        "isolation_forest_rank": "Isolation Forest",
        "logistic_regression_rank": "Logistic Regression",
        "decision_tree_rank": "Decision Tree",
        "random_forest_rank": "Random Forest",
    }).to_frame("Rank score")
    model_scores["Rank score"] = (model_scores["Rank score"] * 100).round(1)
    st.markdown("**Scores from each model**")
    st.dataframe(model_scores, use_container_width=True)

    st.markdown("**Highest-ranked activity days**")
    st.dataframe(
        friendly_activity_table(selected_days),
        hide_index=True,
        use_container_width=True,
    )

st.caption(
    "Model scores are relative ranks within the selected data. Confirm findings "
    "against original logs and other evidence before drawing conclusions."
)
