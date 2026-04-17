import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
from app.utils.vision import vision_processor

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("id-verify")

app = FastAPI(
    title="SANS-Way ID Verification Service",
    description="Microservice for real-time user identity verification with face and government ID.",
    version="1.0.0"
)

# Enable CORS for Nuxt Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory Session Store (For PoC) ---
sessions: Dict[str, Dict[str, Any]] = {}

# Models
class InitRequest(BaseModel):
    api_key: str
    callback_url: str
    request_id: str
    data: Optional[Dict[str, Any]] = {}

# Endpoints
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "online", "service": "id-verify"}

@app.get("/api/info")
async def get_info():
    return {
        "app": "id-verify",
        "version": "1.0.0",
        "description": "User Onboarding and ID Verification microservice",
        "tech_stack": ["Python", "FastAPI", "OpenCV", "MediaPipe", "PaddleOCR"]
    }

@app.post("/verify/init")
async def initialize_verification(req: InitRequest):
    logger.info(f"Initializing verification for request: {req.request_id}")
    
    # Create session state
    sessions[req.request_id] = {
        "target_data": req.data,
        "callback_url": req.callback_url,
        "captures": {
            "face": None,
            "front": None,
            "back": None
        },
        "ocr_results": [],
        "status": "initiated"
    }
    
    return {
        "status": "success",
        "request_id": req.request_id,
        "capture_url": f"/verify/{req.request_id}"
    }

@app.get("/verify/session/{request_id}")
async def get_session(request_id: str):
    if request_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[request_id]

def _ensure_session(request_id: str):
    """Helper to ensure a session exists for PoC/Demo purposes."""
    if request_id not in sessions:
        logger.info(f"Auto-initializing session for Demo/PoC: {request_id}")
        sessions[request_id] = {
            "target_data": {"firstName": "DEMO", "lastName": "USER", "idNumber": "123456789"},
            "callback_url": "http://localhost:3000/callback",
            "captures": {"face": None, "front": None, "back": None},
            "ocr_results": [],
            "status": "auto-initiated"
        }

@app.post("/verify/capture/face")
async def capture_face(request_id: str, file: UploadFile = File(...)):
    _ensure_session(request_id)
    
    logger.info(f"Received face capture for {request_id}")
    content = await file.read()
    
    is_valid, message = vision_processor.validate_face_capture(content)
    if not is_valid:
        return {"status": "rejected", "message": message}
    
    sessions[request_id]["captures"]["face"] = "captured"
    return {"status": "validated", "message": "Face capture accepted"}

@app.post("/verify/capture/card")
async def capture_card(request_id: str, side: str, file: UploadFile = File(...)):
    _ensure_session(request_id)
    
    if side not in ["front", "back"]:
        raise HTTPException(status_code=400, detail="Invalid card side")
    
    content = await file.read()
    logger.info(f"Received {side} card capture for {request_id}")
    
    # Process OCR
    ocr_result = vision_processor.process_id_card(content, side)
    
    if ocr_result["status"] == "success":
        sessions[request_id]["captures"][side] = "captured"
        sessions[request_id]["ocr_results"].extend(ocr_result["raw_text"])
        
        # If both sides are captured, perform matching
        match_result = None
        if sessions[request_id]["captures"]["front"] and sessions[request_id]["captures"]["back"]:
             match_result = vision_processor.match_data(
                 sessions[request_id]["ocr_results"], 
                 sessions[request_id]["target_data"]
             )
             sessions[request_id]["status"] = "verified" if match_result["is_valid"] else "unmatched"
        
        return {
            "status": "processed", 
            "ocr": ocr_result,
            "matching": match_result
        }
    
    return {"status": "error", "message": "OCR Processing failed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
