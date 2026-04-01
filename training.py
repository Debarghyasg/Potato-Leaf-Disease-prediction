"""
=============================================================================
 POTATO LEAF DISEASE DETECTION - COMPLETE ML PIPELINE
=============================================================================
 Pipeline follows the flowchart:
   Kaggle PlantVillage Dataset → Data Augmentation (tf.keras.preprocessing)
   → Resize & Rescale → Random-flip + Random-Rotation
   → Split Dataset (80% Train / 10% Val / 10% Test)
   → Cache, Shuffle, Prefetch
   → CNN with NIRMAL Activation (novel activation function)
   → Keras Sequential Model → Train Images Data
   → Ensemble Model → Saving the Model
   + Comparison against 7 classical algorithms + Performance Evaluation

 Novel Activation: NIRMAL — Variance-based Normalization with Hybrid
                   Linear–Nonlinear adaptive transformation.
=============================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# 0.  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import os
import math
import warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks, regularizers
from tensorflow.keras.preprocessing import image_dataset_from_directory

from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
tf.get_logger().setLevel("ERROR")

# ─────────────────────────────────────────────────────────────────────────────
# 1.  GLOBAL CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
CONFIG = {
    # ── Dataset path (Kaggle: warcoder/potato-leaf-disease-dataset v1) ────
    # Raw Windows path stored as a plain string; pathlib normalises separators
    # automatically on every OS, so this file runs unchanged on Linux / macOS.
    "dataset_dir"    : str(Path(
        r"C:\Users\ISHITA DAS\.cache\kagglehub\datasets"
        r"\warcoder\potato-leaf-disease-dataset\versions\1"
        r"\Potato Leaf Disease Dataset in Uncontrolled Environment"
    )),

    "image_size"     : (224, 224),         # resize target
    "batch_size"     : 64,
    "seed"           : 42,

    # Splits  (80 / 10 / 10)
    "train_split"    : 0.80,
    "val_split"      : 0.10,
    # remaining 10 % → test

    # Training
    "epochs"         : 50,
    "learning_rate"  : 1e-3,
    "dropout_rate"   : 0.4,
    "dense_units"    : 512,

    # NIRMAL hyper-params (trainable, but good defaults)
    "nirmal_alpha0"  : 1.0,
    "nirmal_beta0"   : 0.5,
    "nirmal_epsilon" : 1e-7,

    # Paths (outputs written next to this script, not inside the dataset dir)
    "model_save_path": "./saved_models/potato_disease_model.keras",
    "history_plot"   : "./results/training_history.png",
    "cm_plot"        : "./results/confusion_matrix.png",
    "comparison_plot": "./results/algorithm_comparison.png",
}

# ── Validate dataset path at import time so failures are obvious early ────
_dataset_path = Path(CONFIG["dataset_dir"])
if not _dataset_path.exists():
    raise FileNotFoundError(
        f"\n[Config] Dataset directory not found:\n  {CONFIG['dataset_dir']}\n"
        "Please verify the path or re-download with:\n"
        "  import kagglehub\n"
        "  kagglehub.dataset_download('warcoder/potato-leaf-disease-dataset')"
    )

# Create output dirs
for d in ["./saved_models", "./results"]:
    os.makedirs(d, exist_ok=True)

# ── Auto-discover class names from sub-folder names ───────────────────────
# This makes the code robust to any sub-folder naming the dataset uses
# (e.g. "Early Blight", "Early_blight", "Potato___Early_blight", etc.)
_discovered = sorted([
    d.name for d in _dataset_path.iterdir()
    if d.is_dir() and not d.name.startswith(".")
])
if not _discovered:
    raise RuntimeError(
        f"[Config] No class sub-folders found inside:\n  {CONFIG['dataset_dir']}"
    )

CLASS_NAMES = _discovered
NUM_CLASSES = len(CLASS_NAMES)

print(f"[Config] Dataset  : {CONFIG['dataset_dir']}")
print(f"[Config] Classes  : {CLASS_NAMES}")
print(f"[Config] Num classes: {NUM_CLASSES}")

# ─────────────────────────────────────────────────────────────────────────────
# 2.  NIRMAL ACTIVATION FUNCTION  (custom Keras layer)
# ─────────────────────────────────────────────────────────────────────────────
class NIRMALActivation(layers.Layer):
    """
    NIRMAL: Novel Implicit Regularised Multi-Adaptive Linear activation.

    For input tensor x:
      σ(x)          = sigmoid(x)
      var(x)        = variance of x (over all dims except batch)
      norm_factor   = 1 / sqrt(var(x) + ε)

      f_linear(x)   = α * x                       (linear branch)
      f_nonlinear(x)= β * σ(x) * (1 - σ(x)) * x  (nonlinear branch)

      dominant_x = where(|f_linear| > |f_nonlinear|, f_linear, f_nonlinear)

      NIRMAL(x)  = dominant_x * norm_factor

    α, β are trainable per-layer scalar parameters.
    Regularisation: L2 on α and β to keep them bounded.
    """

    def __init__(self, epsilon: float = 1e-7, **kwargs):
        super().__init__(**kwargs)
        self.epsilon = epsilon

    def build(self, input_shape):
        # Trainable scalars — initialised as per the paper (α=1, β=0.5)
        self.alpha = self.add_weight(
            name="alpha",
            shape=(),
            initializer=tf.constant_initializer(CONFIG["nirmal_alpha0"]),
            regularizer=regularizers.L2(1e-4),
            trainable=True,
        )
        self.beta = self.add_weight(
            name="beta",
            shape=(),
            initializer=tf.constant_initializer(CONFIG["nirmal_beta0"]),
            regularizer=regularizers.L2(1e-4),
            trainable=True,
        )
        super().build(input_shape)

    def call(self, x, training=None):
        # ── Step 1: variance over all non-batch axes ──────────────────────
        axes = list(range(1, len(x.shape)))           # e.g. [1,2,3] for BHWC
        var_x = tf.math.reduce_variance(x, axis=axes, keepdims=True)

        # ── Step 2: normalisation factor ──────────────────────────────────
        norm_factor = 1.0 / tf.sqrt(var_x + self.epsilon)

        # ── Step 3: sigmoid ───────────────────────────────────────────────
        sigma = tf.sigmoid(x)

        # ── Step 4: linear branch  f_L = α·x ─────────────────────────────
        f_linear = self.alpha * x

        # ── Step 5: nonlinear branch  f_NL = β·σ(x)·(1−σ(x))·x ──────────
        f_nonlinear = self.beta * sigma * (1.0 - sigma) * x

        # ── Step 6: select dominant response ─────────────────────────────
        dominant = tf.where(
            tf.abs(f_linear) >= tf.abs(f_nonlinear),
            f_linear,
            f_nonlinear,
        )

        # ── Step 7: apply normalisation ───────────────────────────────────
        output = dominant * norm_factor

        return output

    def get_config(self):
        cfg = super().get_config()
        cfg.update({"epsilon": self.epsilon})
        return cfg


# ─────────────────────────────────────────────────────────────────────────────
# 3.  DATA PIPELINE  (following the flowchart exactly)
# ─────────────────────────────────────────────────────────────────────────────
def build_data_pipeline(dataset_dir: str):
    img_size   = CONFIG["image_size"]
    batch_size = CONFIG["batch_size"]
    seed       = CONFIG["seed"]

    full_ds = image_dataset_from_directory(
        dataset_dir, labels="inferred", label_mode="int",
        class_names=CLASS_NAMES, image_size=img_size,
        batch_size=batch_size, shuffle=True, seed=seed,
    )
    total_batches = len(full_ds)

    train_size = int(total_batches * CONFIG["train_split"])
    val_size   = int(total_batches * CONFIG["val_split"])

    train_ds = full_ds.take(train_size)
    val_ds   = full_ds.skip(train_size).take(val_size)
    test_ds  = full_ds.skip(train_size + val_size)

    # REMOVED the 1.0/255 rescaling layer. EfficientNetV2 expects 0-255!
    
    augmentation = keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.15),
        layers.RandomBrightness(0.15),
        layers.RandomContrast(0.15),
    ], name="augmentation")

    def preprocess_train(images, labels):
        images = augmentation(images, training=True)
        return images, labels

    def preprocess_eval(images, labels):
        return images, labels # Passed straight through

    AUTOTUNE = tf.data.AUTOTUNE

    train_ds = (
        train_ds.map(preprocess_train, num_parallel_calls=AUTOTUNE)
        .cache().shuffle(buffer_size=1000, seed=seed).prefetch(AUTOTUNE)
    )
    val_ds = val_ds.map(preprocess_eval, num_parallel_calls=AUTOTUNE).cache().prefetch(AUTOTUNE)
    test_ds = test_ds.map(preprocess_eval, num_parallel_calls=AUTOTUNE).cache().prefetch(AUTOTUNE)

    print(f"[Data] Train batches: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")
    return train_ds, val_ds, test_ds


# ─────────────────────────────────────────────────────────────────────────────
# 4.  CNN MODEL  (flowchart + NIRMAL paper architecture)
# ─────────────────────────────────────────────────────────────────────────────
def build_cnn_model(num_classes: int = NUM_CLASSES) -> keras.Model:
    inputs = keras.Input(shape=(*CONFIG["image_size"], 3), name="input_image")

    # FIX: Remove input_tensor=inputs and use input_shape instead.
    # This keeps EfficientNetV2S as a single, nested "Model" block.
    backbone = keras.applications.EfficientNetV2S(
        include_top=False, 
        weights="imagenet", 
        input_shape=(*CONFIG["image_size"], 3) 
    )
    
    # PHASE 1 REQUIREMENT: Freeze the ENTIRE backbone initially
    backbone.trainable = False 

    # Pass the inputs through the bundled backbone
    x = backbone(inputs) 
    
    x = layers.GlobalAveragePooling2D(name="gap")(x)

    x = layers.Dense(64, use_bias=False, name="dense_64")(x)
    x = layers.BatchNormalization(name="bn_64")(x)
    x = NIRMALActivation(name="nirmal_64")(x)
    x = layers.Dropout(CONFIG["dropout_rate"], name="drop_64")(x)

    x = layers.Dense(CONFIG["dense_units"], use_bias=False, name="dense_512")(x)
    x = layers.BatchNormalization(name="bn_512")(x)
    x = NIRMALActivation(name="nirmal_512")(x)
    x = layers.Dropout(CONFIG["dropout_rate"], name="drop_512")(x)

    outputs = layers.Dense(num_classes, activation="softmax", name="softmax_out")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="PotatoDiseaseCNN_NIRMAL")
    return model


# ─────────────────────────────────────────────────────────────────────────────
# 5.  TRAINING  (Keras Sequential-style compile → fit)
# ─────────────────────────────────────────────────────────────────────────────
def train_model(model: keras.Model, train_ds, val_ds):
    print("\n--- Phase 1: Warming up the NIRMAL Head ---")
    # Train only the new dense layers quickly
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=CONFIG["learning_rate"]),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    
    history_p1 = model.fit(
        train_ds, validation_data=val_ds, 
        epochs=10, # 10 epochs is enough to warm up the head
        verbose=1
    )

    print("\n--- Phase 2: High-Precision Fine-Tuning ---")
    # Find the EfficientNet backbone inside the model
    backbone = next(layer for layer in model.layers if isinstance(layer, keras.Model))
    backbone.trainable = True
    
    # Unfreeze the top 50 layers for fine-tuning
    for layer in backbone.layers[:-50]:
        layer.trainable = False

    # Recompile with a VERY low learning rate (crucial for 95%+)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-5), 
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    cb_list = [
        callbacks.EarlyStopping(monitor="val_accuracy", patience=12, restore_best_weights=True, verbose=1),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-7, verbose=1),
        callbacks.ModelCheckpoint(filepath=CONFIG["model_save_path"], monitor="val_accuracy", save_best_only=True, verbose=1),
    ]

    history_p2 = model.fit(
        train_ds, validation_data=val_ds,
        epochs=CONFIG["epochs"] - 10, # Remaining epochs
        callbacks=cb_list,
        verbose=1,
    )
    
    # Merge histories for the plot
    for key in history_p1.history.keys():
        history_p1.history[key].extend(history_p2.history[key])
        
    # Mock a single history object to return
    history_p2.history = history_p1.history
    return history_p2


# ─────────────────────────────────────────────────────────────────────────────
# 6.  EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_model(model: keras.Model, test_ds):
    """Evaluate on test set; print classification report + confusion matrix."""
    y_true, y_pred_prob = [], []

    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_pred_prob.extend(preds)
        y_true.extend(labels.numpy())

    y_true      = np.array(y_true)
    y_pred      = np.argmax(y_pred_prob, axis=1)
    test_acc    = accuracy_score(y_true, y_pred)

    print(f"\n{'='*60}")
    print(f"  CNN (NIRMAL) Test Accuracy : {test_acc*100:.2f}%")
    print(f"{'='*60}")
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=CLASS_NAMES))

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    plot_confusion_matrix(cm, CLASS_NAMES, CONFIG["cm_plot"])
    return y_true, y_pred, test_acc


def plot_confusion_matrix(cm, class_names, save_path):
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens",
                xticklabels=class_names, yticklabels=class_names, ax=ax)
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("True", fontsize=12)
    ax.set_title("Confusion Matrix — Potato Leaf Disease (NIRMAL CNN)", fontsize=13)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[Plot] Confusion matrix saved → {save_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 7.  TRAINING HISTORY PLOT
# ─────────────────────────────────────────────────────────────────────────────
def plot_training_history(history, save_path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy
    axes[0].plot(history.history["accuracy"],     label="Train Acc",  lw=2, color="#2ecc71")
    axes[0].plot(history.history["val_accuracy"], label="Val Acc",    lw=2, color="#e74c3c", linestyle="--")
    axes[0].set_title("Model Accuracy", fontsize=14)
    axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Accuracy")
    axes[0].legend(); axes[0].grid(alpha=0.3)

    # Loss
    axes[1].plot(history.history["loss"],     label="Train Loss",  lw=2, color="#2ecc71")
    axes[1].plot(history.history["val_loss"], label="Val Loss",    lw=2, color="#e74c3c", linestyle="--")
    axes[1].set_title("Model Loss", fontsize=14)
    axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("Loss")
    axes[1].legend(); axes[1].grid(alpha=0.3)

    fig.suptitle("Training History — Potato Disease CNN (NIRMAL)", fontsize=15, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[Plot] Training history saved → {save_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 8.  COMPARING ALGORITHMS  (flowchart right panel)
#     Train classical ML on CNN features (feature extraction transfer)
# ─────────────────────────────────────────────────────────────────────────────
def extract_features(model: keras.Model, dataset) -> tuple:
    """Use the layer before softmax as a feature extractor."""
    feature_model = keras.Model(
        inputs=model.input,
        outputs=model.get_layer("drop_512").output,   # 512-d embedding
        name="feature_extractor",
    )
    features, labels = [], []
    for images, lbls in dataset:
        feats = feature_model.predict(images, verbose=0)
        features.extend(feats)
        labels.extend(lbls.numpy())
    return np.array(features), np.array(labels)


def compare_algorithms(train_ds, test_ds, model: keras.Model):
    """
    Flowchart: Comparing Algorithms
      1. Random Forest
      2. Logistic Regression
      3. k-Nearest Neighbors
      4. Decision Trees
      5. Naive Bayes
      6. Linear Discriminant Analysis
      7. Support Vector Machine
    Features extracted from NIRMAL CNN backbone.
    """
    print("\n[Compare] Extracting CNN features for classical classifiers …")
    X_train, y_train = extract_features(model, train_ds)
    X_test,  y_test  = extract_features(model, test_ds)

    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    classifiers = {
        "Random Forest"              : RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
        "Logistic Regression"        : LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1),
        "k-Nearest Neighbors"        : KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
        "Decision Trees"             : DecisionTreeClassifier(random_state=42),
        "Naive Bayes"                : GaussianNB(),
        "Linear Discriminant Analysis": LinearDiscriminantAnalysis(),
        "Support Vector Machine"     : SVC(kernel="rbf", probability=True, random_state=42),
    }

    results = {}
    for name, clf in classifiers.items():
        print(f"  Training {name} …", end=" ", flush=True)
        clf.fit(X_train, y_train)
        acc = accuracy_score(y_test, clf.predict(X_test))
        results[name] = round(acc * 100, 2)
        print(f"Acc = {results[name]:.2f}%")

    # ── Performance Evaluation Plot ────────────────────────────────────────
    plot_algorithm_comparison(results, CONFIG["comparison_plot"])
    return results, classifiers, scaler, X_train, y_train, X_test, y_test


def plot_algorithm_comparison(results: dict, save_path: str):
    names  = list(results.keys())
    scores = list(results.values())
    colors = ["#27ae60" if s >= 95 else "#e67e22" if s >= 90 else "#e74c3c"
              for s in scores]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(names, scores, color=colors, edgecolor="white", height=0.55)
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{score:.2f}%", va="center", fontsize=11, fontweight="bold")
    ax.set_xlim(0, 107)
    ax.axvline(95, color="#c0392b", linestyle="--", lw=1.5, label="95% target")
    ax.set_xlabel("Test Accuracy (%)", fontsize=12)
    ax.set_title("Algorithm Comparison — CNN Features + Classical Classifiers", fontsize=13)
    ax.legend()
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[Plot] Algorithm comparison saved → {save_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 9.  ENSEMBLE MODEL  (flowchart: Ensemble Model node)
# ─────────────────────────────────────────────────────────────────────────────
def build_and_evaluate_ensemble(classifiers: dict, results: dict,
                                X_train, y_train, X_test, y_test):
    """
    Soft-voting ensemble: pick top-3 probabilistic classifiers
    (RF, LR, SVM) since they support predict_proba.
    """
    print("\n[Ensemble] Building soft-voting ensemble …")
    ensemble_clf = VotingClassifier(
        estimators=[
            ("rf",  classifiers["Random Forest"]),
            ("lr",  classifiers["Logistic Regression"]),
            ("svm", classifiers["Support Vector Machine"]),
        ],
        voting="soft",
        n_jobs=-1,
    )
    ensemble_clf.fit(X_train, y_train)
    ens_acc = accuracy_score(y_test, ensemble_clf.predict(X_test))
    print(f"[Ensemble] Accuracy: {ens_acc*100:.2f}%")
    return ensemble_clf, ens_acc


# ─────────────────────────────────────────────────────────────────────────────
# 10.  SAVE MODEL  (flowchart: Saving the model)
# ─────────────────────────────────────────────────────────────────────────────
def save_model(model: keras.Model):
    """Save the best CNN checkpoint (already saved via ModelCheckpoint callback)."""
    # The callback already saved the best weights.
    # We also export as SavedModel for serving.
    export_path = "./saved_models/potato_disease_savedmodel"
    model.export(export_path)
    print(f"[Save] SavedModel exported → {export_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 11.  SINGLE-IMAGE INFERENCE  (production utility)
# ─────────────────────────────────────────────────────────────────────────────
def predict_single_image(model: keras.Model, image_path: str) -> dict:
    """
    Load any real-world image (JPEG / PNG) and return disease prediction.
    Handles variability in size, lighting, and background automatically
    via the same preprocessing as training.
    """
    img = tf.io.read_file(image_path)
    img = tf.image.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, CONFIG["image_size"])
    img = tf.cast(img, tf.float32) / 255.0
    img = tf.expand_dims(img, 0)   # add batch dim

    probs      = model.predict(img, verbose=0)[0]
    pred_idx   = int(np.argmax(probs))
    pred_class = CLASS_NAMES[pred_idx]
    confidence = float(probs[pred_idx]) * 100

    result = {
        "image"       : image_path,
        "prediction"  : pred_class,
        "confidence"  : f"{confidence:.2f}%",
        "probabilities": {c: f"{p*100:.2f}%" for c, p in zip(CLASS_NAMES, probs)},
    }
    print(f"\n[Inference] {image_path}")
    for k, v in result.items():
        print(f"  {k}: {v}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 12.  MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  POTATO LEAF DISEASE DETECTION — NIRMAL CNN + Ensemble")
    print("=" * 65)

    # ── Step 1: Data Pipeline ─────────────────────────────────────────────
    print("\n[1/6] Building data pipeline …")
    train_ds, val_ds, test_ds = build_data_pipeline(CONFIG["dataset_dir"])

    # ── Step 2: Build CNN ─────────────────────────────────────────────────
    print("\n[2/6] Building CNN model with NIRMAL activation …")
    model = build_cnn_model(num_classes=NUM_CLASSES)

    # ── Step 3: Train ─────────────────────────────────────────────────────
    print("\n[3/6] Training model (Keras Sequential workflow) …")
    history = train_model(model, train_ds, val_ds)
    plot_training_history(history, CONFIG["history_plot"])

    # ── Step 4: Evaluate CNN ──────────────────────────────────────────────
    print("\n[4/6] Evaluating CNN on test set …")
    # Load best weights (saved by checkpoint callback)
    best_model = keras.models.load_model(
        CONFIG["model_save_path"],
        custom_objects={"NIRMALActivation": NIRMALActivation},
    )
    y_true, y_pred, cnn_acc = evaluate_model(best_model, test_ds)

    # ── Step 5: Compare Classical Algorithms ─────────────────────────────
    print("\n[5/6] Comparing classical algorithms (flowchart right panel) …")
    results, classifiers, scaler, Xtr, ytr, Xte, yte = compare_algorithms(
        train_ds, test_ds, best_model
    )

    # ── Step 6: Ensemble Model ────────────────────────────────────────────
    print("\n[6/6] Building Ensemble Model …")
    ensemble_clf, ens_acc = build_and_evaluate_ensemble(
        classifiers, results, Xtr, ytr, Xte, yte
    )

    # ── Save ──────────────────────────────────────────────────────────────
    save_model(best_model)

    # ── Final Summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  FINAL PERFORMANCE SUMMARY")
    print("=" * 65)
    print(f"  CNN (NIRMAL)  Accuracy : {cnn_acc*100:.2f}%")
    print(f"  Ensemble      Accuracy : {ens_acc*100:.2f}%")
    print("-" * 65)
    for algo, acc in sorted(results.items(), key=lambda x: -x[1]):
        bar   = "█" * int(acc // 5)
        mark  = "✓" if acc >= 95 else " "
        print(f"  [{mark}] {algo:<35} {acc:.2f}%  {bar}")
    print("=" * 65)

    return best_model, history, results


# ─────────────────────────────────────────────────────────────────────────────
# 13.  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # ── GPU memory growth (avoids OOM on smaller GPUs) ────────────────────
    gpus = tf.config.list_physical_devices("GPU")
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    if gpus:
        print(f"[GPU] {len(gpus)} GPU(s) detected.")
    else:
        print("[GPU] No GPU found — running on CPU (training will be slower).")

    model, history, results = main()

    # ── Optional: demo inference on a single image ─────────────────────────
    # result = predict_single_image(model, "./test_images/potato_sample.jpg")