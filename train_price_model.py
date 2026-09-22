import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

data = pd.read_csv(BASE_DIR / "market_data.csv")

crop_encoder = LabelEncoder()
location_encoder = LabelEncoder()

data["crop_encoded"] = crop_encoder.fit_transform(data["crop"])
data["location_encoded"] = location_encoder.fit_transform(data["location"])

X = data[
    ["crop_encoded", "location_encoded", "month", "quantity"]
]

y = data["price"]

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42
)

model.fit(X, y)

joblib.dump(model, BASE_DIR / "price_model.pkl")
joblib.dump(crop_encoder, BASE_DIR / "crop_encoder.pkl")
joblib.dump(location_encoder, BASE_DIR / "location_encoder.pkl")

print("Realistic market price model trained successfully")