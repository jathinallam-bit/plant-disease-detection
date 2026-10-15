# ai_model.py
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os

class PlantDiseaseDetector:
    def __init__(self, model_path=None):
        self.model = None
        if model_path and os.path.exists(model_path):
            self.model = load_model(model_path)
    
    def predict(self, image_path):
        """Predict plant disease from image"""
        if self.model is None:
            # Fallback to mock data
            return self._mock_predict()
        
        # Load and preprocess image
        img = image.load_img(image_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0
        
        # Get prediction
        predictions = self.model.predict(img_array)
        return self._process_predictions(predictions)
    
    def _mock_predict(self):
        """Mock prediction when model not available"""
        diseases = ['Healthy Plant', 'Leaf Blight', 'Powdery Mildew', 'Root Rot']
        import random
        return {
            'disease': random.choice(diseases),
            'confidence': random.uniform(75, 98),
            'severity': random.choice(['LOW', 'MEDIUM', 'HIGH'])
        }