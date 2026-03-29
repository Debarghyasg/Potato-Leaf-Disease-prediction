import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import tensorflow as tf
import numpy as np
from PIL import Image

app = Flask(__name__)
CORS(app)

# model
model = tf.keras.models.load_model("potato_leaf_prodv1.keras")

# class names
with open("class_names.txt", "r") as f:
    class_names = [line.strip() for line in f.readlines()]

IMG_SIZE = 128
print(class_names)

treatments = {
    "Early Blight": "Use Mancozeb or Chlorothalonil fungicide.",
    "Late Blight": "Apply Metalaxyl and remove infected leaves immediately.",
    "Healthy": "No treatment needed. Maintain proper care."
}

def preprocess_image(image):
    image = image.resize((IMG_SIZE, IMG_SIZE))
    image = np.array(image)
    image = tf.keras.applications.resnet.preprocess_input(image)
    image = np.expand_dims(image, axis=0)
    return image

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/analyze")
def analyze():
    return render_template("analyze.html")

@app.route("/predict", methods=["POST"])
def predict():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    image = Image.open(file).convert("RGB")
    image = preprocess_image(image)

    prediction = model.predict(image)
    predicted_index = np.argmax(prediction)
    predicted_class = class_names[predicted_index]
    confidence = float(np.max(prediction)) * 100
    treatment = treatments.get(predicted_class, "No treatment information available.")

    return jsonify({
    "prediction": predicted_class,
    "confidence": round(confidence, 2),
    "treatment": treatment
})

if __name__ == "__main__":
    app.run(debug=True)
