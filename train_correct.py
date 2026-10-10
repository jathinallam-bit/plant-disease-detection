# train_correct.py - Corrected to use the actual disease classes
import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from datetime import datetime

print("🌱 Plant Disease Detection - Training (Corrected)")
print("=" * 60)
print(f"🐍 TensorFlow version: {tf.__version__}")

# Correct path - the disease classes are inside train/ and valid/
base_path = "dataset/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)"

if not os.path.exists(base_path):
    print("❌ Dataset not found!")
    exit()

train_path = os.path.join(base_path, 'train')
valid_path = os.path.join(base_path, 'valid')

if not os.path.exists(train_path):
    print(f"❌ Train folder not found at: {train_path}")
    exit()

# Get the actual disease classes from the train folder
classes = [d for d in os.listdir(train_path) if os.path.isdir(os.path.join(train_path, d))]
print(f"📋 Found {len(classes)} disease classes!")

if len(classes) == 0:
    print("❌ No class folders found! Please check the dataset structure.")
    exit()

print(f"📋 First 5 classes: {classes[:5]}")

# Configuration
IMAGE_SIZE = (128, 128)  # Smaller = faster
BATCH_SIZE = 64
EPOCHS = 13

print(f"\n📊 Training Configuration:")
print(f"   Classes: {len(classes)}")
print(f"   Image Size: {IMAGE_SIZE}")
print(f"   Batch Size: {BATCH_SIZE}")
print(f"   Epochs: {EPOCHS}")

# Data augmentation
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

val_datagen = ImageDataGenerator(rescale=1./255)

# Create generators from the train and valid folders
train_generator = train_datagen.flow_from_directory(
    train_path,  # This should contain the disease class folders
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=True
)

validation_generator = val_datagen.flow_from_directory(
    valid_path,  # This should contain the disease class folders
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)

print(f"\n✅ Training samples: {train_generator.samples:,}")
print(f"✅ Validation samples: {validation_generator.samples:,}")

# Save labels
os.makedirs('models', exist_ok=True)
with open('models/labels.json', 'w') as f:
    json.dump(train_generator.class_indices, f)
print(f"✅ Labels saved to models/labels.json")
print(f"   Labels: {train_generator.class_indices}")

# Build model
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(*IMAGE_SIZE, 3)),
    layers.MaxPooling2D(2, 2),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D(2, 2),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D(2, 2),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D(2, 2),
    layers.Flatten(),
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(len(classes), activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print("\n🏗️ Model Summary:")
model.summary()

# Callbacks
callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=3, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=2, min_lr=0.0001),
    ModelCheckpoint('models/plant_disease_model.h5', monitor='val_accuracy', save_best_only=True, verbose=1)
]

# Train
print("\n🚀 Starting training...")
print(f"📊 Training on {train_generator.samples:,} images across {len(classes)} classes")
print("=" * 60)

start_time = datetime.now()

history = model.fit(
    train_generator,
    epochs=EPOCHS,
    validation_data=validation_generator,
    callbacks=callbacks,
    verbose=1
)

# Evaluate
print("\n📊 Evaluating model...")
loss, accuracy = model.evaluate(validation_generator)
print(f"✅ Validation Accuracy: {accuracy*100:.2f}%")

# Save final model
model.save('models/plant_disease_model.h5')
print("✅ Model saved to models/plant_disease_model.h5")

elapsed = datetime.now() - start_time
print(f"\n⏱️ Total training time: {elapsed}")

print("\n" + "=" * 60)
print("✅ Training Complete!")
print(f"🎯 Accuracy: {accuracy*100:.2f}%")
print(f"📁 Model: models/plant_disease_model.h5")
print("=" * 60)