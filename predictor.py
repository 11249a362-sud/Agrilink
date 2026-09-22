from app.ai.model import model


# ============================================================
# CONFIDENCE-BASED GRADING
# ============================================================

def get_grade(confidence: float) -> str:
    """
    Convert YOLO prediction confidence into a Grade 1-5.

    Grade 1 -> Very High Confidence
    Grade 2 -> High Confidence
    Grade 3 -> Good Confidence
    Grade 4 -> Moderate Confidence
    Grade 5 -> Low Confidence
    """

    if confidence >= 90:
        return "Grade 1"

    elif confidence >= 80:
        return "Grade 2"

    elif confidence >= 70:
        return "Grade 3"

    elif confidence >= 60:
        return "Grade 4"

    else:
        return "Grade 5"


# ============================================================
# CROP PREDICTION
# ============================================================

def predict_crop(image_path: str):

    # --------------------------------------------------------
    # 1. Run YOLO
    # --------------------------------------------------------

    results = model(image_path)

    result = results[0]


    # --------------------------------------------------------
    # 2. Check whether a crop was detected
    # --------------------------------------------------------

    if len(result.boxes) == 0:

        return {
            "prediction": "No crop detected",
            "confidence": 0,
            "grade": "N/A"
        }


    # --------------------------------------------------------
    # 3. Get first detected object
    # --------------------------------------------------------

    box = result.boxes[0]


    # --------------------------------------------------------
    # 4. Get class ID
    # --------------------------------------------------------

    class_id = int(box.cls[0])


    # --------------------------------------------------------
    # 5. Get confidence
    # --------------------------------------------------------

    confidence = float(box.conf[0]) * 100


    # --------------------------------------------------------
    # 6. Get crop name
    # --------------------------------------------------------

    prediction = model.names[class_id]


    # --------------------------------------------------------
    # 7. Calculate confidence-based grade
    # --------------------------------------------------------

    grade = get_grade(confidence)


    # --------------------------------------------------------
    # 8. Return result
    # --------------------------------------------------------

    return {
        "prediction": prediction,
        "confidence": round(confidence, 2),
        "grade": grade
    }