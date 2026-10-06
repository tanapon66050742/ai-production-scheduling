from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

BASE = Path(__file__).resolve().parents[1]


st.title("📈 Data Analysis")

st.caption(
    "Explore production orders, workload, risk patterns and machine capacity."
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    orders = pd.read_csv(
        BASE / "cleaned_production_data.csv"
    )

    schedule = pd.read_csv(
        BASE / "final_production_schedule.csv"
    )

    return orders, schedule


orders, schedule = load_data()


# ============================================================
# FILTER
# ============================================================

st.subheader("🔎 Data Filters")

col1, col2, col3 = st.columns(3)


with col1:

    products = st.multiselect(
        "Product Type",
        sorted(
            orders["product_type"].unique()
        ),
        default=sorted(
            orders["product_type"].unique()
        )
    )


with col2:

    priorities = st.multiselect(
        "Priority",
        sorted(
            orders["priority"].unique()
        ),
        default=sorted(
            orders["priority"].unique()
        )
    )


with col3:

    risk_filter = st.selectbox(
        "Risk",
        [
            "All",
            "High Risk",
            "Normal"
        ]
    )


filtered = orders[
    orders["product_type"].isin(products)
    & orders["priority"].isin(priorities)
].copy()


if risk_filter == "High Risk":

    filtered = filtered[
        filtered["is_high_risk"] == 1
    ]


elif risk_filter == "Normal":

    filtered = filtered[
        filtered["is_high_risk"] == 0
    ]


# ============================================================
# KPI
# ============================================================

st.subheader("📊 Overview")

c1, c2, c3, c4 = st.columns(4)


c1.metric(
    "Orders",
    len(filtered)
)


c2.metric(
    "Avg Quantity",
    f'{filtered["quantity"].mean():.1f}'
)


c3.metric(
    "Avg Process Time",
    f'{filtered["process_time_hours"].mean():.1f} h'
)


c4.metric(
    "High Risk",
    int(
        filtered["is_high_risk"].sum()
    )
)


# ============================================================
# ORDER ANALYSIS
# ============================================================

st.divider()

left, right = st.columns(2)


with left:

    st.subheader("📦 Orders by Product")

    product_count = (
        filtered["product_type"]
        .value_counts()
    )

    fig, ax = plt.subplots(
        figsize=(7, 4)
    )

    product_count.plot(
        kind="bar",
        ax=ax
    )

    ax.set_ylabel("Orders")
    ax.set_xlabel("")

    plt.xticks(rotation=0)
    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


with right:

    st.subheader("⏱️ Process Time Distribution")

    fig, ax = plt.subplots(
        figsize=(7, 4)
    )

    ax.hist(
        filtered["process_time_hours"],
        bins=8
    )

    ax.set_xlabel(
        "Process Time (hours)"
    )

    ax.set_ylabel(
        "Orders"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


# ============================================================
# RISK ANALYSIS
# ============================================================

st.divider()

st.subheader("⚠️ Order Risk Analysis")

left, right = st.columns(2)


with left:

    risk_count = (
        filtered["is_high_risk"]
        .value_counts()
        .rename(
            {
                0: "Normal",
                1: "High Risk"
            }
        )
    )

    fig, ax = plt.subplots(
        figsize=(7, 4)
    )

    risk_count.plot(
        kind="bar",
        ax=ax
    )

    ax.set_ylabel(
        "Orders"
    )

    ax.set_xlabel("")

    plt.xticks(rotation=0)
    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


with right:

    st.subheader("📅 Due Days")

    fig, ax = plt.subplots(
        figsize=(7, 4)
    )

    ax.hist(
        filtered["due_days"],
        bins=10
    )

    ax.set_xlabel(
        "Days Until Due"
    )

    ax.set_ylabel(
        "Orders"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


# ============================================================
# MACHINE WORKLOAD
# ============================================================

st.divider()

st.subheader("⚙️ Machine Workload")

machine_workload = (
    schedule
    .groupby(
        "assigned_machine"
    )["process_time_hours"]
    .sum()
    .sort_values(
        ascending=False
    )
)


fig, ax = plt.subplots(
    figsize=(10, 4)
)

machine_workload.plot(
    kind="bar",
    ax=ax
)

ax.set_ylabel(
    "Production Hours"
)

ax.set_xlabel(
    "Machine"
)

plt.xticks(rotation=0)
plt.tight_layout()

st.pyplot(fig)

plt.close(fig)


# ============================================================
# MACHINE RISK
# ============================================================

st.divider()

st.subheader("🏭 Machine Risk Assessment")


col1, col2 = st.columns(2)


with col1:

    hours_per_day = st.number_input(
        "Production hours / day",
        min_value=1,
        max_value=24,
        value=8
    )


with col2:

    production_days = st.number_input(
        "Planning period (days)",
        min_value=1,
        max_value=365,
        value=30
    )


machine_capacity = (
    hours_per_day
    * production_days
)


machine_risk = (
    machine_workload
    .reset_index()
)


machine_risk.columns = [
    "Machine",
    "Workload Hours"
]


machine_risk["Utilization (%)"] = (
    machine_risk["Workload Hours"]
    / machine_capacity
    * 100
).round(1)


def get_machine_risk(
    utilization
):

    if utilization >= 90:
        return "🔴 High Risk"

    elif utilization >= 75:
        return "🟡 Medium Risk"

    return "🟢 Low Risk"


machine_risk["Risk Level"] = (
    machine_risk["Utilization (%)"]
    .apply(
        get_machine_risk
    )
)


st.markdown(
    f"**Machine Capacity:** "
    f"{machine_capacity} production hours"
)


st.dataframe(
    machine_risk,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# MACHINE RISK ALERT
# ============================================================

high_risk_machines = machine_risk[
    machine_risk["Risk Level"]
    == "🔴 High Risk"
]


medium_risk_machines = machine_risk[
    machine_risk["Risk Level"]
    == "🟡 Medium Risk"
]


if len(high_risk_machines) > 0:

    st.error(
        f"🔴 {len(high_risk_machines)} machine(s) "
        "are at high workload risk."
    )

elif len(medium_risk_machines) > 0:

    st.warning(
        f"🟡 {len(medium_risk_machines)} machine(s) "
        "are at medium workload risk."
    )

else:

    st.success(
        "🟢 All machines are within normal workload."
    )


# ============================================================
# DATA TABLE
# ============================================================

st.divider()

st.subheader("📋 Filtered Production Data")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)