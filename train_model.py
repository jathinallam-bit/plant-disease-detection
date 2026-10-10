# train_model.py - Complete working version
import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from datetime import datetime

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

print("🌱 Plant Disease Detection - Training")
print("=" * 60)
print(f"🐍 TensorFlow version: {tf.__version__}")

# Find the actual dataset path
possible_paths = [
    "dataset/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)",
    "dataset/New Plant Diseases Dataset(Augmented)",
    "dataset"
]

base_path = None
for path in possible_paths:
    if os.path.exists(path):
        # Check if it contains class folders
        folders = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        if folders:
            base_path = path
            print(f"✅ Found dataset at: {base_path}")
            print(f"📋 Found {len(folders)} class folders")
            break

if not base_path:
    print("❌ Dataset not found!")
    print("   Please make sure your dataset is in the 'dataset' folder.")
    exit()

# Get all class folders
classes = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
print(f"📋 Sample classes: {classes[:5]}...")

if len(classes) == 0:
    print("❌ No class folders found!")
    exit()

# Configuration
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10  # Start with 10 epochs (increase for better accuracy)

# Data augmentation for better generalization
datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2  # 20% for validation
)

# Create generators
print("\n📊 Creating data generators...")
train_generator = datagen.flow_from_directory(
    base_path,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True
)

validation_generator = datagen.flow_from_directory(
    base_path,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False
)

print(f"✅ Training samples: {train_generator.samples}")
print(f"✅ Validation samples: {validation_generator.samples}")

# Save labels for later use
os.makedirs('models', exist_ok=True)
with open('models/labels.json', 'w') as f:
    json.dump(train_generator.class_indices, f)
print(f"✅ Labels saved to models/labels.json")

# Build the model
print("\n🏗️ Building model...")
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

print("\n📋 Model Summary:")
model.summary()

# Callbacks for better training
callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=0.00001),
    ModelCheckpoint('models/plant_disease_model.h5', monitor='val_accuracy', save_best_only=True, verbose=1)
]

# Train
print("\n🚀 Starting training...")
print(f"📊 Epochs: {EPOCHS}")
print(f"📦 Batch size: {BATCH_SIZE}")
print(f"📁 Training on {train_generator.samples} images")
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
print(f"✅ Validation Loss: {loss:.4f}")

# Save final model
model.save('models/plant_disease_model_final.h5')
print("✅ Model saved to models/plant_disease_model_final.h5")

# Time taken
elapsed = datetime.now() - start_time
print(f"\n⏱️ Training time: {elapsed}")

print("\n" + "=" * 60)
print("✅ Training Complete!")
print(f"🎯 Validation Accuracy: {accuracy*100:.2f}%")
print("📁 Best model: models/plant_disease_model.h5")
print("📋 Labels: models/labels.json")
print("=" * 60)

# Save training history
import matplotlib.pyplot as plt
try:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    ax1.plot(history.history['accuracy'], label='Training')
    ax1.plot(history.history['val_accuracy'], label='Validation')
    ax1.set_title('Model Accuracy')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(history.history['loss'], label='Training')
    ax2.plot(history.history['val_loss'], label='Validation')
    ax2.set_title('Model Loss')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('models/training_history.png')
    print("📊 Training history saved to models/training_history.png")
except:
    print("⚠️ Could not save training plot")