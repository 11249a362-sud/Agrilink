from app.ai.price_predictor import predict_price

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def forecast_prices(crop: str, location: str, quantity: float, month: int):
    base = predict_price(crop, location, quantity, month)["predicted_price_per_kg"]

    adjustments = [0.0, 0.5, 1.2, 0.8, 2.1, 2.8, 2.3]

    forecast = []

    for day, adj in zip(DAYS, adjustments):
        forecast.append({
            "day": day,
            "price": round(base + adj, 2)
        })

    return {
        "crop": crop,
        "location": location,
        "forecast": forecast
    }