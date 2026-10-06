import numpy as np
import pandas as pd

np.random.seed(42)
N = 150

df = pd.DataFrame({
    "order_id": [f"ORD-{i:04d}" for i in range(1, N + 1)],
    "product_type": np.random.choice(["Part_A", "Part_B", "Part_C"], N),
    "quantity": np.random.randint(50, 1000, N),
    "process_time_hours": np.random.randint(1, 9, N),
    "due_days": np.random.randint(3, 31, N),
    "priority": np.random.choice([1, 2, 3], N, p=[0.2, 0.5, 0.3])
})

df["available_hours"] = df["due_days"] * 8
df["workload_ratio"] = df["process_time_hours"] / df["available_hours"]
df["is_high_risk"] = (
    (df["workload_ratio"] > 0.8)
    | ((df["priority"] == 1) & (df["due_days"] <= 3))
).astype(int)

df.to_csv("cleaned_production_data.csv", index=False)
print(f"Created {len(df)} production orders")
print(df.head())
