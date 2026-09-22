from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent

model = joblib.load(BASE_DIR / "price_model.pkl")
crop_encoder = joblib.load(BASE_DIR / "crop_encoder.pkl")
location_encoder = joblib.load(BASE_DIR / "location_encoder.pkl")