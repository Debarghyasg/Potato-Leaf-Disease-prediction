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

checkpoint = torch.load(
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


# ── Disease metadata ──────────────────────────────────────────────
treatments = {
    "Early Blight": "Apply Mancozeb (Dithane M-45) or Chlorothalonil (Kavach) fungicide every 7–10 days.",
    "Late Blight":  "Apply Metalaxyl + Mancozeb (Ridomil Gold MZ) or Cymoxanil (Curzate) immediately.",
    "Healthy":      "No treatment needed. Continue regular maintenance and monitoring.",
    "Fungi":        "Apply Carbendazim (Bavistin) or Tebuconazole (Folicur) fungicide spray.",
    "Pest":         "Apply Imidacloprid (Confidor) or Lambda-cyhalothrin (Karate) insecticide.",
    "Virus":        "No chemical cure. Remove and destroy infected plants. Control aphid vectors with Thiamethoxam (Actara)."
}

precautions = {
    "Early Blight": [
        "Remove and destroy infected leaves immediately",
        "Avoid overhead watering — water at the base only",
        "Rotate crops every season to break the disease cycle",
        "Maintain proper plant spacing for air circulation",
        "Apply Dithane M-45 or Kavach at first sign of symptoms",
        "Avoid working in the field when leaves are wet"
    ],
    "Late Blight": [
        "Destroy ALL infected plant material — never compost it",
        "Apply Ridomil Gold MZ within 24 hours of detection",
        "Avoid overhead irrigation completely",
        "Use certified disease-free seed potatoes only",
        "Monitor daily during cool (10–20°C) and moist weather",
        "Do not enter field when foliage is wet to avoid spread"
    ],
    "Healthy": [
        "Continue regular watering at the base of the plant",
        "Inspect leaves weekly for early signs of disease",
        "Maintain adequate spacing between plants",
        "Apply balanced NPK fertilizer as scheduled",
        "Keep field free of weeds to reduce pest pressure",
        "Rotate crops each season as a preventive measure"
    ],
    "Fungi": [
        "Remove and burn all visibly infected plant parts",
        "Apply Bavistin (Carbendazim) or Folicur (Tebuconazole) spray",
        "Avoid excess moisture and improve field drainage",
        "Do not reuse soil from heavily infected plots",
        "Maintain crop rotation with non-host plants",
        "Spray during early morning for best absorption"
    ],
    "Pest": [
        "Inspect undersides of leaves daily for eggs and insects",
        "Apply Confidor (Imidacloprid) or Karate (Lambda-cyhalothrin)",
        "Use yellow sticky traps to monitor and catch flying pests",
        "Remove heavily infested leaves and destroy them",
        "Avoid excessive nitrogen fertilizer — attracts pests",
        "Introduce natural predators like ladybugs where possible"
    ],
    "Virus": [
        "Immediately uproot and destroy ALL infected plants",
        "Control aphids with Actara (Thiamethoxam) — they spread virus",
        "Never propagate cuttings from infected plants",
        "Disinfect all tools with 10% bleach solution after use",
        "Use virus-resistant certified seed potato varieties",
        "Install insect-proof nets to block vector insects"
    ]
}

severity_map = {
    "Early Blight": "moderate",
    "Late Blight":  "severe",
    "Healthy":      "none",
    "Fungi":        "moderate",
    "Pest":         "moderate",
    "Virus":        "severe"
}

# ── Medicine details with prices sourced from DB (medicines.sql) ──
# Prices in INR for standard retail pack sizes.
# Sources: BigHaat, IndiaMART, AgriBegri (verified Apr 2025)
# ⚠ If you connect a live DB, replace this dict with a DB query:
#   SELECT name, chemical, dose, pack_size, price_inr
#   FROM medicines WHERE disease_target = %s AND in_stock = 1
medicine_details = {
    "Early Blight": [
        {
            "name":      "Dithane M-45",
            "chemical":  "Mancozeb 75% WP",
            "dose":      "2.5g per litre of water",
            "pack_size": "250g pack",
            "price":     250,           # Rs. — BigHaat listed
        },
        {
            "name":      "Kavach",
            "chemical":  "Chlorothalonil 75% WP",
            "dose":      "2g per litre of water",
            "pack_size": "250g pack",
            "price":     390,           # Rs. — BigHaat Rs.390 for 250g
        },
        {
            "name":      "Indofil M-45",
            "chemical":  "Mancozeb 75% WP",
            "dose":      "2.5g per litre of water",
            "pack_size": "250g pack",
            "price":     220,           # Rs. — BigHaat / AgriBegri ~Rs.220
        },
    ],
    "Late Blight": [
        {
            "name":      "Ridomil Gold MZ",
            "chemical":  "Metalaxyl 4% + Mancozeb 64% WP",
            "dose":      "2.5g per litre of water",
            "pack_size": "250g pack",
            "price":     649,           # Rs. — Syngenta brand, BigHaat
        },
        {
            "name":      "Curzate M8",
            "chemical":  "Cymoxanil 8% + Mancozeb 64% WP",
            "dose":      "3g per litre of water",
            "pack_size": "200g pack",
            "price":     520,           # Rs. — IndiaMART ~Rs.500-540
        },
        {
            "name":      "Equation Pro",
            "chemical":  "Famoxadone + Cymoxanil",
            "dose":      "0.5g per litre of water",
            "pack_size": "100g pack",
            "price":     750,           # Rs. — DuPont/Corteva, IndiaMART
        },
    ],
    "Healthy": [],
    "Fungi": [
        {
            "name":      "Bavistin",
            "chemical":  "Carbendazim 50% WP",
            "dose":      "1g per litre of water",
            "pack_size": "100g pack",
            "price":     158,           # Rs. — BigHaat starting Rs.158
        },
        {
            "name":      "Folicur",
            "chemical":  "Tebuconazole 25.9% EC",
            "dose":      "1ml per litre of water",
            "pack_size": "100ml bottle",
            "price":     480,           # Rs. — Bayer brand, AgriBegri
        },
        {
            "name":      "Saaf",
            "chemical":  "Carbendazim 12% + Mancozeb 63% WP",
            "dose":      "2g per litre of water",
            "pack_size": "250g pack",
            "price":     320,           # Rs. — UPL Saaf, BigHaat
        },
    ],
    "Pest": [
        {
            "name":      "Confidor",
            "chemical":  "Imidacloprid 17.8% SL",
            "dose":      "0.5ml per litre of water",
            "pack_size": "100ml bottle",
            "price":     545,           # Rs. — Bayer brand, BigHaat
        },
        {
            "name":      "Karate",
            "chemical":  "Lambda-cyhalothrin 5% EC",
            "dose":      "1ml per litre of water",
            "pack_size": "100ml bottle",
            "price":     285,           # Rs. — Syngenta brand, AgriBegri
        },
        {
            "name":      "Rogor",
            "chemical":  "Dimethoate 30% EC",
            "dose":      "2ml per litre of water",
            "pack_size": "100ml bottle",
            "price":     130,           # Rs. — generic, IndiaMART
        },
    ],
    "Virus": [
        {
            "name":      "Actara",
            "chemical":  "Thiamethoxam 25% WG",
            "dose":      "0.5g per litre (for aphid control)",
            "pack_size": "100g pack",
            "price":     890,           # Rs. — Syngenta Actara, BigHaat
        },
        {
            "name":      "Confidor",
            "chemical":  "Imidacloprid 17.8% SL",
            "dose":      "0.5ml per litre (for vector control)",
            "pack_size": "100ml bottle",
            "price":     545,           # Rs. — Bayer brand, BigHaat
        },
    ]
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


# ── Routes ────────────────────────────────────────────────────────
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
            "prediction":        predicted_class,
            "confidence":        confidence,
            "treatment":         treatments.get(predicted_class, "Consult an agronomist."),
            "precautions":       precautions.get(predicted_class, []),
            "severity":          severity_map.get(predicted_class, "unknown"),
            "medicines":         medicine_details.get(predicted_class, []),
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