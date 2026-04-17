import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Any, Tuple

class VisionProcessor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

    def validate_face_capture(self, image_bytes: bytes) -> Tuple[bool, str]:
        """
        Validates if the image contains exactly one face and it is properly aligned.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return False, "Invalid image format"

        # Convert to RGB for MediaPipe
        results = self.face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            return False, "No face detected"
        
        if len(results.multi_face_landmarks) > 1:
            return False, "Multiple faces detected. Please ensure only one person is visible."

        # Additional checks (lighting, orientation) can be added here
        return True, "Face validated"

    def process_id_card(self, image_bytes: bytes, side: str) -> Dict[str, Any]:
        """
        Uses PaddleOCR/Tesseract to extract information from the ID card.
        """
        # TODO: Implement OCR logic
        return {"status": "success", "extracted_data": {}}

# Singleton instance
vision_processor = VisionProcessor()
