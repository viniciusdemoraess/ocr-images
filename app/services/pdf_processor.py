from pdf2image import convert_from_path
from typing import List
from PIL import Image
import tempfile
import os

def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Converte todas as páginas do PDF em PIL Images.
    Requer poppler-utils instalado no sistema (pdf2image depende dele).
    """
    images = convert_from_path(pdf_path, dpi=dpi)
    return images

def save_pil_image_to_path(img, out_path: str):
    img.save(out_path)
