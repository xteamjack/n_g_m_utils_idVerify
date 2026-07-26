import logging
import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
from app.utils.vision import vision_processor
from app.utils.config import get_config
from app.utils.banner import print_banner
from app.utils.config_check import validate_config

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("id-verify")

# 1. Resolve Config and Validate on startup
server_cnf = get_config("apps.idVerifyServer")
validate_config()

# 2. Print Banner
app_name = server_cnf.get("name", "ID-Verify Service") if server_cnf else "ID-Verify Service"
print_banner(app_name, "1.0.0")

app = FastAPI(
    title=app_name,
    description=server_cnf.get("desc", "Identity verification microservice") if server_cnf else "Identity verification microservice",
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
    return {
        "status": "online",
        "service": server_cnf.get("name", "id-verify"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/info")
async def get_info():
    return {
        "app": server_cnf.get("slug", "id-verify-server"),
        "name": server_cnf.get("name", "Identity Verify Server"),
        "version": "1.0.0",
        "description": server_cnf.get("desc", "Identity verification microservice"),
        "tech_stack": server_cnf.get("techStack", "python, fast").split(", "),
        "environment": os.environ.get("SANS_ENV", "dev")
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

    is_valid, message = vision_processor.validate_face_capture(content, request_id)
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
    ocr_result = vision_processor.process_id_card(content, side, request_id)

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

@app.post("/verify/capture/combined")
async def capture_combined(request_id: str, file: UploadFile = File(...)):
    _ensure_session(request_id)

    logger.info(f"Received combined capture for {request_id}")
    content = await file.read()

    result = vision_processor.process_combined_capture(content, request_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    if not result["face_valid"]:
        return {"status": "rejected", "message": result["face_message"]}

    card_res = result["card_result"]
    if card_res["status"] == "success":
        sessions[request_id]["captures"]["face"] = "captured"
        sessions[request_id]["captures"]["front"] = "captured"
        sessions[request_id]["ocr_results"].extend(card_res["raw_text"])

        # Auto-match if we have target data
        match_result = vision_processor.match_data(
            sessions[request_id]["ocr_results"],
            sessions[request_id]["target_data"]
        )

        return {
            "status": "validated",
            "message": "Double-verification successful",
            "ocr": card_res,
            "matching": match_result
        }
    else:
        return {"status": "rejected", "message": "ID card could not be parsed"}

if __name__ == "__main__":
    # Resolve host and port from config server
    host = "0.0.0.0"
    port = 8010

    if server_cnf and "webServer" in server_cnf:
        host = server_cnf["webServer"].get("host", host)
        port = int(server_cnf["webServer"].get("port", port))
        logger.info(f"Resolved server settings from Config Server: {host}:{port}")
    else:
        logger.warning(f"Using default server settings: {host}:{port}")

    # SANS_BIND_HOST (e.g. 0.0.0.0, set in sans-env) overrides the config host
    # (127.0.0.1) for the LISTEN address only, so the server is reachable across
    # the LAN. Mirrors the other Python services' SANS_BIND_HOST convention.
    host = os.environ.get("SANS_BIND_HOST") or host

    uvicorn.run(app, host=host, port=port)
