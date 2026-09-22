import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

model = tf.keras.models.load_model(BASE_DIR / "model" / "tomato_best.keras")

with open(BASE_DIR / "class_names.json", "r") as f:
    class_names = json.load(f)

def grade_tomato(image_path: str):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    prediction = model.predict(img_array, verbose=0)

    predicted_index = int(np.argmax(prediction))
    predicted_class = class_names[predicted_index]
    confidence = float(prediction[0][predicted_index] * 100)

    return {
        "vegetable": "Tomato",
        "condition": "Fresh" if predicted_class == "FreshTomato" else "Rotten",
        "confidence": round(confidence, 2),
        "recommendation": (
            "Suitable for Auction"
            if predicted_class == "FreshTomato"
            else "Not Suitable for Auction"
        ),
    }