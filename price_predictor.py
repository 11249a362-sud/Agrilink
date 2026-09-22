def predict_price(crop: str, location: str, quantity: float, month: int):
    crop = crop.lower()
    location = location.lower()

    base_prices = {
        "tomato": 30,
        "onion": 25,
        "potato": 20,
        "rice": 40,
        "wheat": 35,
        "banana": 22,
        "carrot": 28,
    }

    base_price = base_prices.get(crop, 25)

    seasonal_factor = 1.0
    if month in [6, 7, 8]:
        seasonal_factor = 1.15
    elif month in [3, 4, 5]:
        seasonal_factor = 0.95

    location_factor = 1.0
    if location in ["coimbatore", "chennai", "madurai"]:
        location_factor = 1.05

    predicted_price = round(base_price * seasonal_factor * location_factor, 2)

    if predicted_price >= 35:
        demand = "High"
    elif predicted_price >= 25:
        demand = "Medium"
    else:
        demand = "Low"

    recommendation = (
        f"Sell now in {location.title()}. Prices are above seasonal average."
        if demand == "High"
        else f"Monitor the market in {location.title()} before selling."
    )

    return {
        "predicted_price_per_kg": predicted_price,
        "demand": demand,
        "recommendation": recommendation,
    }