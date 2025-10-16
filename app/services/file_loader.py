import os
import json
from typing import List, Tuple
from app.config import settings
from app.utils.logger import logger

def list_documents(input_dir: str = settings.input_dir) -> List[str]:
    files = []
    for entry in os.listdir(input_dir):
        path = os.path.join(input_dir, entry)
        if os.path.isfile(path) and entry.lower().split('.')[-1] in ('pdf','jpeg','jpg','png'):
            files.append(path)
    return sorted(files)

def find_metadata_for(file_path: str) -> dict:
    base, _ = os.path.splitext(file_path)
    json_path = base + ".json"
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro lendo metadata {json_path}: {e}")
            return {}
    return {}
