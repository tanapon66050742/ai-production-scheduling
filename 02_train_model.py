import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

DATA = "cleaned_production_data.csv"
FEATURES = ["quantity", "process_time_hours", "due_days", "priority", "workload_ratio"]

df = pd.read_csv(DATA)
X = df[FEATURES]
y = df["is_high_risk"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=150, max_depth=5, random_state=42)
model.fit(X_train, y_train)
pred = model.predict(X_test)

print("Accuracy:", round(accuracy_score(y_test, pred), 3))
print(classification_report(y_test, pred, zero_division=0))
print("Feature importance:")
for name, importance in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {name}: {importance:.3f}")
