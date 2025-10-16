from fastapi import FastAPI
from app.controllers.ocr_controller import router as ocr_router
from app.utils.logger import logger

app = FastAPI(title="OCR Service POC")

app.include_router(ocr_router, prefix="")

@app.get("/")
async def root():
    return {"status": "ok", "service": "ocr_service_poc"}
