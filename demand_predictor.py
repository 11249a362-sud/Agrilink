from app.ai.demand_model import (
    model,
    crop_encoder,
    location_encoder
)

def predict_demand(crop: str, location: str, month: int):

    crop_id = crop_encoder.transform([crop])[0]
    location_id = location_encoder.transform([location])[0]

    prediction = model.predict(
        [[crop_id, location_id, month]]
    )[0]

    if prediction >= 180:
        demand = "Very High"
        trend = "Increasing"
        recommendation = (
            "Increase production by 15%. Industries are expected to require more stock."
        )
    elif prediction >= 120:
        demand = "High"
        trend = "Stable"
        recommendation = (
            "Maintain current production levels."
        )
    elif prediction >= 80:
        demand = "Medium"
        trend = "Stable"
        recommendation = (
            "Normal market conditions."
        )
    else:
        demand = "Low"
        trend = "Decreasing"
        recommendation = (
            "Consider reducing production or storing inventory."
        )

    return {
        "expected_orders": round(float(prediction)),
        "expected_demand": demand,
        "price_trend": trend,
        "recommendation": recommendation
    }