import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    input_dir: str = os.getenv("INPUT_DIR", "/app/input_docs")
    ocr_lang: str = "pt"  # ajustar se preciso
    name_match_threshold: int = 80
    value_tolerance: float = 0.01  # tolerância para comparar valores numéricos

settings = Settings()
