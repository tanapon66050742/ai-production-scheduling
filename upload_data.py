import importlib.util
from pathlib import Path

import pandas as pd
import streamlit as st


BASE = Path(__file__).resolve().parents[1]


# ============================================================
# PAGE CONFIG
# ============================================================

st.title("📁 Upload & Analyze Production Data")

st.caption(
    "Upload production data and run AI-assisted risk analysis "
    "and rule-based production scheduling."
)


# ============================================================
# LOAD EXISTING MODEL
# ============================================================

def load_module(filename, name):

    spec = importlib.util.spec_from_file_location(
        name,
        BASE / filename
    )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


model_mod = load_module(
    "02_train_model.py",
    "model_module"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "order_id",
    "product_type",
    "quantity",
    "process_time_hours",
    "due_days",
    "priority",
]


# ============================================================
# UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Choose a production CSV file",
    type=["csv"]
)


if uploaded_file is None:

    st.info(
        "Upload a CSV file to start production analysis."
    )

    st.markdown(
        """
        ### 📋 Required columns

        Your CSV should contain:

        - `order_id`
        - `product_type`
        - `quantity`
        - `process_time_hours`
        - `due_days`
        - `priority`

        After uploading, the system will:

        **Validate → Analyze → Predict Risk → Schedule Production**
        """
    )

    st.stop()


# ============================================================
# READ DATA
# ============================================================

try:

    df = pd.read_csv(
        uploaded_file
    )

except Exception as e:

    st.error(
        f"Unable to read CSV file: {e}"
    )

    st.stop()


st.success(
    f"Successfully uploaded **{len(df):,} orders**."
)


# ============================================================
# DATA VALIDATION
# ============================================================

st.subheader("🔍 Data Validation")

missing_columns = [
    col
    for col in REQUIRED_COLUMNS
    if col not in df.columns
]


if missing_columns:

    st.error(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )

    st.dataframe(
        df.head(),
        use_container_width=True,
        hide_index=True
    )

    st.stop()


# Check missing values

missing_values = int(
    df[REQUIRED_COLUMNS]
    .isna()
    .sum()
    .sum()
)


if missing_values > 0:

    st.warning(
        f"Found {missing_values} missing values "
        "in required columns."
    )

else:

    st.success(
        "All required columns are available and complete."
    )


# ============================================================
# DATA PREVIEW
# ============================================================

