from app.models.user import User

def recommend_buyers(db, crop: str, location: str, quantity: float, month: int):
    industries = db.query(User).filter(User.role == "industry").all()

    recommendations = []

    for industry in industries:
        score = 50

        # Location preference
        if industry.address and location.lower() in industry.address.lower():
            score += 30

        # Quantity preference
        if quantity >= 500:
            score += 20
        elif quantity >= 100:
            score += 10

        recommendations.append({
            "industry": industry.name,
            "location": industry.address,
            "score": score
        })

    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return {
        "recommended_buyers": recommendations[:5]
    }