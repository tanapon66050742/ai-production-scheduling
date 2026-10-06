import json
import os

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


# Load API key from .env
load_dotenv()


def build_summary(schedule):
    """Create a compact summary from the production schedule."""

    total = len(schedule)

    high_risk = int(schedule["is_high_risk"].sum())
    late = int(schedule["is_late"].sum())

    makespan = (
        float(schedule["end_hour"].max())
        if total > 0
        else 0
    )

    machine_hours = (
        schedule
        .groupby("assigned_machine")["process_time_hours"]
        .sum()
        .round(1)
        .to_dict()
    )

    # Select the most critical orders
    critical = (
        schedule
        .sort_values(
            ["is_late", "is_high_risk", "due_days"],
            ascending=[False, False, True]
        )
        .head(5)
    )

    critical_orders = critical[
        [
            "order_id",
            "due_days",
            "is_high_risk",
            "is_late",
            "assigned_machine",
        ]
    ].to_dict("records")

    return {
        "total_orders": total,
        "high_risk_orders": high_risk,
        "late_orders": late,
        "makespan_hours": round(makespan, 1),
        "machine_hours": machine_hours,
        "critical_orders": critical_orders,
    }


def template_report(summary):
    """Fallback report if GenAI is unavailable."""

    lines = [
        "DAILY PRODUCTION REPORT",
        f"Total orders: {summary['total_orders']}",
        f"High-risk orders: {summary['high_risk_orders']}",
        f"Late orders: {summary['late_orders']}",
        f"Makespan: {summary['makespan_hours']} hours",
        "",
        "Machine workload:",
    ]

    for machine, hours in summary["machine_hours"].items():
        lines.append(f"- {machine}: {hours} hours")

    lines += [
        "",
        "Priority actions:",
    ]

    if summary["late_orders"]:
        lines.append(
            "- Review late orders first and consider "
            "reassigning work to the least-loaded machine."
        )

    if summary["high_risk_orders"]:
        lines.append(
            "- Monitor high-risk orders closely and confirm "
            "material/machine readiness."
        )

    lines.append(
        "- Use the dashboard to inspect the schedule "
        "and risk orders before production starts."
    )

    return "\n".join(lines)


def generate_with_openrouter(summary):
    """Generate a production report using OpenRouter."""

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("WARNING: OPENROUTER_API_KEY not found in .env")
        return None

    try:
        # OpenRouter is compatible with the OpenAI Python SDK
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # Convert schedule summary to JSON
        summary_json = json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )

        # Prompt for GenAI
        prompt = f"""
คุณเป็นผู้ช่วยวางแผนการผลิตในโรงงาน

จากข้อมูล Production Schedule ด้านล่าง
ให้สร้างรายงานการผลิตประจำวันเป็นภาษาไทย

ข้อกำหนด:
1. ใช้ข้อมูลที่ให้มาเท่านั้น
2. ห้ามสร้างตัวเลขหรือข้อมูลใหม่
3. เขียนให้กระชับและเหมาะสำหรับผู้จัดการฝ่ายผลิต
4. แบ่งเป็น 3 หัวข้อ:
   - สรุปภาพรวม
   - จุดเสี่ยง
   - สิ่งที่ควรทำวันนี้
5. หากมี Late Orders ให้พูดถึงก่อน
6. หากมี High-risk Orders ให้ระบุว่าควรติดตาม
7. ระบุ Machine workload ที่สำคัญถ้าเกี่ยวข้อง

Production Schedule Summary:

{summary_json}
"""

        # Use OpenRouter free model
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        report = response.choices[0].message.content

        if report:
            return report.strip()

        return None

    except Exception as exc:
        print(f"GenAI unavailable: {exc}")
        return None


if __name__ == "__main__":

    # Load final production schedule
    schedule = pd.read_csv("final_production_schedule.csv")

    # Build summary
    summary = build_summary(schedule)

    # Try GenAI first
    report = generate_with_openrouter(summary)

    # Use template if GenAI is unavailable
    if not report:
        print("Using template report instead.")
        report = template_report(summary)

    # Save report
    with open(
        "ai_daily_report.txt",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(report)

    # Print report
    print("\n" + "=" * 60)
    print("AI DAILY PRODUCTION REPORT")
    print("=" * 60)
    print(report)
    print("=" * 60)

    print("\nReport saved to: ai_daily_report.txt")