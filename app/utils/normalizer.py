import re
from rapidfuzz import fuzz

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = s.strip()
    s = s.replace("’", "'")
    # remover múltiplos espaços
    s = re.sub(r'\s+', ' ', s)
    return s

def normalize_value(s: str) -> str:
    if s is None:
        return ""
    s = s.strip()
    # transformar vírgula decimal para ponto e remover símbolos
    s = s.replace('.', '').replace(',', '.')
    s = re.sub(r'[^\d.-]', '', s)
    return s

def fuzzy_ratio(a: str, b: str) -> int:
    return fuzz.token_sort_ratio(a or "", b or "")
