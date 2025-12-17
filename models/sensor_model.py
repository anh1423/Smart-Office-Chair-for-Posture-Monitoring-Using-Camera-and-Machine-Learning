"""
Sensor Model Wrapper
Loads and uses the Random Forest model trained on 7 pressure sensors
"""
import numpy as np
import joblib
import logging
from pathlib import Path
from typing import Tuple, List

import config

logger = logging.getLogger(__name__)


class SensorModel:
    """Wrapper for sensor-based posture recognition model"""
    
    def __init__(self, model_path: Path = None, encoder_path: Path = None):
        """
        Initialize sensor model
        
        Args:
            model_path: Path to trained Random Forest model (.pkl)
            encoder_path: Path to label encoder (.pkl)
        """
        self.model_path = model_path or config.SENSOR_MODEL_PATH
        self.encoder_path = encoder_path or config.SENSOR_ENCODER_PATH
        
        self.model = None
        self.label_encoder = None
        self.is_loaded = False
        
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and label encoder"""
        try:
            # Check if files exist
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            if not self.encoder_path.exists():
                raise FileNotFoundError(f"Encoder file not found: {self.encoder_path}")
            
            # Load model and encoder
            self.model = joblib.load(self.model_path)
            self.label_encoder = joblib.load(self.encoder_path)
            
            self.is_loaded = True
            logger.info(f"Sensor model loaded successfully from {self.model_path}")
            logger.info(f"Classes: {list(self.label_encoder.classes_)}")
            
        except Exception as e:
            logger.error(f"Failed to load sensor model: {e}")
            self.is_loaded = False
            raise
    
    def predict(self, sensor_values: List[float]) -> Tuple[str, float]:
        """
        Predict posture from sensor values
        
        Args:
            sensor_values: List of 7 sensor values [sensor1, sensor2, ..., sensor7]
        
        Returns:
            Tuple of (predicted_label, confidence_score)
        
        Raises:
            ValueError: If model is not loaded or invalid input
        """
        if not self.is_loaded:
            raise ValueError("Model is not loaded. Cannot make predictions.")
        
        if len(sensor_values) != 7:
            raise ValueError(f"Expected 7 sensor values, got {len(sensor_values)}")
        
        try:
            # Prepare input data
            input_data = np.array([sensor_values])
            
            # Make prediction
            prediction = self.model.predict(input_data)
            probabilities = self.model.predict_proba(input_data)[0]
            
            # Get predicted label and confidence
            predicted_label = self.label_encoder.inverse_transform(prediction)[0]
            confidence = probabilities.max()
            
            logger.debug(f"Sensor prediction: {predicted_label} (confidence: {confidence:.2f})")
            
            return predicted_label, confidence
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
    
    def get_all_probabilities(self, sensor_values: List[float]) -> dict:
        """
        Get probabilities for all posture classes
        
        Args:
            sensor_values: List of 7 sensor values
        
        Returns:
            Dictionary mapping posture labels to probabilities
        """
        if not self.is_loaded:
            raise ValueError("Model is not loaded.")
        
        if len(sensor_values) != 7:
            raise ValueError(f"Expected 7 sensor values, got {len(sensor_values)}")
        
        try:
            input_data = np.array([sensor_values])
            probabilities = self.model.predict_proba(input_data)[0]
            
            # Create dict mapping labels to probabilities
            prob_dict = {
                label: float(prob) 
                for label, prob in zip(self.label_encoder.classes_, probabilities)
            }
            
            return prob_dict
            
        except Exception as e:
            logger.error(f"Failed to get probabilities: {e}")
            raise
    
    def get_classes(self) -> List[str]:
        """
        Get list of all posture classes
        
        Returns:
            List of posture class names
        """
        if not self.is_loaded:
            return []
        return list(self.label_encoder.classes_)


# Singleton instance
_sensor_model_instance = None


def get_sensor_model() -> SensorModel:
    """
    Get singleton instance of SensorModel
    
    Returns:
        SensorModel instance
    """
    global _sensor_model_instance
    if _sensor_model_instance is None:
        _sensor_model_instance = SensorModel()
    return _sensor_model_instance
