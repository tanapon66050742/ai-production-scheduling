import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

BASE = Path(__file__).resolve().parents[1]


# ============================================================
# LOAD MODULES
# ============================================================

def load_module(filename, name):
    spec = importlib.util.spec_from_file_location(
        name,
        BASE / filename
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


forecast_mod = load_module(
    "04_forecast.py",
    "forecast_mod_dashboard"
)

genai_mod = load_module(
    "05_genai_report.py",
    "genai_mod_dashboard"
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7f8fc;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
    }

    .hero {
        background: linear-gradient(135deg, #111827, #334155);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 25px;
    }

    .hero h1 {
        margin: 0;
        font-size: 32px;
    }

    .hero p {
        color: #cbd5e1;
        margin-bottom: 0;
    }

    .card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
    }

    .label {
        color: #64748b;
        font-size: 13px;
        font-weight: 600;
    }

    .value {
        color: #111827;
        font-size: 30px;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def get_data():

    orders = pd.read_csv(
        BASE / "cleaned_production_data.csv"
    )

    schedule = pd.read_csv(
        BASE / "final_production_schedule.csv"
    )

    history = forecast_mod.create_history()

    forecast = forecast_mod.forecast_demand(
        history
    )

    return orders, schedule, history, forecast


orders, schedule, history, forecast = get_data()

summary = genai_mod.build_summary(schedule)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🏭 AI Production Control Center</h1>
        <p>
            Intelligent production planning powered by
            Forecasting, Risk Analysis, Rule-based Scheduling and GenAI.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPI
# ============================================================

st.subheader("Production Overview")

c1, c2, c3, c4 = st.columns(4)

kpis = [
    ("Total Orders", summary["total_orders"]),
    ("High Risk Orders", summary["high_risk_orders"]),
    ("Late Orders", summary["late_orders"]),
    ("Makespan", f'{summary["makespan_hours"]:g} h'),
]

for col, (label, value) in zip(
    [c1, c2, c3, c4],
    kpis
):
    with col:
        st.markdown(
            f"""
            <div class="card">
                <div class="label">{label}</div>
                <div class="value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# MACHINE WORKLOAD & RISK
# ============================================================

st.divider()

st.subheader("⚙️ Machine Workload & Risk")

workload = (
    schedule
    .groupby("assigned_machine")["process_time_hours"]
    .sum()
    .sort_values(ascending=False)
)

# MVP assumption:
# 8 production hours/day × 30 days = 240 hours
hours_per_day = st.number_input(
    "Production hours per day",
    min_value=1,
    max_value=24,
    value=8
)

production_days = st.number_input(
    "Planning period (days)",
    min_value=1,
    max_value=365,
    value=30
)

machine_capacity = (
    hours_per_day * production_days
)

machine_risk = workload.reset_index()

machine_risk.columns = [
    "Machine",
    "Workload Hours"
]

machine_risk["Utilization (%)"] = (
    machine_risk["Workload Hours"]
    / machine_capacity
    * 100
).round(1)


def get_machine_risk(utilization):

    if utilization >= 90:
        return "🔴 High Risk"

    elif utilization >= 75:
        return "🟡 Medium Risk"

    return "🟢 Low Risk"


machine_risk["Risk Level"] = (
    machine_risk["Utilization (%)"]
    .apply(get_machine_risk)
)


col1, col2 = st.columns([2, 1])


with col1:

    fig, ax = plt.subplots(
        figsize=(8, 4)
    )

    workload.plot(
        kind="bar",
        ax=ax
    )

    ax.axhline(
        machine_capacity,
        linestyle="--",
        label=f"Capacity ({machine_capacity} h)"
    )

    ax.set_ylabel(
        "Production Hours"
    )

    ax.set_xlabel("")

    ax.legend()

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.xticks(rotation=0)
    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


with col2:

    st.markdown(
        f"**Planning Capacity:** {machine_capacity} hours"
    )

    st.dataframe(
        machine_risk,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# MACHINE RISK SUMMARY
# ============================================================

high_machine_risk = machine_risk[
    machine_risk["Risk Level"] == "🔴 High Risk"
]

medium_machine_risk = machine_risk[
    machine_risk["Risk Level"] == "🟡 Medium Risk"
]


if len(high_machine_risk) > 0:

    st.error(
        f"⚠️ {len(high_machine_risk)} machine(s) "
        "have high workload risk and should be monitored."
    )

elif len(medium_machine_risk) > 0:

    st.warning(
        f"⚠️ {len(medium_machine_risk)} machine(s) "
        "have medium workload risk."
    )

else:

    st.success(
        "✅ All machines are within the normal workload range."
    )


# ============================================================
# DEMAND FORECAST
# ============================================================

st.divider()

st.subheader("📈 Demand Forecast")

selected = st.selectbox(
    "Product",
    sorted(
        history["product_type"].unique()
    )
)

h = history[
    history["product_type"] == selected
]

f = forecast[
    forecast["product_type"] == selected
]

fig, ax = plt.subplots(
    figsize=(12, 4)
)

ax.plot(
    h["date"],
    h["demand"],
    label="Actual"
)

ax.plot(
    f["date"],
    f["forecast_demand"],
    marker="o",
    label="Forecast"
)

ax.set_ylabel("Demand")
ax.legend()

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.xticks(rotation=30)
plt.tight_layout()

st.pyplot(fig)

plt.close(fig)


# ============================================================
# AI DAILY REPORT
# ============================================================

st.divider()

st.subheader("🤖 AI Daily Production Report")

if st.button(
    "✨ Generate AI Report",
    use_container_width=True
):

    with st.spinner(
        "AI is analyzing production data..."
    ):

        report = (
            genai_mod.generate_with_openrouter(
                summary
            )
            or genai_mod.template_report(
                summary
            )
        )

        st.session_state["report"] = report


report = st.session_state.get(
    "report",
    genai_mod.template_report(summary)
)

st.text_area(
    "AI Report",
    report,
    height=280
)


# ============================================================
# RISK & LATE ORDERS
# ============================================================

st.divider()

st.subheader("🚨 Risk & Late Orders")

risk = schedule[
    (schedule["is_high_risk"] == 1)
    | (schedule["is_late"] == 1)
].copy()

risk = risk.sort_values(
    [
        "is_late",
        "is_high_risk",
        "due_days"
    ],
    ascending=[
        False,
        False,
        True
    ]
)

columns = [
    "order_id",
    "product_type",
    "assigned_machine",
    "process_time_hours",
    "due_days",
    "priority",
    "is_high_risk",
    "is_late",
]

if len(risk) > 0:

    st.dataframe(
        risk[columns],
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No high-risk or late orders detected."
    )


# ============================================================
# PRODUCTION SCHEDULE
# ============================================================

st.divider()

st.subheader("🗓️ Production Schedule")

st.dataframe(
    schedule[
        [
            "order_id",
            "product_type",
            "assigned_machine",
            "start_hour",
            "end_hour",
            "process_time_hours",
            "due_days",
            "priority",
            "is_high_risk",
            "is_late",
        ]
    ],
    use_container_width=True,
    hide_index=True
)