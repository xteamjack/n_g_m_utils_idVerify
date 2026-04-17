import cv2
import numpy as np
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, Tuple, List
from paddleocr import PaddleOCR

# Configure Logger early to avoid NameError in initialization blocks
logger = logging.getLogger("id-verify.vision")

# Use explicit and redundant import paths to avoid AttributeError/ImportError on different OS builds
try:
    import mediapipe.solutions.face_mesh as mp_face_mesh
    import mediapipe.solutions.drawing_utils as mp_drawing
except (ImportError, AttributeError):
    try:
        # Fallback for some Windows/Python 3.10 builds
        from mediapipe.python.solutions import face_mesh as mp_face_mesh
        from mediapipe.python.solutions import drawing_utils as mp_drawing
    except (ImportError, AttributeError):
        logger.error("MediaPipe solutions module could not be imported through standard paths.")
        mp_face_mesh = None
        mp_drawing = None

class VisionProcessor:
    def __init__(self):
        # 1. Initialize Face Mesh
        self.face_mesh = None
        if mp_face_mesh:
            try:
                self.face_mesh = mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
                )
                logger.info("MediaPipe FaceMesh initialized.")
            except Exception as e:
                logger.error(f"Failed to create FaceMesh: {e}")
        else:
            logger.error("MediaPipe FaceMesh module not found.")
        
        # 2. Initialize PaddleOCR (Lazily loaded or on first call if preferred, but doing it here for speed later)
        # Use English by default, can be extended to others ['en', 'hi', etc]
        try:
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("PaddleOCR initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.ocr = None

        # 3. Ensure uploads directory exists
        self.upload_dir = "uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def _save_debug_image(self, img: np.ndarray, prefix: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.jpg"
        path = os.path.join(self.upload_dir, filename)
        cv2.imwrite(path, img)
        return path

    def validate_face_capture(self, image_bytes: bytes) -> Tuple[bool, str]:
        """
        Validates the face capture for biometric quality.
        """
        if not self.face_mesh:
            logger.error("FaceMesh is None. Validation aborted.")
            return False, "Biometric engine failed to initialize. Please check server logs."

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return False, "Invalid image format"

        # Blur Detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < 100:
            return False, "Capture is too blurry."

        # Face Landmark Processing
        try:
            results = self.face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if not results.multi_face_landmarks:
                return False, "No face detected."
            return True, "Face verified successfully."
        except Exception as e:
            logger.error(f"Error during face processing: {e}")
            return False, "Processing error."

    def process_id_card(self, image_bytes: bytes, side: str) -> Dict[str, Any]:
        """
        Uses PaddleOCR to extract information from the ID card.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"status": "error", "message": "Invalid image"}

        path = self._save_debug_image(img, f"card_{side}")
        
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
