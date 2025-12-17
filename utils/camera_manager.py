"""
Camera Manager - Manages USB camera with priority for inference over streaming
Implements thread-safe camera access with locking mechanism
"""
import cv2
import threading
import time
import logging
from typing import Optional, Tuple
import numpy as np

import config

logger = logging.getLogger(__name__)


class CameraManager:
    """
    Manages camera with priority system:
    - Normal mode: Stream frames for web display
    - Inference mode: Pause stream, capture snapshot for AI processing
    """
    
    def __init__(self, camera_index: int = None, width: int = None, height: int = None):
        """
        Initialize camera manager
        
        Args:
            camera_index: Camera device index (default from config)
            width: Frame width (default from config)
            height: Frame height (default from config)
        """
        self.camera_index = camera_index or config.CAMERA_INDEX
        self.width = width or config.CAMERA_WIDTH
        self.height = height or config.CAMERA_HEIGHT
        
        self.cap = None
        self.is_opened = False
        self.current_frame = None
        self.lock = threading.Lock()
        
        # Inference priority flag
        self.inference_mode = False
        self.inference_frame = None
        
        # Thread for continuous capture
        self.capture_thread = None
        self.running = False
        
        self._init_camera()
    
    def _init_camera(self):
        """Initialize camera device"""
        try:
            logger.info(f"Initializing camera {self.camera_index}...")
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                logger.warning(f"Camera {self.camera_index} not available - running without camera")
                logger.warning("Camera features (video stream, camera-based inference) will be disabled")
                self.is_opened = False
                return  # Don't raise exception, just return
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            # Read actual properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            self.is_opened = True
            
            # Start capture thread
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
        except Exception as e:
            logger.warning(f"Camera initialization failed: {e}")
            logger.warning("Running without camera - camera features will be disabled")
            self.is_opened = False
            # Don't raise - allow webserver to run without camera
    
    def _capture_loop(self):
        """Continuous capture loop running in background thread"""
        logger.info("Camera capture thread started")
        
        while self.running:
            try:
                if not self.cap or not self.cap.isOpened():
                    logger.warning("Camera not available, attempting reconnect...")
                    time.sleep(1)
                    self._reconnect()
                    continue
                
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    logger.warning("Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                # Update current frame (thread-safe)
                with self.lock:
                    self.current_frame = frame.copy()
                
                # Small delay to prevent CPU overload
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.5)
        
        logger.info("Camera capture thread stopped")
    
    def _reconnect(self):
        """Attempt to reconnect to camera"""
        try:
            if self.cap:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                logger.info("Camera reconnected successfully")
            else:
                logger.error("Camera reconnection failed")
                
        except Exception as e:
            logger.error(f"Reconnection error: {e}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get current frame for streaming
        
        Returns:
            Current frame (BGR) or None if not available
        """
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None
    
    def capture_for_inference(self) -> Optional[np.ndarray]:
        """
        Capture a frame specifically for AI inference
        This pauses the normal streaming temporarily
        
        Returns:
            Captured frame (BGR) or None if failed
        """
        try:
            logger.debug("Capturing frame for inference...")
            
            # Set inference mode flag
            self.inference_mode = True
            
            # Wait a bit for the flag to take effect
            time.sleep(0.05)
            
            # Capture fresh frame
            with self.lock:
                if self.current_frame is not None:
                    inference_frame = self.current_frame.copy()
                else:
                    logger.warning("No frame available for inference")
                    inference_frame = None
            
            # Reset inference mode
            self.inference_mode = False
            
            return inference_frame
            
        except Exception as e:
            logger.error(f"Failed to capture frame for inference: {e}")
            self.inference_mode = False
            return None
    
    def get_jpeg_frame(self, quality: int = 85) -> Optional[bytes]:
        """
        Get current frame encoded as JPEG
        
        Args:
            quality: JPEG quality (0-100)
        
        Returns:
            JPEG-encoded frame bytes or None
        """
        frame = self.get_frame()
        
        if frame is None:
            return None
        
        try:
            # Encode as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            ret, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if ret:
                return buffer.tobytes()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to encode frame: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        Check if camera is available
        
        Returns:
            True if camera is working, False otherwise
        """
        return self.is_opened and self.cap is not None and self.cap.isOpened()
    
    def get_status(self) -> dict:
        """
        Get camera status information
        
        Returns:
            Dictionary with camera status
        """
        return {
            'is_opened': self.is_opened,
            'is_available': self.is_available(),
            'camera_index': self.camera_index,
            'width': self.width,
            'height': self.height,
            'inference_mode': self.inference_mode,
            'has_frame': self.current_frame is not None
        }
    
    def release(self):
        """Release camera resources"""
        logger.info("Releasing camera...")
        
        # Stop capture thread
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        # Release camera
        if self.cap:
            self.cap.release()
        
        self.is_opened = False
        logger.info("Camera released")
    
    def __del__(self):
        """Destructor - ensure camera is released"""
        self.release()


# Singleton instance
_camera_manager_instance = None


def get_camera_manager() -> CameraManager:
    """
    Get singleton instance of CameraManager
    
    Returns:
        CameraManager instance
    """
    global _camera_manager_instance
    if _camera_manager_instance is None:
        _camera_manager_instance = CameraManager()
    return _camera_manager_instance
