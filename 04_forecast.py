import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def create_history(seed=42, days=30):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize() - pd.Timedelta(days=1), periods=days, freq="D")
    rows = []
    base = {"Part_A": 420, "Part_B": 330, "Part_C": 260}
    for product, level in base.items():
        for i, date in enumerate(dates):
            trend = 1 + 0.004 * i
            weekly = 1 + 0.12 * np.sin(2 * np.pi * i / 7)
            noise = rng.normal(0, 28)
            demand = max(50, int(level * trend * weekly + noise))
            rows.append({"date": date, "product_type": product, "demand": demand})
    return pd.DataFrame(rows)


def forecast_demand(history, horizon=7):
    outputs = []
    for product, g in history.groupby("product_type"):
        series = g.sort_values("date").set_index("date")["demand"]
        try:
            model = ExponentialSmoothing(
                series, trend="add", seasonal="add", seasonal_periods=7
            ).fit(optimized=True)
            fc = model.forecast(horizon)
        except Exception:
            fc = pd.Series([series.tail(7).mean()] * horizon,
                           index=pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=horizon))
        for date, value in fc.items():
            outputs.append({
                "date": date,
                "product_type": product,
                "forecast_demand": max(0, round(float(value))),
            })
    return pd.DataFrame(outputs)


if __name__ == "__main__":
    history = create_history()
    forecast = forecast_demand(history)
    history.to_csv("demand_history.csv", index=False)
    forecast.to_csv("demand_forecast.csv", index=False)
    print(forecast)
