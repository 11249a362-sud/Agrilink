def decide_reallocation(
    unsold_quantity: float,
    demand_level: str
):
    """
    AI decides how much stock should be reallocated
    based on demand conditions.
    """

    demand = demand_level.lower()

    if demand == "high":
        ratio = 0.70
    elif demand == "medium":
        ratio = 0.50
    else:
        ratio = 0.30

    transfer_quantity = unsold_quantity * ratio
    reserve_quantity = unsold_quantity - transfer_quantity

    return {
        "transfer_quantity": round(transfer_quantity, 2),
        "reserve_quantity": round(reserve_quantity, 2),
        "ratio": ratio,
        "reason": f"Demand level: {demand_level}"
    }