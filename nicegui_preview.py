"""Single-page NiceGUI dashboard for the insider activity project.

Copy this file into the Ai-Forensic project root beside the r4.2 folder and
sprint1_output folder, then run it with the project's Python environment.
"""

from pathlib import Path

import joblib
import pandas as pd
from nicegui import run, ui


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "sprint1_output" / "insider_investigation_model.joblib"
REQUIRED_FILES = ["logon.csv", "device.csv", "file.csv", "email.csv", "http.csv"]
CHUNK_SIZE = 25_000

state = {"employee_days": None, "ranking": None, "model_bundle": None}

ui.page_title("Insider Risk Review")
ui.colors(primary="#087e8b", secondary="#1d3557", accent="#32b8a6")
ui.add_head_html("""
<style>
body { background: #f3f6fb; color: #182438; }
.q-header { background: #142238 !important; }
.q-card { border: 1px solid #dce5ef; border-radius: 14px; }
.risk-card { box-shadow: 0 4px 18px rgba(20, 34, 56, .07); }
</style>
""")


def load_model_bundle():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}. Run the model-save cell first."
        )
    return joblib.load(MODEL_PATH)


def process_activity_file(file_path: Path) -> pd.DataFrame:
    """Read a source log in chunks and count activity by employee and day."""
    source = file_path.stem.lower()
    headers = [name.strip().lower() for name in pd.read_csv(file_path, nrows=0).columns]
    useful = ["date", "user", "activity", "attachments"]
    columns_to_read = [name for name in useful if name in headers]

    if "date" not in columns_to_read or "user" not in columns_to_read:
        raise ValueError(f"{file_path.name} must have date and user columns.")

    daily = pd.DataFrame()

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
        grouped = grouped.rename(
            columns={name: f"{source}_{name}" for name in feature_columns}
        )
        daily = grouped if daily.empty else daily.add(grouped, fill_value=0)

    return daily


