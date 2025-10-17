from paddleocr import PaddleOCR
import pprint
import os
import json
import re
from difflib import SequenceMatcher

def similarity(a, b):
    """Calcula a similaridade entre duas strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalize_text(text):
    """Normaliza texto removendo caracteres especiais e espaços extras"""
    # Remove caracteres especiais, mantém apenas letras, números, espaços, vírgulas e pontos
    text = re.sub(r'[^\w\s,.]', '', text)
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def find_matches_in_text(extracted_texts, search_values, threshold=0.7):
    """Encontra matches entre o texto extraído e os valores procurados"""
    matches = {}
    
    for field, search_value in search_values.items():
        best_match = None
        best_similarity = 0
        best_confidence = 0
        
        search_value_normalized = normalize_text(str(search_value))
        
        for text_info in extracted_texts:
            text = text_info['text']
            confidence = text_info['confidence']
            text_normalized = normalize_text(text)
            
            # Verifica similaridade completa
            sim_score = similarity(text_normalized, search_value_normalized)
            
            # Verifica se o valor procurado está contido no texto extraído
            contains_score = 0
            if search_value_normalized in text_normalized:
                contains_score = 0.9
            
            # Usa a maior pontuação entre similaridade e contenção
            final_score = max(sim_score, contains_score)
            
            if final_score > threshold and final_score > best_similarity:
                best_similarity = final_score
                best_match = text
                best_confidence = confidence
        
        if best_match:
            matches[field] = {
                'found': True,
                'expected': search_value,
                'extracted': best_match,
                'similarity': best_similarity,
                'ocr_confidence': best_confidence
            }
        else:
            matches[field] = {
                'found': False,
                'expected': search_value,
                'extracted': None,
                'similarity': 0,
                'ocr_confidence': 0
            }
    
    return matches

def extract_text_from_ocr_result(result):
    """Extrai texto e confiança do resultado do OCR"""
    texto_extraido = []
    
    for res in result:
        if isinstance(res, dict) and 'data' in res:
            linhas = res['data']
        elif isinstance(res, list):
            linhas = res
        elif isinstance(res, dict) and 'rec_texts' in res:
            for i, texto in enumerate(res['rec_texts']):
                confianca = res['rec_scores'][i] if 'rec_scores' in res else 0.0
                texto_extraido.append({
                    'text': texto,
                    'confidence': confianca
                })
            continue
        else:
            continue
        
        for linha in linhas:
            texto = linha.get('text', '')
            confianca = linha.get('confidence', 0.0)
            texto_extraido.append({
                'text': texto,
                'confidence': confianca
            })
    
    return texto_extraido

def process_document(file_path, json_data, ocr):
    """Processa um documento e verifica matches com os dados do JSON"""
    print(f"\n=== Processando: {file_path} ===")
    
    # Executa OCR
    result = ocr.predict(file_path)
    
    # Extrai texto e confiança
    extracted_texts = extract_text_from_ocr_result(result)
    
    # Encontra matches
    matches = find_matches_in_text(extracted_texts, json_data)
    
    return {
        'file_path': file_path,
        'json_data': json_data,
        'extracted_texts': extracted_texts,
        'matches': matches
    }

# Inicializa OCR
ocr = PaddleOCR(use_angle_cls=True, lang='pt')

# Diretório dos documentos
input_dir = 'input_docs'

# Lista para armazenar todos os resultados
all_results = []

# Processa todos os arquivos
for filename in os.listdir(input_dir):
    if filename.endswith(('.pdf', '.jpeg', '.jpg', '.png')):
        # Encontra o JSON correspondente
        json_filename = filename.rsplit('.', 1)[0] + '.json'
        json_path = os.path.join(input_dir, json_filename)
        
        if os.path.exists(json_path):
            # Carrega dados do JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Processa o documento
            file_path = os.path.join(input_dir, filename)
            result = process_document(file_path, json_data, ocr)
            all_results.append(result)

# Gera relatório detalhado em TXT
nome_arquivo_saida = 'resultado_ocr_completo.txt'
with open(nome_arquivo_saida, 'w', encoding='utf-8') as arquivo:
    arquivo.write("=== RESULTADO DO OCR - ANÁLISE COMPLETA ===\n\n")
    arquivo.write(f"Total de documentos processados: {len(all_results)}\n\n")
    
    for i, result in enumerate(all_results, 1):
        arquivo.write(f"=== DOCUMENTO {i}: {os.path.basename(result['file_path'])} ===\n\n")
        
        # Dados esperados do JSON
        arquivo.write("DADOS ESPERADOS (JSON):\n")
        for key, value in result['json_data'].items():
            arquivo.write(f"  {key}: {value}\n")
        arquivo.write("\n")
        
        # Resultados dos matches
        arquivo.write("RESULTADOS DOS MATCHES:\n")
        for field, match_info in result['matches'].items():
            status = "✅ ENCONTRADO" if match_info['found'] else "❌ NÃO ENCONTRADO"
            arquivo.write(f"  {field}: {status}\n")
            arquivo.write(f"    Esperado: {match_info['expected']}\n")
            if match_info['found']:
                arquivo.write(f"    Extraído: {match_info['extracted']}\n")
                arquivo.write(f"    Similaridade: {match_info['similarity']:.2%}\n")
                arquivo.write(f"    Confiança OCR: {match_info['ocr_confidence']:.2%}\n")
            arquivo.write("\n")
        
        # Todos os textos extraídos
        arquivo.write("TODOS OS TEXTOS EXTRAÍDOS:\n")
        for j, text_info in enumerate(result['extracted_texts'], 1):
            arquivo.write(f"  {j:03d}. {text_info['text']} (Confiança: {text_info['confidence']:.2%})\n")
        
        arquivo.write("\n" + "="*50 + "\n\n")

# Gera arquivos JSON individuais para cada documento
output_dir = 'resultados_json'
os.makedirs(output_dir, exist_ok=True)

for result in all_results:
    filename = os.path.basename(result['file_path'])
    json_filename = f"{filename.rsplit('.', 1)[0]}_resultado.json"
    json_path = os.path.join(output_dir, json_filename)
    
    # Prepara dados para JSON
    json_data = {
        "arquivo_processado": filename,
        "caminho_completo": result['file_path'],
        "data_processamento": "2024-11-17",
        "dados_esperados": result['json_data'],
        "resumo_matches": {
            "total_campos": len(result['matches']),
            "campos_encontrados": sum(1 for match in result['matches'].values() if match['found']),
            "taxa_sucesso": f"{(sum(1 for match in result['matches'].values() if match['found']) / len(result['matches']) * 100):.1f}%"
        },
        "detalhes_matches": {},
        "todos_textos_extraidos": []
    }
    
    # Adiciona detalhes dos matches
    for field, match_info in result['matches'].items():
        json_data["detalhes_matches"][field] = {
            "encontrado": match_info['found'],
            "valor_esperado": match_info['expected'],
            "valor_extraido": match_info['extracted'],
            "similaridade_percentual": f"{match_info['similarity']:.1%}",
            "confianca_ocr_percentual": f"{match_info['ocr_confidence']:.1%}",
            "similaridade_decimal": round(match_info['similarity'], 3),
            "confianca_ocr_decimal": round(match_info['ocr_confidence'], 3)
        }
    
    # Adiciona todos os textos extraídos
    for text_info in result['extracted_texts']:
        json_data["todos_textos_extraidos"].append({
            "texto": text_info['text'],
            "confianca_percentual": f"{text_info['confidence']:.1%}",
            "confianca_decimal": round(text_info['confidence'], 3)
        })
    
    # Salva o JSON
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)
    
    print(f"📄 JSON salvo: {json_path}")

# Relatório resumido no console
print(f"\n=== RELATÓRIO RESUMIDO ===")
print(f"Total de documentos processados: {len(all_results)}")

for result in all_results:
    filename = os.path.basename(result['file_path'])
    print(f"\n📄 {filename}:")
    
    total_fields = len(result['matches'])
    found_fields = sum(1 for match in result['matches'].values() if match['found'])
    
    print(f"  Campos encontrados: {found_fields}/{total_fields}")
    
    for field, match_info in result['matches'].items():
        status = "✅" if match_info['found'] else "❌"
        if match_info['found']:
            print(f"  {status} {field}: {match_info['similarity']:.1%} similaridade, {match_info['ocr_confidence']:.1%} confiança")
        else:
            print(f"  {status} {field}: Não encontrado")

print(f"\n📊 Relatório detalhado salvo em: {nome_arquivo_saida}")
print(f"🔍 Processamento concluído com sucesso!")