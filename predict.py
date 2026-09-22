import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input

# ===============================
# BASE DIRECTORY
# ===============================

BASE_DIR = Path(__file__).resolve().parent

# ===============================
# LOAD MODEL
# ===============================

MODEL_PATH = BASE_DIR / "model" / "tomato_best.keras"
model = tf.keras.models.load_model(MODEL_PATH)

# ===============================
# LOAD CLASS NAMES
# ===============================

CLASS_PATH = BASE_DIR / "class_names.json"

with open(CLASS_PATH, "r") as f:
    class_names = json.load(f)

# ===============================
# GET IMAGE PATH FROM BACKEND
# ===============================

if len(sys.argv) < 2:
    print(json.dumps({"error": "Image path not provided"}))
    sys.exit(1)

IMAGE_PATH = sys.argv[1]

# ===============================
# LOAD IMAGE
# ===============================

img = image.load_img(IMAGE_PATH, target_size=(224, 224))
img_array = image.img_to_array(img)
img_array = np.expand_dims(img_array, axis=0)
img_array = preprocess_input(img_array)

# ===============================
# PREDICT
# ===============================

prediction = model.predict(img_array, verbose=0)

predicted_index = int(np.argmax(prediction))
predicted_class = class_names[predicted_index]
confidence = float(prediction[0][predicted_index] * 100)

# ===============================
# RETURN JSON
# ===============================

result = {
    "vegetable": "Tomato",
    "condition": "Fresh" if predicted_class == "FreshTomato" else "Rotten",
    "confidence": round(confidence, 2),
    "recommendation": (
        "Suitable for Auction"
        if predicted_class == "FreshTomato"
        else "Not Suitable for Auction"
    )
}

print(json.dumps(result))