def analyze_dataset(folder: str, model_bundle: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    data_dir = Path(folder).expanduser()
    missing = [name for name in REQUIRED_FILES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Folder is missing: " + ", ".join(missing))

    parts = [process_activity_file(data_dir / name) for name in REQUIRED_FILES]
    employee_days = pd.concat(parts, axis=1).fillna(0)
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

    ranking = employee_days.groupby("user").agg(
        risk_score=("risk_score", "max"),
        active_days=("day", "nunique"),
    )

    for target, source in [
        ("after_hours", "logon_after_hours_count"),
        ("usb_connects", "device_device_connect_count"),
    ]:
        if source in employee_days:
            ranking[target] = employee_days.groupby("user")[source].sum()
        else:
            ranking[target] = 0

    ranking = ranking.sort_values("risk_score", ascending=False).reset_index()
    return employee_days, ranking


def render_report(employee_select, report_area, selected_user=None):
    report_area.clear()
    employee_days = state["employee_days"]
    ranking = state["ranking"]
    if employee_days is None or ranking is None or ranking.empty:
        with report_area:
            ui.label("Run an analysis to see the report.").classes("text-slate-500")
        return

    users = ranking["user"].tolist()
    if selected_user not in users:
        selected_user = users[0]

    with report_area:
        ui.label("Top employees").classes("text-xl font-bold text-slate-800 mt-2")
        top = ranking.head(10).copy()
        top.insert(0, "rank", range(1, len(top) + 1))
        top = top.rename(columns={
            "rank": "Rank",
            "user": "Employee",
            "risk_score": "Risk",
            "active_days": "Days",
            "after_hours": "After-hours",
            "usb_connects": "USB connects",
        })
        top["Risk"] = top["Risk"].round(3)
        ui.table(
            columns=[
                {"name": "Rank", "label": "Rank", "field": "Rank", "align": "left"},
                {"name": "Employee", "label": "Employee", "field": "Employee", "align": "left"},
                {"name": "Risk", "label": "Risk", "field": "Risk", "align": "right"},
                {"name": "Days", "label": "Days", "field": "Days", "align": "right"},
                {"name": "After-hours", "label": "After-hours", "field": "After-hours", "align": "right"},
                {"name": "USB connects", "label": "USB", "field": "USB connects", "align": "right"},
            ],
            rows=top.to_dict("records"),
            row_key="Employee",
        ).classes("w-full risk-card")

        employee_select.options = users
        employee_select.value = selected_user
        ui.separator().classes("my-5")
        ui.label(f"Activity: {selected_user}").classes("text-xl font-bold text-slate-800")

        user_days = employee_days[employee_days["user"] == selected_user].copy()
        user_days = user_days.sort_values("risk_score", ascending=False)
        top_day = user_days.iloc[0]

        with ui.row().classes("w-full gap-4"):
            for label, value in [
                ("Risk", f"{float(top_day['risk_score']):.3f}"),
                ("Active days", f"{user_days['day'].nunique():,}"),
                ("After-hours logins", f"{int(user_days.get('logon_after_hours_count', pd.Series(0, index=user_days.index)).sum()):,}"),
                ("USB connects", f"{int(user_days.get('device_device_connect_count', pd.Series(0, index=user_days.index)).sum()):,}"),
            ]:
                with ui.card().classes("grow risk-card"):
                    ui.label(label).classes("text-xs uppercase tracking-wide text-slate-500")
                    ui.label(value).classes("text-2xl font-bold text-teal-700")

        friendly_names = {
            "day": "Date",
            "risk_score": "Risk",
            "logon_event_count": "Logins",
            "logon_after_hours_count": "After-hours logins",
            "device_device_connect_count": "USB",
            "file_event_count": "Files",
            "email_event_count": "Emails",
            "http_event_count": "Web visits",
        }
        wanted = [
            "day", "risk_score", "logon_event_count", "logon_after_hours_count",
            "device_device_connect_count", "file_event_count",
            "email_event_count", "http_event_count",
        ]
        detail = user_days[[name for name in wanted if name in user_days.columns]].head(15)
        detail = detail.rename(columns=friendly_names)
        detail["Risk"] = detail["Risk"].round(3)
        ui.label("Highest-risk days").classes("text-lg font-semibold text-slate-700 mt-3")
        ui.table.from_pandas(detail).classes("w-full risk-card")
        ui.label("Scores are leads for review, not proof of wrongdoing.").classes(
            "text-sm text-slate-500 mt-2"
        )


with ui.header().classes("items-center justify-between px-6 py-3"):
    with ui.row().classes("items-center gap-3"):
        ui.icon("shield", color="teal-3").classes("text-2xl")
        ui.label("INSIDER RISK REVIEW").classes("text-lg font-bold tracking-wide")
    model_name = "Model not loaded"
    try:
        state["model_bundle"] = load_model_bundle()
        model_name = state["model_bundle"]["model_name"]
    except Exception as error:
        ui.notify(str(error), type="negative")
    ui.label(f"Model: {model_name}").classes("text-sm opacity-80")

with ui.column().classes("w-full max-w-7xl mx-auto p-6 gap-4"):
    ui.label("Investigation dashboard").classes("text-3xl font-bold text-slate-900")
    ui.label("Review activity patterns and prioritize cases.").classes("text-slate-500")

    with ui.card().classes("w-full risk-card p-4"):
        ui.label("Analyze data").classes("text-lg font-semibold text-slate-800")
        folder_input = ui.input(
            "Data folder",
            value=str(PROJECT_DIR / "r4.2"),
            placeholder="Path to the folder with five CSV files",
        ).classes("w-full")
        status_label = ui.label("Ready").classes("text-sm text-slate-500")

        async def analyze():
            if state["model_bundle"] is None:
                ui.notify("Model file not found. Save the model from the notebook first.", type="negative")
                return
            status_label.text = "Reading the activity files. This may take a while…"
            analyze_button.disable()
            try:
                employee_days, ranking = await run.io_bound(
                    analyze_dataset,
                    folder_input.value,
                    state["model_bundle"],
                )
                state["employee_days"] = employee_days
                state["ranking"] = ranking

                results_dir = PROJECT_DIR / "sprint1_output"
                results_dir.mkdir(exist_ok=True)
                employee_days.to_csv(results_dir / "dashboard_employee_day_scores.csv", index=False)
                ranking.to_csv(results_dir / "dashboard_employee_ranking.csv", index=False)
                status_label.text = f"Done — ranked {len(ranking):,} employees."
                render_report(employee_select, report_area)
                ui.notify("Analysis complete.", type="positive")
            except Exception as error:
                status_label.text = "Could not analyze this folder."
                ui.notify(str(error), type="negative", timeout=10000)
            finally:
                analyze_button.enable()

        analyze_button = ui.button("Analyze", on_click=analyze, icon="play_arrow").props(
            "unelevated color=primary"
        )

    employee_select = ui.select(
        options=[],
        label="Employee",
        on_change=lambda event: render_report(
            employee_select, report_area, event.value
        ),
    ).classes("w-64")
    report_area = ui.column().classes("w-full gap-3")
    with report_area:
        ui.label("Run Analyze to see employee rankings and activity details.").classes(
            "text-slate-500"
        )

ui.run(title="Insider Risk Review", port=8080, reload=False)
