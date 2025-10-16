from typing import Dict, List
from app.utils.normalizer import normalize_value, normalize_text, fuzzy_ratio
from app.config import settings
from decimal import Decimal, InvalidOperation

def compare_value(expected: str, ocr_texts: List[Dict]) -> Dict:
    """
    Procura a melhor correspondência numérica entre o OCR e o valor esperado.
    Retorna o match e a entrada encontrada (texto + bbox + confidence)
    """
    normalized_expected = normalize_value(expected)
    try:
        expected_num = Decimal(normalized_expected)
    except (InvalidOperation, ValueError):
        expected_num = None

    best = {"match": False, "found": None, "ocr_raw": None}
    if expected_num is None:
        return best

    for t in ocr_texts:
        candidate_raw = normalize_value(t["text"])
        try:
            cand_num = Decimal(candidate_raw)
            # comparação numérica exata dentro da tolerância
            diff = abs(cand_num - expected_num)
            if diff <= Decimal(str(settings.value_tolerance)):
                best = {"match": True, "found": str(cand_num), "ocr_raw": t}
                return best
        except (InvalidOperation, ValueError):
            continue

    # se não encontrou exato, tenta aproximação por menor diff
    closest = None
    min_diff = None
    for t in ocr_texts:
        candidate_raw = normalize_value(t["text"])
        try:
            cand_num = Decimal(candidate_raw)
            diff = abs(cand_num - expected_num)
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest = {"match": False, "found": str(cand_num), "ocr_raw": t}
        except:
            continue

    return closest or best

def compare_name(expected: str, ocr_texts: List[Dict]) -> Dict:
    expected_norm = normalize_text(expected)
    best = {"match": False, "score": 0, "ocr_raw": None}
    for t in ocr_texts:
        score = fuzzy_ratio(expected_norm.lower(), (t["text"] or "").lower())
        if score > best["score"]:
            best = {"match": score >= settings.name_match_threshold, "score": score, "ocr_raw": t}
    return best
