"""
Camera Model Wrapper
Uses YOLO for keypoint detection + Random Forest for posture classification
"""
import cv2
import numpy as np
import joblib
import logging
from pathlib import Path
from typing import Tuple, List, Dict
from ultralytics import YOLO

import config

logger = logging.getLogger(__name__)


# YOLO keypoints indices (COCO format)
RELEVANT_KEYPOINTS = [
    0,   # nose
    1, 2,  # eyes
    3, 4,  # ears
    5, 6,  # shoulders
    11, 12,  # hips
    13, 14,  # knees
    15, 16,  # ankles
]


class CameraModel:
    """Wrapper for camera-based posture recognition using YOLO + Random Forest"""
    
    def __init__(self, yolo_path: Path = None, model_path: Path = None, encoder_path: Path = None):
        """
        Initialize camera model
        
        Args:
            yolo_path: Path to YOLO pose model (.pt)
            model_path: Path to trained Random Forest model (.pkl)
            encoder_path: Path to label encoder (.pkl)
        """
        self.yolo_path = yolo_path or config.YOLO_MODEL_PATH
        self.model_path = model_path or config.CAMERA_MODEL_PATH
        self.encoder_path = encoder_path or config.CAMERA_ENCODER_PATH
        
        self.yolo_model = None
        self.rf_model = None
        self.label_encoder = None
        self.is_loaded = False
        
        self._load_models()
    
    def _load_models(self):
        """Load YOLO and Random Forest models"""
        try:
            # Check if files exist
            if not self.yolo_path.exists():
                raise FileNotFoundError(f"YOLO model not found: {self.yolo_path}")
            if not self.model_path.exists():
                raise FileNotFoundError(f"RF model not found: {self.model_path}")
            if not self.encoder_path.exists():
                raise FileNotFoundError(f"Encoder not found: {self.encoder_path}")
            
            # Load YOLO model
            logger.info("Loading YOLO pose model...")
            self.yolo_model = YOLO(str(self.yolo_path))
            
            # Load Random Forest classifier
            logger.info("Loading Random Forest classifier...")
            self.rf_model = joblib.load(self.model_path)
            self.label_encoder = joblib.load(self.encoder_path)
            
            self.is_loaded = True
            logger.info("Camera model loaded successfully")
            logger.info(f"Classes: {list(self.label_encoder.classes_)}")
            
        except Exception as e:
            logger.error(f"Failed to load camera model: {e}")
            self.is_loaded = False
            raise
    
    def _calculate_angle(self, p1, p2, p3):
        """Calculate angle between three points (in degrees)"""
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        return np.degrees(angle)
    
    def _calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _extract_derived_features(self, keypoints):
        """Extract derived features from keypoints"""
        features = {}
        
        nose = keypoints[0]
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        left_hip = keypoints[11]
        right_hip = keypoints[12]
        left_knee = keypoints[13]
        right_knee = keypoints[14]
        left_ankle = keypoints[15]
        right_ankle = keypoints[16]
        
        shoulder_center = [(left_shoulder[0] + right_shoulder[0]) / 2,
                          (left_shoulder[1] + right_shoulder[1]) / 2]
        hip_center = [(left_hip[0] + right_hip[0]) / 2,
                     (left_hip[1] + right_hip[1]) / 2]
        
        # Angles
        features['back_angle'] = self._calculate_angle(nose, shoulder_center, hip_center)
        features['left_knee_angle'] = self._calculate_angle(left_hip, left_knee, left_ankle)
        features['right_knee_angle'] = self._calculate_angle(right_hip, right_knee, right_ankle)
        features['left_hip_angle'] = self._calculate_angle(left_shoulder, left_hip, left_knee)
        features['right_hip_angle'] = self._calculate_angle(right_shoulder, right_hip, right_knee)
        
        # Normalized distances
        torso_length = self._calculate_distance(shoulder_center, hip_center) + 1e-6
        
        features['nose_to_shoulder_dist'] = self._calculate_distance(nose, shoulder_center) / torso_length
        features['shoulder_width'] = self._calculate_distance(left_shoulder, right_shoulder) / torso_length
        features['hip_width'] = self._calculate_distance(left_hip, right_hip) / torso_length
        
        # Asymmetry features
        features['shoulder_y_diff'] = abs(left_shoulder[1] - right_shoulder[1])
        features['shoulder_x_diff'] = abs(left_shoulder[0] - right_shoulder[0])
        features['hip_y_diff'] = abs(left_hip[1] - right_hip[1])
        features['hip_x_diff'] = abs(left_hip[0] - right_hip[0])
        
        # Vertical differences
        features['nose_shoulder_y_diff'] = nose[1] - shoulder_center[1]
        features['shoulder_hip_y_diff'] = shoulder_center[1] - hip_center[1]
        
        # Leg features
        features['knee_distance'] = self._calculate_distance(left_knee, right_knee) / torso_length
        features['ankle_distance'] = self._calculate_distance(left_ankle, right_ankle) / torso_length
        
        # Ratios
        features['knee_ankle_ratio'] = features['knee_distance'] / (features['ankle_distance'] + 1e-6)
        features['shoulder_hip_ratio'] = features['shoulder_width'] / (features['hip_width'] + 1e-6)
        
        return features
    
    def _extract_features(self, keypoints):
        """
        Extract all features from keypoints
        
        Args:
            keypoints: numpy array of shape (17, 2)
        
        Returns:
            numpy array of all features
        """
        features_list = []
        
        # Raw keypoints (only relevant ones)
        for idx in RELEVANT_KEYPOINTS:
            features_list.extend([keypoints[idx, 0], keypoints[idx, 1]])
        
        # Derived features
        derived = self._extract_derived_features(keypoints)
        features_list.extend(derived.values())
        
        return np.array(features_list)
    
    def predict(self, frame: np.ndarray) -> Tuple[str, float]:
        """
        Predict posture from camera frame
        
        Args:
            frame: BGR image from camera (numpy array)
        
        Returns:
            Tuple of (predicted_label, confidence_score)
        
        Raises:
            ValueError: If model is not loaded or no person detected
        """
        if not self.is_loaded:
            raise ValueError("Model is not loaded. Cannot make predictions.")
        
        try:
            # Run YOLO inference
            results = self.yolo_model(frame, verbose=False)
            
            # Check if any person detected
            if len(results[0].keypoints) == 0:
                raise ValueError("No person detected in frame")
            
            # Get keypoints (17, 2)
            keypoints = results[0].keypoints.xy[0].cpu().numpy()
            
            if keypoints.shape[0] != 17:
                raise ValueError(f"Invalid keypoints shape: {keypoints.shape}")
            
            # Extract features
            features = self._extract_features(keypoints)
            features_reshaped = features.reshape(1, -1)
            
            # Make prediction with Random Forest
            prediction = self.rf_model.predict(features_reshaped)
            probabilities = self.rf_model.predict_proba(features_reshaped)[0]
            
            # Get predicted label and confidence
            predicted_label = self.label_encoder.inverse_transform(prediction)[0]
            confidence = probabilities.max()
            
            logger.debug(f"Camera prediction: {predicted_label} (confidence: {confidence:.2f})")
            
            return predicted_label, confidence
            
        except Exception as e:
            logger.error(f"Camera prediction failed: {e}")
            raise
    
    def get_all_probabilities(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Get probabilities for all posture classes
        
        Args:
            frame: BGR image from camera
        
        Returns:
            Dictionary mapping posture labels to probabilities
        """
        if not self.is_loaded:
            raise ValueError("Model is not loaded.")
        
        try:
            # Run YOLO inference
            results = self.yolo_model(frame, verbose=False)
            
            if len(results[0].keypoints) == 0:
                raise ValueError("No person detected in frame")
            
            keypoints = results[0].keypoints.xy[0].cpu().numpy()
            features = self._extract_features(keypoints)
            features_reshaped = features.reshape(1, -1)
            
            # Get probabilities
            probabilities = self.rf_model.predict_proba(features_reshaped)[0]
            
            prob_dict = {
                label: float(prob)
                for label, prob in zip(self.label_encoder.classes_, probabilities)
            }
            
            return prob_dict
            
        except Exception as e:
            logger.error(f"Failed to get probabilities: {e}")
            raise
    
    def get_classes(self) -> List[str]:
        """Get list of all posture classes"""
        if not self.is_loaded:
            return []
        return list(self.label_encoder.classes_)


# Singleton instance
_camera_model_instance = None


def get_camera_model() -> CameraModel:
    """
    Get singleton instance of CameraModel
    
    Returns:
        CameraModel instance
    """
    global _camera_model_instance
    if _camera_model_instance is None:
        _camera_model_instance = CameraModel()
    return _camera_model_instance
