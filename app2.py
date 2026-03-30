import os
# Disable oneDNN custom operations for cleaner logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
CORS(app) # Allows the Node.js server to communicate without blocked requests

# ── Load model & class names ──────────────────────────────────────
# Ensure this file is in the same directory as app2.py
# app2.py line 17 — change to:
model = tf.keras.models.load_model("potato_leaf_prod_v1.keras")

try:
    with open("class_names.txt", "r") as f:
        class_names = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    # Fallback if the file is missing
    class_names = ["Early Blight", "Late Blight", "Healthy"]

IMG_SIZE = 224
print("Model Loaded. Detected Classes:", class_names)

# ── Disease Metadata ──────────────────────────────────────────────
# These match the keys in your result.ejs template
treatments = {
    "Early Blight": "Use Mancozeb or Chlorothalonil fungicide.",
    "Late Blight":  "Apply Metalaxyl and remove infected leaves immediately.",
    "Healthy":      "No treatment needed. Maintain proper care."
}

precautions = {
    "Early Blight": [
        "Remove and destroy infected leaves immediately",
        "Avoid overhead watering — water at the base",
        "Rotate crops each season to break the disease cycle",
        "Maintain proper plant spacing for airflow",
        "Apply fungicide at first sign of symptoms"
    ],
    "Late Blight": [
        "Destroy all infected plant material — do not compost",
        "Avoid working in the field when leaves are wet",
        "Use certified disease-free seed potatoes",
        "Monitor plants daily during cool, moist weather",
        "Apply copper-based fungicide as a preventive measure"
    ],
    "Healthy": [
        "Continue regular watering at the base of the plant",
        "Monitor weekly for early signs of disease",
        "Maintain adequate spacing between plants",
        "Apply balanced fertilizer as scheduled",
        "Keep weeds cleared to reduce pest pressure"
    ]
}

severity_map = {
    "Early Blight": "moderate",
    "Late Blight":  "severe",
    "Healthy":      "none"
}

# ── Helper ────────────────────────────────────────────────────────
def preprocess_image(image_bytes):
    # Convert bytes to PIL Image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((IMG_SIZE, IMG_SIZE))
    image = np.array(image)
    
    # ResNet specific preprocessing
    image = tf.keras.applications.efficientnet_v2.preprocess_input(image)
    image = np.expand_dims(image, axis=0)
    return image

# ── Routes ────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ML Server is running", "port": 5000})

@app.route("/predict", methods=["POST"])
def predict():
    # 1. Check if file exists in the request
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # 2. Read image and preprocess
        image_bytes = file.read()
        processed_img = preprocess_image(image_bytes)

        # 3. Model Inference
        prediction = model.predict(processed_img)
        predicted_index = int(np.argmax(prediction))
        predicted_class = class_names[predicted_index]
        confidence = round(float(np.max(prediction)) * 100, 2)

        # 4. Construct JSON response for Node.js
        result = {
            "prediction": predicted_class,
            "confidence": confidence,
            "treatment": treatments.get(predicted_class, "Consult an agronomist."),
            "precautions": precautions.get(predicted_class, []),
            "severity": severity_map.get(predicted_class, "unknown"),
            "all_probabilities": {
                class_names[i]: round(float(prediction[0][i]) * 100, 2)
                for i in range(len(class_names))
            }
        }

        # Return just the data — Node.js handles the rest!
        return jsonify(result)

    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return jsonify({"error": "Internal Model Error", "details": str(e)}), 500

if __name__ == "__main__":
    # Ensure this runs on port 5000 to match your Node.js FLASK_URL
    app.run(host="0.0.0.0", port=5000, debug=True)