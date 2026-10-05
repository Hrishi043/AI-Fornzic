from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "sprint1_output" / "insider_investigation_model.joblib"
REQUIRED_FILES = ["logon.csv", "device.csv", "file.csv", "email.csv", "http.csv"]
CHUNK_SIZE = 25_000

st.set_page_config(
    page_title="Insider Risk Review",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f7fb; color: #172033; }
    [data-testid="stSidebar"] { background: #142238; }
    [data-testid="stSidebar"] * { color: #eef4ff !important; }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 0.45rem; }
    [data-testid="stSidebar"] label { border-radius: 9px; padding: 0.35rem 0.55rem; }
    .block-container { max-width: 1380px; padding-top: 2rem; }
    h1 { color: #15243a; letter-spacing: -0.03em; }
    h2, h3 { color: #203650; }
    [data-testid="stMetric"] {
        background: white; border: 1px solid #dce5ef; border-radius: 14px;
        padding: 1rem 1.1rem; box-shadow: 0 3px 12px rgba(23, 32, 51, .05);
    }
    [data-testid="stMetricLabel"] { color: #62748a; font-size: .82rem; }
    [data-testid="stMetricValue"] { color: #176b87; font-size: 1.55rem; }
    .stButton > button[kind="primary"] {
        background: #087e8b; border: 0; border-radius: 9px; font-weight: 650;
    }
    .stButton > button[kind="primary"]:hover { background: #066875; }
    [data-testid="stDataFrame"] { border: 1px solid #dce5ef; border-radius: 10px; }
    .note { color: #63758b; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_model_bundle(model_path):
    return joblib.load(model_path)


def process_activity_file(file_path):
    """Read one activity log in chunks and create daily employee features."""
    source = file_path.stem.lower()
    headers = [name.strip().lower() for name in pd.read_csv(file_path, nrows=0).columns]
    useful_columns = ["date", "user", "activity", "attachments"]
    columns_to_read = [name for name in useful_columns if name in headers]

    if "date" not in columns_to_read or "user" not in columns_to_read:
        raise ValueError(f"{file_path.name} needs date and user columns.")

    daily_features = pd.DataFrame()

    for chunk in pd.read_csv(
        file_path,
        usecols=lambda name: name.strip().lower() in columns_to_read,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        chunk.columns = [name.strip().lower() for name in chunk.columns]
        chunk["user"] = chunk["user"].astype("string").str.strip()
        dates = pd.to_datetime(chunk["date"], errors="coerce", format="mixed")

        missing_user = chunk["user"].isna() | chunk["user"].eq("")
        keep = ~(missing_user | dates.isna() | chunk.duplicated())
        chunk = chunk.loc[keep].copy()
        dates = dates.loc[keep]
        if chunk.empty:
            continue

        chunk["day"] = dates.dt.strftime("%Y-%m-%d").to_numpy()
        hours = dates.dt.hour
        chunk["after_hours_count"] = ((hours < 6) | (hours >= 18)).astype("int8").to_numpy()
        chunk["event_count"] = 1
        feature_columns = ["event_count", "after_hours_count"]

        if source == "device" and "activity" in chunk.columns:
            chunk["device_connect_count"] = (
                chunk["activity"].astype("string").str.lower() == "connect"
            ).astype("int8")
            feature_columns.append("device_connect_count")

        if source == "email" and "attachments" in chunk.columns:
            chunk["attachment_count"] = (
                pd.to_numeric(chunk["attachments"], errors="coerce").fillna(0)
            )
            feature_columns.append("attachment_count")

        grouped = chunk.groupby(["user", "day"])[feature_columns].sum()
        grouped = grouped.rename(columns={name: f"{source}_{name}" for name in feature_columns})
        daily_features = grouped if daily_features.empty else daily_features.add(grouped, fill_value=0)

    return daily_features


def analyze_dataset(data_folder, model_bundle):
    data_folder = Path(data_folder)
    missing = [name for name in REQUIRED_FILES if not (data_folder / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing files: " + ", ".join(missing))

    tables = []
    progress = st.progress(0)
    status = st.empty()
    for number, filename in enumerate(REQUIRED_FILES, start=1):
        status.write(f"Reading {filename}…")
        tables.append(process_activity_file(data_folder / filename))
        progress.progress(number / len(REQUIRED_FILES))

    employee_days = pd.concat(tables, axis=1).fillna(0)
    employee_days = employee_days.groupby(level=["user", "day"]).sum().reset_index()

    feature_columns = model_bundle["feature_columns"]
    for name in feature_columns:
        if name not in employee_days.columns:
            employee_days[name] = 0
    model_input = employee_days[feature_columns].fillna(0)
    model = model_bundle["model"]

    if hasattr(model, "predict_proba"):
        employee_days["risk_score"] = model.predict_proba(model_input)[:, 1]
    else:
        employee_days["risk_score"] = -model.decision_function(model_input)

    def total(column):
        return employee_days[column] if column in employee_days.columns else 0

    ranking = employee_days.groupby("user").agg(
        risk_score=("risk_score", "max"),
        active_days=("day", "nunique"),
    )
    ranking["after_hours"] = employee_days.assign(
        _value=total("logon_after_hours_count")
    ).groupby("user")["_value"].sum()
    ranking["usb_connects"] = employee_days.assign(
        _value=total("device_device_connect_count")
    ).groupby("user")["_value"].sum()
    ranking = ranking.sort_values("risk_score", ascending=False).reset_index()
    return employee_days, ranking


if not MODEL_PATH.is_file():
    st.error("Saved model not found. Run the model-save cell in the notebook first.")
    st.stop()

model_bundle = load_model_bundle(str(MODEL_PATH))
st.sidebar.markdown("### 🔎 Risk Review")
st.sidebar.caption(f"Model: {model_bundle['model_name']}")
page = st.sidebar.radio("Page", ["Upload", "Report"], label_visibility="collapsed")

if "employee_days" not in st.session_state:
    st.session_state["employee_days"] = None
    st.session_state["employee_ranking"] = None

st.title("Insider Risk Review")
st.markdown(
    '<p class="note">Risk scores help prioritize review. They are not proof of wrongdoing.</p>',
    unsafe_allow_html=True,
)

if page == "Upload":
    st.header("Upload data")
    st.write("Choose the folder that contains all five activity CSV files.")
    data_folder = st.text_input(
        "Data folder",
        value=str(PROJECT_DIR / "r4.2"),
        label_visibility="collapsed",
        placeholder="Path to the r4.2 folder",
    )
    st.caption("Files are read from your computer in small chunks.")

    if st.button("Analyze", type="primary"):
        try:
            with st.spinner("Reading and analyzing the activity files. This may take a while…"):
                employee_days, ranking = analyze_dataset(data_folder, model_bundle)
            st.session_state["employee_days"] = employee_days
            st.session_state["employee_ranking"] = ranking

            results_folder = PROJECT_DIR / "sprint1_output"
            results_folder.mkdir(exist_ok=True)
            employee_days.to_csv(results_folder / "dashboard_employee_day_scores.csv", index=False)
            ranking.to_csv(results_folder / "dashboard_employee_ranking.csv", index=False)
            st.success("Done. Open Report to review the results.")
        except Exception as error:
            st.error(f"Could not analyze this folder: {error}")

if page == "Report":
    ranking = st.session_state.get("employee_ranking")
    employee_days = st.session_state.get("employee_days")

    if ranking is None or employee_days is None:
        st.info("Run Analyze first, then come back to Report.")
    else:
        st.header("Report")
        st.caption(f"Model: {model_bundle['model_name']}")

        top = ranking.head(15).copy()
        top.insert(0, "Rank", range(1, len(top) + 1))
        top = top.rename(columns={
            "user": "Employee",
            "risk_score": "Risk score",
            "active_days": "Active days",
            "after_hours": "After-hours logins",
            "usb_connects": "USB connects",
        })
        top["Risk score"] = top["Risk score"].round(3)

        st.subheader("Top employees")
        st.dataframe(
            top,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Risk score": st.column_config.NumberColumn(format="%.3f"),
                "Rank": st.column_config.NumberColumn(width="small"),
            },
        )

        selected_user = st.selectbox(
            "Employee",
            ranking["user"].tolist(),
            label_visibility="collapsed",
        )
        user_days = employee_days[employee_days["user"] == selected_user].copy()
        user_days = user_days.sort_values("risk_score", ascending=False)

        max_score = float(user_days["risk_score"].max())
        active_days = int(user_days["day"].nunique())
        after_hours = int(user_days.get("logon_after_hours_count", pd.Series(0, index=user_days.index)).sum())
        usb = int(user_days.get("device_device_connect_count", pd.Series(0, index=user_days.index)).sum())

        st.subheader(f"Activity: {selected_user}")
        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Risk score", f"{max_score:.3f}")
        metric2.metric("Active days", f"{active_days:,}")
        metric3.metric("After-hours logins", f"{after_hours:,}")
        metric4.metric("USB connects", f"{usb:,}")

        friendly_names = {
            "day": "Date",
            "logon_event_count": "Logins",
            "logon_after_hours_count": "After-hours logins",
            "device_event_count": "Device events",
            "device_device_connect_count": "USB connects",
            "file_event_count": "Files",
            "email_event_count": "Emails",
            "email_attachment_count": "Attachments",
            "http_event_count": "Web visits",
            "risk_score": "Risk score",
        }
        detail_columns = [
            name for name in [
                "day", "risk_score", "logon_event_count",
                "logon_after_hours_count", "device_device_connect_count",
                "file_event_count", "email_event_count", "http_event_count",
            ]
            if name in user_days.columns
        ]
        details = user_days[detail_columns].head(20).rename(columns=friendly_names)
        details["Risk score"] = details["Risk score"].round(3)
        st.dataframe(details, hide_index=True, use_container_width=True)
        st.caption("Review the original logs before drawing conclusions.")
