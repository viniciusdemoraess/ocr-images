from typing import List, Dict
from pydantic import BaseModel

class TextBox(BaseModel):
    text: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]

class DocumentComparison(BaseModel):
    arquivo: str
    comparisons: List[Dict]
    ocr_texts: List[TextBox]
