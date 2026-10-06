import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


BASE = Path(__file__).resolve().parents[1]


# ============================================================
# LOAD FORECAST MODULE
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
    "forecast_page_module"
)


# ============================================================
# PAGE
# ============================================================

st.title("🔮 Demand Forecast")

st.caption(
    "Forecast future production demand using time-series analysis."
)


# ============================================================
# DATA
# ============================================================

@st.cache_data
def get_forecast():

    history = forecast_mod.create_history()

    forecast = forecast_mod.forecast_demand(
        history
    )

    return history, forecast


history, forecast = get_forecast()


# ============================================================
# PRODUCT
# ============================================================

products = sorted(
    history["product_type"].unique()
)

selected = st.selectbox(
    "Select Product",
    products
)


h = history[
    history["product_type"] == selected
].copy()

f = forecast[
    forecast["product_type"] == selected
].copy()


# ============================================================
# KPI
# ============================================================

st.subheader("📊 Forecast Summary")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Historical Avg",
    f'{h["demand"].mean():.0f}'
)

c2.metric(
    "Forecast Avg",
    f'{f["forecast_demand"].mean():.0f}'
)

c3.metric(
    "Peak Forecast",
    f'{f["forecast_demand"].max():.0f}'
)


# ============================================================
# CHART
# ============================================================

st.divider()

st.subheader(
    f"📈 {selected} Demand Forecast"
)

fig, ax = plt.subplots(
    figsize=(12, 5)
)

ax.plot(
    h["date"],
    h["demand"],
    marker="o",
    label="Historical"
)

ax.plot(
    f["date"],
    f["forecast_demand"],
    marker="o",
    label="Forecast"
)

ax.set_xlabel("Date")
ax.set_ylabel("Demand")

ax.legend()

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.xticks(rotation=30)

plt.tight_layout()

st.pyplot(fig)

plt.close(fig)


# ============================================================
# FORECAST TABLE
# ============================================================

st.divider()

st.subheader("📋 Forecast Details")

display_forecast = f.copy()

display_forecast["forecast_demand"] = (
    display_forecast["forecast_demand"]
    .round(0)
    .astype(int)
)

st.dataframe(
    display_forecast,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# INSIGHT
# ============================================================

st.divider()

avg_forecast = f["forecast_demand"].mean()
max_forecast = f["forecast_demand"].max()
min_forecast = f["forecast_demand"].min()

st.subheader("💡 Forecast Insight")

st.info(
    f"""
    **{selected}** มีความต้องการคาดการณ์เฉลี่ยประมาณ
    **{avg_forecast:.0f} units** ในช่วง Forecast

    โดยมีค่าคาดการณ์สูงสุดประมาณ
    **{max_forecast:.0f} units**
    และต่ำสุดประมาณ
    **{min_forecast:.0f} units**

    ข้อมูล Forecast สามารถนำไปใช้ประกอบการวางแผน
    Production Scheduling และ Capacity Planning ได้
    """
)