# predictor.py
import os
import json
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

class PlantDiseasePredictor:
    """Plant Disease Prediction Class"""
    
    def __init__(self, model_path='models/plant_disease_model.h5', labels_path='models/labels.json'):
        """Initialize the predictor"""
        self.model = None
        self.labels = None
        self.class_names = {}
        self.image_size = (224, 224)
        
        # Load model if exists
        if os.path.exists(model_path):
            try:
                self.model = load_model(model_path)
                print(f"✅ Model loaded from {model_path}")
            except Exception as e:
                print(f"⚠️ Error loading model: {e}")
                self.model = None
        else:
            print(f"⚠️ Model not found at {model_path}")
            print("   Using mock predictions for demonstration")
        
        # Load labels
        if os.path.exists(labels_path):
            try:
                with open(labels_path, 'r') as f:
                    self.labels = json.load(f)
                self.class_names = {v: k for k, v in self.labels.items()}
                print(f"✅ Labels loaded: {len(self.labels)} classes")
            except Exception as e:
                print(f"⚠️ Error loading labels: {e}")
                self.labels = {}
                self.class_names = {}
        else:
            print(f"⚠️ Labels not found at {labels_path}")
            self.labels = {}
            self.class_names = {}
    
    def preprocess_image(self, image_path):
        """Preprocess image for prediction"""
        try:
            # Load and resize image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img = img.resize(self.image_size)
            img_array = img_to_array(img)
            img_array = img_array / 255.0  # Normalize
            img_array = np.expand_dims(img_array, axis=0)
            return img_array
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def predict(self, image_path):
        """Predict disease from image"""
        # If model is not loaded, use mock prediction
        if self.model is None or not self.labels:
            return self._mock_predict()
        
        # Preprocess image
        img_array = self.preprocess_image(image_path)
        if img_array is None:
            return self._mock_predict()
        
        try:
            # Make prediction
            predictions = self.model.predict(img_array, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = np.max(predictions[0]) * 100
            
            # Get disease name
            disease_name = self.class_names.get(predicted_class, 'Unknown Disease')
            
            return {
                'disease': disease_name,
                'confidence': float(confidence),
                'class_id': predicted_class,
                'all_predictions': {self.class_names.get(i, 'Unknown'): float(predictions[0][i] * 100) 
                                   for i in range(len(predictions[0]))}
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return self._mock_predict()
    
    def _mock_predict(self):
        """Mock prediction when model not available"""
        import random
        diseases = [
            'Leaf Blight', 'Powdery Mildew', 'Root Rot',
            'Bacterial Spot', 'Healthy Plant', 'Nutrient Deficiency'
        ]
        disease = random.choice(diseases)
        confidence = random.uniform(70, 98)
        return {
            'disease': disease,
            'confidence': confidence,
            'class_id': -1,
            'all_predictions': {}
        }