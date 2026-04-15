import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torch.nn as nn
from torchvision import transforms, models
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

# ── DebIsh Activation (must match training.py exactly) ───────────
class DebIshActivation(nn.Module):
    def __init__(self, epsilon: float = 1e-7):
        super().__init__()
        self.epsilon = epsilon
        self.alpha   = nn.Parameter(torch.tensor(1.0))
        self.beta    = nn.Parameter(torch.tensor(0.5))

    def forward(self, x):
        dims        = list(range(1, x.dim()))
        var_x       = x.var(dim=dims, keepdim=True)
        norm_factor = 1.0 / torch.sqrt(var_x + self.epsilon)
        sigma       = torch.sigmoid(x)
        f_linear    = self.alpha * x
        f_nonlinear = self.beta * sigma * (1.0 - sigma) * x
        dominant    = torch.where(
            torch.abs(f_linear) >= torch.abs(f_nonlinear),
            f_linear, f_nonlinear
        )
        return dominant * norm_factor


# ── Model Definition (must match training.py exactly) ────────────
class PotatoDiseaseModel(nn.Module):
    def __init__(self, num_classes: int, dropout: float = 0.4):
        super().__init__()
        self.backbone = models.efficientnet_v2_s(weights=None)
        in_features   = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()

        self.head = nn.Sequential(
            nn.Linear(in_features, 512, bias=False),
            nn.BatchNorm1d(512),
            DebIshActivation(),
            nn.Dropout(dropout),

            nn.Linear(512, 256, bias=False),
            nn.BatchNorm1d(256),
            DebIshActivation(),
            nn.Dropout(dropout),

            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.head(self.backbone(x))


# ── Load model once at startup ────────────────────────────────────
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

checkpoint  = torch.load(
    "./saved_models/potato_disease_full.pth",
    map_location=DEVICE
)
CLASS_NAMES = checkpoint["class_names"]
CONFIG      = checkpoint["config"]

model = PotatoDiseaseModel(num_classes=len(CLASS_NAMES), dropout=CONFIG["dropout_rate"])
model.load_state_dict(checkpoint["model_state_dict"])
model.to(DEVICE)
model.eval()

print(f"✅ PyTorch model loaded on {DEVICE}")
print(f"✅ Classes: {CLASS_NAMES}")

# ── Disease metadata (keep exactly as before) ─────────────────────
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

# ── Image preprocessing ───────────────────────────────────────────
eval_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std =[0.229, 0.224, 0.225]),
])

def preprocess_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return eval_transforms(image).unsqueeze(0).to(DEVICE)


# ── Routes (identical contract as before — index.js unchanged) ────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ML Server is running", "port": 5000})


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        tensor = preprocess_image(file.read())

        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=1)[0].cpu().numpy()

        predicted_index = int(np.argmax(probs))
        predicted_class = CLASS_NAMES[predicted_index]
        confidence      = round(float(probs[predicted_index]) * 100, 2)

        result = {
            "prediction": predicted_class,
            "confidence": confidence,
            "treatment":  treatments.get(predicted_class, "Consult an agronomist."),
            "precautions": precautions.get(predicted_class, []),
            "severity":   severity_map.get(predicted_class, "unknown"),
            "all_probabilities": {
                CLASS_NAMES[i]: round(float(probs[i]) * 100, 2)
                for i in range(len(CLASS_NAMES))
            }
        }
        return jsonify(result)

    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return jsonify({"error": "Internal Model Error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)