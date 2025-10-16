from fastapi import APIRouter
from app.services.file_loader import list_documents, find_metadata_for
from app.services.pdf_processor import pdf_to_images
from app.services.ocr_service import ocr_image_pil
from app.services.comparator_service import compare_value, compare_name
from app.utils.logger import logger
from app.models.ocr_result import DocumentComparison
from typing import List
from PIL import Image
import os

router = APIRouter()

# @router.post("/processar-documentos")
# async def process_documents():
#     results = []
#     files = list_documents()
#     logger.info(f"Encontrados {len(files)} arquivos em input_dir")
#     for fpath in files:
#         logger.info(f"Processando {fpath}")
#         metadata = find_metadata_for(fpath)
#         ocr_texts = []
#         ext = os.path.splitext(fpath)[1].lower()
#         images = []
#         try:
#             if ext == ".pdf":
#                 images = pdf_to_images(fpath)
#             else:
#                 img = Image.open(fpath).convert("RGB")
#                 images = [img]

#             # extrair OCR por página/imagem
#             for img in images:
#                 page_texts = ocr_image_pil(img)
#                 ocr_texts.extend(page_texts)

#             # comparações simples (ex.: nome, valor) quando existirem no metadata
#             comparisons = []
#             if metadata:
#                 if "valor" in metadata:
#                     comp_val = compare_value(metadata.get("valor"), ocr_texts)
#                     comparisons.append({
#                         "campo": "valor",
#                         "esperado": metadata.get("valor"),
#                         "resultado": comp_val
#                     })
#                 if "nome" in metadata:
#                     comp_name = compare_name(metadata.get("nome"), ocr_texts)
#                     comparisons.append({
#                         "campo": "nome",
#                         "esperado": metadata.get("nome"),
#                         "resultado": comp_name
#                     })

#             doc_res = {
#                 "arquivo": os.path.basename(fpath),
#                 "comparisons": comparisons,
#                 "ocr_texts": ocr_texts
#             }
#             results.append(doc_res)
#         except Exception as e:
#             logger.error(f"Erro processando {fpath}: {e}")
#             results.append({"arquivo": os.path.basename(fpath), "error": str(e)})
#     return {"results": results}


@router.post("/processar-documentos")
async def process_documents():
    results = []
    files = list_documents()
    logger.info(f"Encontrados {len(files)} arquivos em input_dir")

    for fpath in files:
        logger.info(f"Processando {fpath}")
        try:
            # Carregar metadata se existir
            metadata = find_metadata_for(fpath)
            ext = os.path.splitext(fpath)[1].lower()
            
            # Processar arquivo para extrair imagens
            if ext == ".pdf":
                images = pdf_to_images(fpath)
            else:
                img = Image.open(fpath).convert("RGB")
                images = [img]

            # Processar OCR em todas as imagens
            all_ocr_items = []
            for img in images:
                ocr_items = ocr_image_pil(img)
                all_ocr_items.extend(ocr_items)

            logger.info(f"Total de textos extraídos: {len(all_ocr_items)}")

            # Preparar resultado
            doc_result = {
                "arquivo": os.path.basename(fpath),
                "textos_extraidos": len(all_ocr_items)
                "ocr_resultados": all_ocr_items
            }

            # Adicionar comparações se houver metadata
            if metadata and all_ocr_items:
                try:
                    comparisons = []
                    logger.info(f"Metadata encontrado: {metadata}")
                    logger.info(f"Primeiro item OCR: {all_ocr_items[0] if all_ocr_items else 'Nenhum'}")
                    
                    # As funções de comparação esperam List[Dict], não List[str]
                    # Então passamos all_ocr_items diretamente
                    if "valor" in metadata:
                        comp_val = compare_value(metadata.get("valor"), all_ocr_items)
                        comparisons.append({
                            "campo": "valor",
                            "esperado": metadata.get("valor"),
                            "resultado": comp_val
                        })
                    
                    if "nome" in metadata:
                        comp_name = compare_name(metadata.get("nome"), all_ocr_items)
                        comparisons.append({
                            "campo": "nome",
                            "esperado": metadata.get("nome"),
                            "resultado": comp_name
                        })

                    doc_result["comparisons"] = comparisons
                    logger.info(f"Comparações adicionadas: {len(comparisons)}")
                    
                except Exception as comp_error:
                    logger.error(f"Erro durante comparações: {comp_error}")
                    doc_result["comparisons"] = []

            results.append(doc_result)

        except Exception as e:
            logger.error(f"Erro processando {fpath}: {e}")
            results.append({
                "arquivo": os.path.basename(fpath), 
                "error": str(e)
            })

    return {"results": results}
