# from typing import List, Dict
# from app.utils.logger import logger
# from app.utils.normalizer import normalize_text
# from app.config import settings
# from paddleocr import PaddleOCR
# from PIL import Image
# import numpy as np
# import tempfile
# import os

# # Inicializa o modelo uma vez
# OCR = PaddleOCR(use_angle_cls=True, lang=settings.ocr_lang, use_gpu=False)  # use_gpu se disponível

# def ocr_image_pil(image: Image.Image) -> List[Dict]:
#     """
#     Recebe PIL Image e retorna lista de {text, confidence, bbox}
#     bbox como [x1,y1,x2,y2] (retângulo aproximado)
#     """
#     tmp_path = None
#     try:
#         # PaddleOCR aceita caminho ou numpy array; convertemos para temp png
#         tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
#         tmp_path = tmp.name
#         image.save(tmp_path)
#         result = OCR.ocr(tmp_path, cls=True)
#         extracted = []
#         # result é uma lista por linha: [[box], (text, score)]
#         for line in result:
#             if not line:
#                 continue
#             # depending on paddleocr version, line can be [ [box], (text,score) ] or nested; handle both
#             if isinstance(line[0], list) and len(line) >= 2:
#                 box = line[0]
#                 text, score = line[1][0], float(line[1][1])
#             else:
#                 # fallback
#                 continue
#             # box is 4 points [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
#             xs = [p[0] for p in box]
#             ys = [p[1] for p in box]
#             bbox = [min(xs), min(ys), max(xs), max(ys)]
#             extracted.append({
#                 "text": normalize_text(text),
#                 "confidence": score,
#                 "bbox": bbox
#             })
#         return extracted
#     except Exception as e:
#         logger.error(f"OCR falhou: {e}")
#         return []
#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             try:
#                 os.remove(tmp_path)
#             except:
#                 pass
from paddleocr import PaddleOCR
from PIL import Image
from typing import List, Dict
import tempfile
import os
from app.utils.logger import logger

# Inicializa o OCR uma vez
logger.info("Inicializando PaddleOCR...")
try:
    OCR = PaddleOCR(use_angle_cls=True, lang='pt')
    logger.info("PaddleOCR inicializado com sucesso!")
except Exception as e:
    logger.error(f"Erro ao inicializar PaddleOCR: {e}")
    raise

def ocr_image_pil(image: Image.Image) -> List[Dict]:
    tmp_path = None
    try:
        # Salva a imagem temporariamente
        tmp_f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_path = tmp_f.name
        tmp_f.close()
        image.save(tmp_path)
        
        logger.info(f"Processando OCR na imagem: {tmp_path}")
        
        # Tenta usar predict primeiro (como no seu script)
        result = None
        if hasattr(OCR, 'predict'):
            logger.info("Usando método predict()")
            result = OCR.predict(tmp_path)
            logger.info(f"OCR predict retornou: {type(result)} com {len(result) if result else 0} itens")
        else:
            logger.info("Método predict não encontrado, usando ocr()")
            result = OCR.ocr(tmp_path, cls=True)
            logger.info(f"OCR ocr retornou: {type(result)} com {len(result) if result else 0} itens")
        
        if not result:
            logger.warning("OCR não retornou resultados")
            return []
        
        texto_extraido = []
        
        # Tratamento para resultado do predict (como no seu script)
        if hasattr(OCR, 'predict') and isinstance(result, list):
            for res in result:
                if isinstance(res, dict) and 'data' in res:
                    # Estrutura: {'data': [{'text': '...', 'confidence': 0.99}, ...]}
                    linhas = res['data']
                    for linha in linhas:
                        texto = linha.get('text', '')
                        confianca = float(linha.get('confidence', 0.0))
                        if texto.strip():
                            texto_extraido.append({
                                "text": texto.strip(),
                                "confidence": confianca,
                                "bbox": linha.get('bbox', [])
                            })
                            
                elif isinstance(res, list):
                    # Estrutura: [{'text': '...', 'confidence': 0.99}, ...]
                    for linha in res:
                        if isinstance(linha, dict):
                            texto = linha.get('text', '')
                            confianca = float(linha.get('confidence', 0.0))
                            if texto.strip():
                                texto_extraido.append({
                                    "text": texto.strip(),
                                    "confidence": confianca,
                                    "bbox": linha.get('bbox', [])
                                })
                                
                elif isinstance(res, dict) and 'rec_texts' in res:
                    # Estrutura: {'rec_texts': ['texto1', 'texto2'], 'rec_scores': [0.99, 0.98]}
                    rec_texts = res.get('rec_texts', [])
                    rec_scores = res.get('rec_scores', [])
                    for i, texto in enumerate(rec_texts):
                        confianca = float(rec_scores[i]) if i < len(rec_scores) else 0.0
                        if texto.strip():
                            texto_extraido.append({
                                "text": texto.strip(),
                                "confidence": confianca,
                                "bbox": []
                            })
        else:
            # Tratamento para resultado do ocr() padrão
            page_results = result[0] if result and len(result) > 0 else []
            logger.info(f"Processando {len(page_results)} linhas do OCR padrão")
            
            for i, line in enumerate(page_results):
                try:
                    if line and len(line) >= 2:
                        coords = line[0]  # coordenadas
                        text_info = line[1]  # (texto, confiança)
                        
                        logger.debug(f"Linha {i}: line completa = {line}")
                        
                        # O formato correto é: [[coordenadas], [texto, confiança]]
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            texto = str(text_info[0]).strip()
                            confianca = float(text_info[1])
                        elif isinstance(text_info, str):
                            # Se text_info é string, pode ser que coords seja o texto
                            if isinstance(coords, str):
                                texto = coords.strip()
                                confianca = float(text_info) if isinstance(text_info, (int, float)) else 0.0
                            else:
                                texto = text_info.strip()
                                confianca = 0.0
                        else:
                            logger.warning(f"Linha {i}: formato não reconhecido - {line}")
                            continue
                        
                        if texto and texto != "0" and len(texto) > 1:  # filtro básico
                            bbox = []
                            if isinstance(coords, list) and len(coords) >= 4:
                                try:
                                    xs = [point[0] for point in coords if isinstance(point, (list, tuple)) and len(point) >= 2]
                                    ys = [point[1] for point in coords if isinstance(point, (list, tuple)) and len(point) >= 2]
                                    if xs and ys:
                                        bbox = [min(xs), min(ys), max(xs), max(ys)]
                                except:
                                    bbox = []
                            
                            texto_extraido.append({
                                "text": texto,
                                "confidence": confianca,
                                "bbox": bbox
                            })
                            logger.debug(f"Texto {i} extraído: '{texto}' (conf: {confianca:.2f})")
                        else:
                            logger.debug(f"Linha {i}: texto ignorado: '{texto}'")
                    else:
                        logger.warning(f"Linha {i}: formato inválido: {line}")
                except Exception as line_error:
                    logger.error(f"Erro ao processar linha {i}: {line_error} - Linha: {line}")
                    continue
        
        logger.info(f"OCR extraiu {len(texto_extraido)} textos")
        return texto_extraido
        
    except Exception as e:
        logger.error(f"Erro no OCR: {e}")
        return []
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
