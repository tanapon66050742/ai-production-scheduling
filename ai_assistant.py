import importlib.util
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# BASE PATH
# ============================================================

BASE = Path(__file__).resolve().parents[1]

load_dotenv(BASE / ".env")


# ============================================================
# LOAD GENAI MODULE
# ============================================================

def load_module(filename, name):

    spec = importlib.util.spec_from_file_location(
        name,
        BASE / filename
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


genai_mod = load_module(
    "05_genai_report.py",
    "genai_page_module"
)


# ============================================================
# PAGE
# ============================================================

st.title("🤖 AI Production Assistant")

st.caption(
    "Ask questions about production orders, risks, workload and scheduling."
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

summary = genai_mod.build_summary(schedule)


# ============================================================
# AI FUNCTION
# ============================================================

def ask_ai(question, summary, schedule):

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return (
            "❌ ไม่พบ OPENROUTER_API_KEY\n\n"
            "กรุณาตรวจสอบไฟล์ `.env` ในโฟลเดอร์โปรเจกต์"
        )

    try:

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # ----------------------------------------------------
        # RISK ORDERS
        # ----------------------------------------------------

        risk_orders = schedule[
            (schedule["is_high_risk"] == 1)
            | (schedule["is_late"] == 1)
        ].copy()

        risk_columns = [
            "order_id",
            "product_type",
            "assigned_machine",
            "process_time_hours",
            "due_days",
            "priority",
            "is_high_risk",
            "is_late",
        ]

        risk_orders = risk_orders[risk_columns]

        # ----------------------------------------------------
        # MACHINE WORKLOAD
        # ----------------------------------------------------

        machine_workload = (
            schedule
            .groupby("assigned_machine")["process_time_hours"]
            .sum()
            .round(1)
            .to_dict()
        )

        # ----------------------------------------------------
        # CONTEXT
        # ----------------------------------------------------

        context = {
            "summary": summary,
            "machine_workload": machine_workload,
            "risk_orders": risk_orders.to_dict(
                "records"
            ),
        }

        context_json = json.dumps(
            context,
            ensure_ascii=False,
            indent=2,
        )

        # ----------------------------------------------------
        # PROMPT
        # ----------------------------------------------------

        prompt = f"""
คุณเป็น AI Production Planning Assistant
สำหรับช่วยวิเคราะห์และวางแผนการผลิตในโรงงาน

ให้ตอบคำถามของผู้ใช้โดยใช้ข้อมูล Production Data
ที่ให้ไว้ด้านล่างเท่านั้น

กฎ:
1. ห้ามสร้างตัวเลขใหม่
2. ห้ามสร้าง Order ID ใหม่
3. ห้ามสมมติข้อมูลที่ไม่มีอยู่ใน Dataset
4. ตอบเป็นภาษาไทย
5. ตอบให้กระชับและเข้าใจง่าย
6. เน้น Production Planning, Risk, Workload และ Scheduling
7. ถ้าข้อมูลไม่เพียงพอ ให้บอกตรง ๆ ว่าข้อมูลไม่เพียงพอ

Production Data:
{context_json}

คำถามของผู้ใช้:
{question}
"""

        # ----------------------------------------------------
        # OPENROUTER
        # ----------------------------------------------------

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # ----------------------------------------------------
        # GET ANSWER
        # ----------------------------------------------------

        if not response.choices:
            return "❌ AI ไม่ส่งคำตอบกลับมา"

        message = response.choices[0].message

        answer = message.content

        if not answer:
            return "❌ AI ส่งคำตอบว่างกลับมา"

        return answer.strip()

    except Exception as e:

        return (
            "❌ เกิดข้อผิดพลาดในการเรียก AI\n\n"
            f"`{str(e)}`"
        )


# ============================================================
# CHAT HISTORY
# ============================================================

if "messages" not in st.session_state:

    st.session_state["messages"] = []


# ============================================================
# QUICK QUESTIONS
# ============================================================

st.subheader("💡 Quick Questions")

c1, c2, c3 = st.columns(3)

quick_question = None


with c1:

    if st.button(
        "🚨 Risky Orders",
        use_container_width=True,
    ):

        quick_question = (
            "มี Order ไหนที่เป็น High-risk หรือ Late "
            "บ้าง และควรติดตาม Order ไหนก่อน?"
        )


with c2:

    if st.button(
        "⚙️ Busiest Machine",
        use_container_width=True,
    ):

        quick_question = (
            "Machine ไหนมี workload สูงที่สุด "
            "และมี workload เท่าไร?"
        )


with c3:

    if st.button(
        "📊 Production Summary",
        use_container_width=True,
    ):

        quick_question = (
            "ช่วยสรุปสถานะ Production ปัจจุบัน "
            "ให้ฉันแบบสั้น ๆ"
        )


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state["messages"]:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# USER CHAT INPUT
# ============================================================

user_question = st.chat_input(
    "Ask about your production data..."
)


# ============================================================
# DETERMINE QUESTION
# ============================================================

question = quick_question or user_question


# ============================================================
# ASK AI
# ============================================================

if question:

    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    st.session_state["messages"].append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):

        st.markdown(question)

    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("🤖 AI กำลังวิเคราะห์ข้อมูล..."):

            answer = ask_ai(
                question,
                summary,
                schedule,
            )

        st.markdown(answer)

    # --------------------------------------------------------
    # SAVE RESPONSE
    # --------------------------------------------------------

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# ============================================================
# CURRENT PRODUCTION STATUS
# ============================================================

st.divider()

st.subheader("📊 Current Production Status")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Total Orders",
    summary["total_orders"],
)

c2.metric(
    "High Risk",
    summary["high_risk_orders"],
)

c3.metric(
    "Late Orders",
    summary["late_orders"],
)