with st.expander(
    "👀 Preview Uploaded Data",
    expanded=False
):

    st.dataframe(
        df.head(20),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ANALYZE BUTTON
# ============================================================

st.divider()

analyze = st.button(
    "🚀 Analyze & Generate Production Schedule",
    type="primary",
    use_container_width=True
)


if analyze:

    # --------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------

    data = df.copy()

    numeric_columns = [
        "quantity",
        "process_time_hours",
        "due_days",
        "priority",
    ]

    for col in numeric_columns:

        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    data = data.dropna(
        subset=REQUIRED_COLUMNS
    ).copy()


    # --------------------------------------------------------
    # CREATE WORKLOAD RATIO
    # --------------------------------------------------------

    data["workload_ratio"] = (
        data["process_time_hours"]
        / data["due_days"].clip(lower=1)
    )


    # --------------------------------------------------------
    # RISK CALCULATION
    # --------------------------------------------------------
    # Same rule used in the project dataset.
    #
    # High risk when:
    # - short due date
    # - high workload
    # - high priority
    #
    # --------------------------------------------------------

    data["is_high_risk"] = (
        (
            (data["workload_ratio"] >= 2.0)
            | (data["due_days"] <= 5)
        )
        & (data["priority"] <= 2)
    ).astype(int)


    # --------------------------------------------------------
    # RULE-BASED SCHEDULING
    # --------------------------------------------------------

    data = data.sort_values(
        [
            "is_high_risk",
            "due_days",
            "priority",
            "process_time_hours",
        ],
        ascending=[
            False,
            True,
            True,
            True,
        ]
    ).reset_index(drop=True)


    machines = [
        "Machine_A",
        "Machine_B",
        "Machine_C",
    ]

    machine_available = {
        machine: 0.0
        for machine in machines
    }

    schedule_rows = []


    for _, order in data.iterrows():

        machine = min(
            machine_available,
            key=machine_available.get
        )

        start = machine_available[machine]

        end = (
            start
            + float(order["process_time_hours"])
        )

        machine_available[machine] = end

        schedule_rows.append(
            {
                "order_id": order["order_id"],
                "product_type": order["product_type"],
                "assigned_machine": machine,
                "start_hour": start,
                "end_hour": end,
                "process_time_hours": (
                    order["process_time_hours"]
                ),
                "due_days": order["due_days"],
                "due_hour": (
                    order["due_days"] * 8
                ),
                "priority": order["priority"],
                "workload_ratio": (
                    order["workload_ratio"]
                ),
                "is_high_risk": (
                    order["is_high_risk"]
                ),
            }
        )


    result = pd.DataFrame(
        schedule_rows
    )


    # --------------------------------------------------------
    # LATE ORDERS
    # --------------------------------------------------------

    result["is_late"] = (
        result["end_hour"]
        > result["due_hour"]
    ).astype(int)


    # --------------------------------------------------------
    # SAVE TO SESSION
    # --------------------------------------------------------

    st.session_state[
        "uploaded_schedule"
    ] = result

    st.session_state[
        "uploaded_data"
    ] = data


# ============================================================
# SHOW ANALYSIS RESULT
# ============================================================

if "uploaded_schedule" not in st.session_state:

    st.info(
        "Upload your CSV and click "
        "**Analyze & Generate Production Schedule** "
        "to start the analysis."
    )

    st.stop()


result = st.session_state[
    "uploaded_schedule"
]


data = st.session_state[
    "uploaded_data"
]


# ============================================================
# KPI
# ============================================================

st.divider()

st.subheader("📊 Production Analysis")

total_orders = len(result)

high_risk = int(
    result["is_high_risk"].sum()
)

late_orders = int(
    result["is_late"].sum()
)

makespan = float(
    result["end_hour"].max()
)


c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Orders",
    total_orders
)

c2.metric(
    "High Risk",
    high_risk
)

c3.metric(
    "Late Orders",
    late_orders
)

c4.metric(
    "Makespan",
    f"{makespan:.0f} h"
)


# ============================================================
# MACHINE WORKLOAD
# ============================================================

st.divider()

st.subheader("⚙️ Machine Workload")

workload = (
    result
    .groupby(
        "assigned_machine"
    )["process_time_hours"]
    .sum()
    .sort_values(
        ascending=False
    )
)


st.bar_chart(
    workload
)


# ============================================================
# RISK ANALYSIS
# ============================================================

st.divider()

st.subheader("🚨 Risk & Late Orders")

risk_orders = result[
    (result["is_high_risk"] == 1)
    | (result["is_late"] == 1)
].copy()


risk_orders = risk_orders.sort_values(
    [
        "is_late",
        "is_high_risk",
        "due_days",
    ],
    ascending=[
        False,
        False,
        True,
    ]
)


if len(risk_orders) == 0:

    st.success(
        "No high-risk or late orders detected."
    )

else:

    st.dataframe(
        risk_orders[
            [
                "order_id",
                "product_type",
                "assigned_machine",
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


# ============================================================
# PRODUCTION SCHEDULE
# ============================================================

st.divider()

st.subheader("🗓️ Production Schedule")

st.dataframe(
    result[
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


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

st.subheader("⬇️ Export Results")

csv_data = result.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    "Download Production Schedule",
    data=csv_data,
    file_name="uploaded_production_schedule.csv",
    mime="text/csv",
    use_container_width=True
)