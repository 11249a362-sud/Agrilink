from app.ai.price_predictor import predict_price
from app.ai.demand_predictor import predict_demand
def recommend_buyers(crop, location, quantity, month):

    industries = [
        {"name": "Fresh Foods Ltd", "distance_km": 8.4},
        {"name": "ABC Agro Industries", "distance_km": 15.2},
        {"name": "South Harvest Pvt Ltd", "distance_km": 21.7}
    ]

    price_info = predict_price(
        crop=crop,
        location=location,
        quantity=quantity,
        month=month
    )

    demand_info = predict_demand(
        crop=crop,
        location=location,
        month=month
    )

    buyers = []

    base_price = price_info["predicted_price_per_kg"]

    for i, industry in enumerate(industries):

        estimated_price = round(base_price - (i * 0.6), 2)

        buyers.append({
            "industry": industry["name"],
            "estimated_price": estimated_price,
            "distance_km": industry["distance_km"],
            "reason": (
                "Highest predicted price and closest buyer"
                if i == 0
                else "Strong market demand this month"
            )
        })

    return {
        "predicted_price_per_kg": base_price,
        "expected_demand": demand_info["expected_demand"],
        "best_buyers": buyers
    }