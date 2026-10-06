import streamlit as st


st.set_page_config(
    page_title="AI Production Scheduling",
    page_icon="🏭",
    layout="wide",
)


dashboard_page = st.Page(
    "pages/dashboard.py",
    title="Dashboard",
    icon="📊",
    default=True,
)

analysis_page = st.Page(
    "pages/data_analysis.py",
    title="Data Analysis",
    icon="📈",
)

upload_page = st.Page(
    "pages/upload_data.py",
    title="Upload Data",
    icon="📁",
)

forecast_page = st.Page(
    "pages/forecast.py",
    title="Forecast",
    icon="🔮",
)

ai_page = st.Page(
    "pages/ai_assistant.py",
    title="AI Assistant",
    icon="🤖",
)


pg = st.navigation(
    [
        dashboard_page,
        analysis_page,
        upload_page,
        forecast_page,
        ai_page,
    ]
)


pg.run()