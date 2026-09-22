from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent

model = joblib.load(BASE_DIR / "demand_model.pkl")
crop_encoder = joblib.load(BASE_DIR / "demand_crop_encoder.pkl")
location_encoder = joblib.load(BASE_DIR / "demand_location_encoder.pkl")