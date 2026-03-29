import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.utils.class_weight import compute_class_weight

# --- 1. CONFIGURATION ---
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
DATASET_PATH = r"C:\Users\ISHITA DAS\.cache\kagglehub\datasets\warcoder\potato-leaf-disease-dataset\versions\1\Potato Leaf Disease Dataset in Uncontrolled Environment"

IMG_SIZE = 224
BATCH_SIZE = 32
INITIAL_EPOCHS = 15
FINE_TUNE_EPOCHS = 25

# --- 2. DATA LOADING & PREPARATION ---
# label_mode='categorical' automatically handles one-hot encoding
train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode='categorical'
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    label_mode='categorical'
)

class_names = train_ds.class_names
print(f"Detected Classes: {class_names}")

# --- 3. COMPUTE CLASS WEIGHTS ---
# Helps the model focus on minority classes (crucial for production)
print("Calculating class weights...")
y_train = np.concatenate([y for x, y in train_ds], axis=0)
y_integers = np.argmax(y_train, axis=1)
weights = compute_class_weight('balanced', classes=np.unique(y_integers), y=y_integers)
class_weight_dict = dict(enumerate(weights))

# Optimize performance
train_ds = train_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=tf.data.AUTOTUNE)

# --- 4. PRODUCTION AUGMENTATION & MODEL ---
# Added brightness and contrast to handle "uncontrolled environment"
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomZoom(0.2),
    layers.RandomContrast(0.2),
    layers.RandomBrightness(0.1),
])

# Use EfficientNetV2-S for better accuracy/speed trade-off
base_model = tf.keras.applications.EfficientNetV2S(
    weights="imagenet",
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)
base_model.trainable = False  # Initially frozen

inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x = data_augmentation(inputs)
x = tf.keras.applications.efficientnet_v2.preprocess_input(x)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.BatchNormalization()(x)
x = layers.Dense(256, activation="relu")(x)
x = layers.Dropout(0.4)(x) 
outputs = layers.Dense(len(class_names), activation="softmax")(x)

model = models.Model(inputs, outputs)

# --- 5. COMPILE & PHASE 1 (WARM-UP) ---
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
    metrics=["accuracy", tf.keras.metrics.Precision(name='precision'), tf.keras.metrics.Recall(name='recall')]
)

callbacks = [
    EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
    ModelCheckpoint("best_potato_model.keras", monitor="val_accuracy", save_best_only=True),
    ReduceLROnPlateau(monitor="val_loss", factor=0.2, patience=3, min_lr=1e-7)
]

print("\n--- Phase 1: Training the Classification Head ---")
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=INITIAL_EPOCHS,
    callbacks=callbacks,
    class_weight=class_weight_dict
)

# --- 6. PHASE 2: FINE-TUNING (UNFREEZING) ---
# Unfreeze the top layers of the base model
print("\n--- Phase 2: Fine-Tuning the Base Model ---")
base_model.trainable = True

# We only unfreeze the last 50 layers to avoid over-fitting
for layer in base_model.layers[:-50]:
    layer.trainable = False

# Recompile with a MUCH smaller learning rate
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
    metrics=["accuracy", "precision", "recall"]
)

total_epochs = INITIAL_EPOCHS + FINE_TUNE_EPOCHS
history_fine = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=total_epochs,
    initial_epoch=history.epoch[-1],
    callbacks=callbacks,
    class_weight=class_weight_dict
)

# --- 7. FINAL EXPORT ---
model.save("potato_leaf_prod_v1.keras")
print("\nFinal Validation Accuracy:", history_fine.history['val_accuracy'][-1])
print("Final Validation Recall (Production Metric):", history_fine.history['val_recall'][-1])