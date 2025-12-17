"""
Fusion Logic - Combines Sensor and Camera models based on selected mode
Implements 4 modes: Sensor Only, Camera Only, Auto Smart, and Fusion
"""
import logging
from typing import Tuple, List, Dict, Optional
import numpy as np

from models.sensor_model import get_sensor_model
from models.camera_model import get_camera_model
import config

logger = logging.getLogger(__name__)


class FusionLogic:
    """Handles fusion of sensor and camera predictions based on mode"""
    
    def __init__(self):
        """Initialize fusion logic"""
        self.sensor_model = get_sensor_model()
        self.camera_model = get_camera_model()
        
        # Load configuration
        self.mode = config.DEFAULT_MODE
        self.auto_threshold = config.DEFAULT_AUTO_THRESHOLD
        self.fusion_weights = config.DEFAULT_FUSION_WEIGHTS
    
    def update_config(self, mode: str = None, auto_threshold: float = None, 
                     fusion_weights: Dict[str, float] = None):
        """
        Update fusion configuration
        
        Args:
            mode: Detection mode ('sensor_only', 'camera_only', 'auto', 'fusion')
            auto_threshold: Confidence threshold for auto mode
            fusion_weights: Weights for fusion mode {'sensor': float, 'camera': float}
        """
        if mode:
            self.mode = mode
        if auto_threshold is not None:
            self.auto_threshold = auto_threshold
        if fusion_weights:
            self.fusion_weights = fusion_weights
        
        logger.info(f"Fusion config updated: mode={self.mode}, threshold={self.auto_threshold}")
    
    def predict_sensor_only(self, sensor_values: List[float]) -> Tuple[str, float, Dict]:
        """
        Mode 1: Sensor Only
        Only use sensor data for prediction
        
        Args:
            sensor_values: List of 7 sensor values
        
        Returns:
            Tuple of (label, confidence, metadata)
        """
        try:
            label, confidence = self.sensor_model.predict(sensor_values)
            
            metadata = {
                'mode': 'sensor_only',
                'sensor_confidence': confidence,
                'camera_used': False
            }
            
            logger.info(f"Sensor Only: {label} (confidence: {confidence:.2f})")
            return label, confidence, metadata
            
        except Exception as e:
            logger.error(f"Sensor prediction failed: {e}")
            raise
    
    def predict_camera_only(self, camera_frame: np.ndarray) -> Tuple[str, float, Dict]:
        """
        Mode 2: Camera Only
        Only use camera for prediction, ignore sensor data
        
        Args:
            camera_frame: BGR image from camera
        
        Returns:
            Tuple of (label, confidence, metadata)
        """
        try:
            if camera_frame is None:
                logger.error("Camera Only mode: no camera frame provided")
                raise ValueError("Camera frame is required for camera_only mode")
            
            label, confidence = self.camera_model.predict(camera_frame)
            
            metadata = {
                'mode': 'camera_only',
                'camera_confidence': confidence,
                'camera_used': True
            }
            
            logger.info(f"Camera Only: {label} (confidence: {confidence:.2f})")
            return label, confidence, metadata
            
        except Exception as e:
            logger.error(f"Camera prediction failed: {e}")
            raise
    
    def predict_auto(self, sensor_values: List[float], camera_frame: np.ndarray = None) -> Tuple[str, float, Dict]:
        """
        Mode 2: Auto Smart
        Use sensor first, if confidence < threshold then use camera
        
        Args:
            sensor_values: List of 7 sensor values
            camera_frame: BGR image from camera (optional, required if sensor confidence is low)
        
        Returns:
            Tuple of (label, confidence, metadata)
        """
        try:
            # First, try sensor
            sensor_label, sensor_confidence = self.sensor_model.predict(sensor_values)
            
            metadata = {
                'mode': 'auto',
                'sensor_confidence': sensor_confidence,
                'sensor_label': sensor_label
            }
            
            # Check if sensor confidence is high enough
            if sensor_confidence >= self.auto_threshold:
                metadata['camera_used'] = False
                logger.info(f"Auto (Sensor): {sensor_label} (confidence: {sensor_confidence:.2f})")
                return sensor_label, sensor_confidence, metadata
            
            # Sensor confidence is low, use camera
            if camera_frame is None:
                logger.warning("Auto mode: sensor confidence low but no camera frame provided")
                metadata['camera_used'] = False
                return sensor_label, sensor_confidence, metadata
            
            try:
                camera_label, camera_confidence = self.camera_model.predict(camera_frame)
                metadata['camera_used'] = True
                metadata['camera_confidence'] = camera_confidence
                metadata['camera_label'] = camera_label
                
                logger.info(f"Auto (Camera): {camera_label} (confidence: {camera_confidence:.2f})")
                return camera_label, camera_confidence, metadata
                
            except Exception as e:
                logger.error(f"Camera prediction failed in auto mode: {e}")
                # Fallback to sensor prediction
                metadata['camera_used'] = False
                metadata['camera_error'] = str(e)
                return sensor_label, sensor_confidence, metadata
            
        except Exception as e:
            logger.error(f"Auto prediction failed: {e}")
            raise
    
    def predict_fusion(self, sensor_values: List[float], camera_frame: np.ndarray) -> Tuple[str, float, Dict]:
        """
        Mode 3: Fusion
        Combine both sensor and camera predictions using weighted voting
        
        Args:
            sensor_values: List of 7 sensor values
            camera_frame: BGR image from camera
        
        Returns:
            Tuple of (label, confidence, metadata)
        """
        try:
            # Get predictions from both models
            sensor_label, sensor_confidence = self.sensor_model.predict(sensor_values)
            
            metadata = {
                'mode': 'fusion',
                'sensor_label': sensor_label,
                'sensor_confidence': sensor_confidence,
                'camera_used': True
            }
            
            # Log camera frame info
            if camera_frame is not None:
                logger.info(f"Camera frame available: shape={camera_frame.shape}, dtype={camera_frame.dtype}")
            else:
                logger.warning("Camera frame is None in fusion mode!")
            
            try:
                logger.info("Calling camera model prediction...")
                camera_label, camera_confidence = self.camera_model.predict(camera_frame)
                logger.info(f"Camera prediction successful: {camera_label} ({camera_confidence:.2f})")
                metadata['camera_label'] = camera_label
                metadata['camera_confidence'] = camera_confidence
            except Exception as e:
                logger.error(f"Camera prediction failed in fusion mode: {e}", exc_info=True)
                # Fallback to sensor only
                metadata['camera_used'] = False
                metadata['camera_error'] = str(e)
                return sensor_label, sensor_confidence, metadata
            
            # Get probability distributions
            sensor_probs = self.sensor_model.get_all_probabilities(sensor_values)
            camera_probs = self.camera_model.get_all_probabilities(camera_frame)
            
            # Weighted fusion
            sensor_weight = self.fusion_weights.get('sensor', 0.4)
            camera_weight = self.fusion_weights.get('camera', 0.6)
            
            # Combine probabilities
            all_labels = set(sensor_probs.keys()) | set(camera_probs.keys())
            fused_probs = {}
            
            for label in all_labels:
                sensor_prob = sensor_probs.get(label, 0.0)
                camera_prob = camera_probs.get(label, 0.0)
                fused_probs[label] = (sensor_weight * sensor_prob) + (camera_weight * camera_prob)
            
            # Get final prediction
            final_label = max(fused_probs, key=fused_probs.get)
            final_confidence = fused_probs[final_label]
            
            metadata['fused_label'] = final_label
            metadata['fused_confidence'] = final_confidence
            metadata['weights'] = {'sensor': sensor_weight, 'camera': camera_weight}
            
            logger.info(f"Fusion: {final_label} (confidence: {final_confidence:.2f})")
            logger.debug(f"  Sensor: {sensor_label} ({sensor_confidence:.2f})")
            logger.debug(f"  Camera: {camera_label} ({camera_confidence:.2f})")
            
            return final_label, final_confidence, metadata
            
        except Exception as e:
            logger.error(f"Fusion prediction failed: {e}")
            raise
    
    def predict(self, sensor_values: List[float], camera_frame: np.ndarray = None) -> Tuple[str, float, Dict]:
        """
        Main prediction method - routes to appropriate mode
        
        Args:
            sensor_values: List of 7 sensor values
            camera_frame: BGR image from camera (optional, depends on mode)
        
        Returns:
            Tuple of (label, confidence, metadata)
        """
        if self.mode == 'sensor_only':
            return self.predict_sensor_only(sensor_values)
        
        elif self.mode == 'camera_only':
            if camera_frame is None:
                logger.warning("Camera Only mode requires camera frame, falling back to sensor only")
                return self.predict_sensor_only(sensor_values)
            return self.predict_camera_only(camera_frame)
        
        elif self.mode == 'auto':
            return self.predict_auto(sensor_values, camera_frame)
        
        elif self.mode == 'fusion':
            if camera_frame is None:
                logger.warning("Fusion mode requires camera frame, falling back to sensor only")
                return self.predict_sensor_only(sensor_values)
            return self.predict_fusion(sensor_values, camera_frame)
        
        else:
            logger.error(f"Unknown mode: {self.mode}, using sensor_only")
            return self.predict_sensor_only(sensor_values)
    
    def is_bad_posture(self, label: str) -> bool:
        """
        Check if the predicted posture is bad
        
        Args:
            label: Posture label
        
        Returns:
            True if bad posture, False otherwise
        """
        return label in config.BAD_POSTURES


# Singleton instance
_fusion_logic_instance = None


def get_fusion_logic() -> FusionLogic:
    """
    Get singleton instance of FusionLogic
    
    Returns:
        FusionLogic instance
    """
    global _fusion_logic_instance
    if _fusion_logic_instance is None:
        _fusion_logic_instance = FusionLogic()
    return _fusion_logic_instance
