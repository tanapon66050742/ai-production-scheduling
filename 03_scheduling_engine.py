import pandas as pd

INPUT = "cleaned_production_data.csv"
OUTPUT = "final_production_schedule.csv"
MACHINES = ["Machine_A", "Machine_B", "Machine_C"]

df = pd.read_csv(INPUT)

# Proposed rule: high-risk first, then earliest due date, then priority, then shortest processing time.
df = df.sort_values(
    ["is_high_risk", "due_days", "priority", "process_time_hours"],
    ascending=[False, True, True, True]
).reset_index(drop=True)

machine_available = {m: 0.0 for m in MACHINES}
rows = []

for _, order in df.iterrows():
    machine = min(machine_available, key=machine_available.get)
    start = machine_available[machine]
    end = start + float(order["process_time_hours"])
    machine_available[machine] = end
    rows.append({
        "order_id": order["order_id"],
        "product_type": order["product_type"],
        "assigned_machine": machine,
        "start_hour": start,
        "end_hour": end,
        "process_time_hours": order["process_time_hours"],
        "due_days": order["due_days"],
        "due_hour": order["due_days"] * 8,
        "priority": order["priority"],
        "is_high_risk": order["is_high_risk"],
    })

schedule = pd.DataFrame(rows)
schedule["is_late"] = (schedule["end_hour"] > schedule["due_hour"]).astype(int)
schedule.to_csv(OUTPUT, index=False)

print("Machine total hours:")
print(schedule.groupby("assigned_machine")["process_time_hours"].sum())
print("Late orders:", int(schedule["is_late"].sum()))
print("Makespan:", round(schedule["end_hour"].max(), 2), "hours")
