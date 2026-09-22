import os
import json
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.models import Model
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

# ==========================
# DATASET PATH
# ==========================

DATASET_PATH = r"G:\My Drive\archive (2)\Fruits_Vegetables_Dataset(12000)\Vegetables\tomato"

IMG_SIZE = (224,224)
BATCH_SIZE = 32
SEED = 42

# ==========================
# LOAD DATASET
# ==========================

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

class_names = train_ds.class_names

print("\nClasses:")
print(class_names)

# Save class names
with open("class_names.json","w") as f:
    json.dump(class_names,f)

AUTOTUNE=tf.data.AUTOTUNE

train_ds=train_ds.prefetch(AUTOTUNE)
val_ds=val_ds.prefetch(AUTOTUNE)

# ==========================
# DATA AUGMENTATION
# ==========================

data_augmentation=tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.15),
    layers.RandomZoom(0.15),
    layers.RandomContrast(0.15),
])

# ==========================
# BASE MODEL
# ==========================

base_model=EfficientNetB0(
    include_top=False,
    weights="imagenet",
    input_shape=(224,224,3)
)

base_model.trainable=False

inputs=tf.keras.Input(shape=(224,224,3))

x=data_augmentation(inputs)

x=preprocess_input(x)

x=base_model(x,training=False)

x=layers.GlobalAveragePooling2D()(x)

x=layers.Dropout(0.3)(x)

outputs=layers.Dense(2,activation="softmax")(x)

model=Model(inputs,outputs)

# ==========================
# COMPILE
# ==========================

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-4),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# ==========================
# CALLBACKS
# ==========================

os.makedirs("model",exist_ok=True)

callbacks=[

    EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    ),

    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=2
    ),

    ModelCheckpoint(
        "model/tomato_best.keras",
        monitor="val_accuracy",
        save_best_only=True
    )

]

# ==========================
# TRAIN
# ==========================

history=model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=50,

    callbacks=callbacks

)

print("\nFirst stage completed.")