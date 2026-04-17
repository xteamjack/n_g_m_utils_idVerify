import cv2
import numpy as np
import logging
import os
import re
import urllib.request
from datetime import datetime
from typing import Dict, Any, Tuple, List
from paddleocr import PaddleOCR
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Configure Logger
logger = logging.getLogger("id-verify.vision")

class VisionProcessor:
    def __init__(self):
        # 1. Initialize Face Landmarker (Tasks API)
        # We need the model file. We'll try to download it if not present.
        model_path = "face_landmarker.task"
        if not os.path.exists(model_path):
            logger.info("Downloading face_landmarker.task model...")
            model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            try:
                urllib.request.urlretrieve(model_url, model_path)
                logger.info("Model downloaded successfully.")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")

        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True,
                num_faces=1,
                min_face_detection_confidence=0.5
            )
            self.detector = vision.FaceLandmarker.create_from_options(options)
            logger.info("MediaPipe FaceLandmarker (Tasks API) initialized.")
        except Exception as e:
            self.detector = None
            logger.error(f"Failed to initialize FaceLandmarker: {e}")
        
        # 2. Initialize PaddleOCR (Lazily loaded or on first call if preferred, but doing it here for speed later)
        # Use English by default, can be extended to others ['en', 'hi', etc]
        try:
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("PaddleOCR initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.ocr = None

        # 3. Ensure uploads directory exists in repo root
        self.upload_dir = r"D:\wspc3\repo\node\nuxtTrial\n_g_m_utils_idVerify\uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)

    def _save_debug_image(self, img: np.ndarray, prefix: str, request_id: str = "default"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.upload_dir, request_id)
        if not os.path.exists(session_dir):
            os.makedirs(session_dir, exist_ok=True)
            
        filename = f"{prefix}_{timestamp}.jpg"
        path = os.path.join(session_dir, filename)
        cv2.imwrite(path, img)
        return path

    def validate_face_capture(self, image_bytes: bytes, request_id: str = "default") -> Tuple[bool, str]:
        """
        Validates the face capture for biometric quality and saves it to the session folder.
        """
        if not self.detector:
            logger.error("FaceLandmarker detector is None. Validation aborted.")
            return False, "Biometric engine failed to initialize. Please check server logs."

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return False, "Invalid image format"

        # Save face for reference/debug even if it might fail later
        path = self._save_debug_image(img, "face", request_id)
        logger.info(f"Face capture saved to {path}")

        # Blur Detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < 100:
            return False, "Capture is too blurry."

        # Face Landmark Processing
        try:
            # Convert OpenCV image to MediaPipe Image
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
            
            results = self.detector.detect(mp_image)
            
            if not results.face_landmarks:
                return False, "No face detected."
                
            return True, "Face verified successfully."
        except Exception as e:
            logger.error(f"Error during face processing: {e}")
            return False, "Processing error."

    def process_id_card(self, image_bytes: bytes, side: str, request_id: str = "default") -> Dict[str, Any]:
        """
        Uses PaddleOCR to extract information from the ID card and saves to session folder.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"status": "error", "message": "Invalid image"}

        path = self._save_debug_image(img, f"card_{side}", request_id)
        
        if not self.ocr:
            return {"status": "error", "message": "OCR Engine not initialized"}

        # Perform OCR
        result = self.ocr.ocr(img, cls=True)
        
        extracted_text = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                extracted_text.append(text)

        logger.info(f"OCR Extracted from {side}: {extracted_text}")
        
        # Basic heuristic to find an ID-like number (regex for alphanumeric blocks)
        id_numbers = []
        for text in extracted_text:
            # Look for patterns like "ABC123456" or "1234 5678 9012"
            clean_text = re.sub(r'[^A-Z0-9\s]', '', text.upper())
            if len(clean_text) > 8:
                id_numbers.append(clean_text)

        return {
            "status": "success", 
            "side": side,
            "raw_text": extracted_text,
            "potential_ids": id_numbers,
            "debug_path": path
        }

    def match_data(self, extracted_texts: List[str], target_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Matches extracted OCR text against target user data.
        """
        scores = {}
        all_text = " ".join(extracted_texts).upper()
        
        for key, value in target_data.items():
            if not value: continue
            val_str = str(value).upper()
            # Simple check for now, can be improved with Levenshtein
            if val_str in all_text:
                scores[key] = 1.0
            else:
                scores[key] = 0.0
                
        return {
            "match_scores": scores,
            "is_valid": all(s > 0.8 for s in scores.values()) if scores else False
        }

# Singleton instance
vision_processor = VisionProcessor()
