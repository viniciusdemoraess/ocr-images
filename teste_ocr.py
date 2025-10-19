from paddleocr import PaddleOCR
import pprint
import os
import json
import re
from difflib import SequenceMatcher
from datetime import datetime

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
        # Pula campos com valores null, None ou string vazia
        if search_value is None or search_value == "" or search_value == "null":
            continue
            
        best_match = None
        best_similarity = 0
        best_confidence = 0
        
        search_value_normalized = normalize_text(str(search_value))
        
        # Se após normalizar o valor ficar vazio, também pula
        if not search_value_normalized.strip():
            continue
        
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

def process_document(file_path, json_data, ocr, edital_name):
    """Processa um documento e verifica matches com os dados do JSON"""
    print(f"\n=== Processando: {file_path} (Edital: {edital_name}) ===")
    
    # Executa OCR
    result = ocr.predict(file_path)
    
    # Extrai texto e confiança
    extracted_texts = extract_text_from_ocr_result(result)
    
    # Encontra matches
    matches = find_matches_in_text(extracted_texts, json_data)
    
    return {
        'file_path': file_path,
        'edital': edital_name,
        'json_data': json_data,
        'extracted_texts': extracted_texts,
        'matches': matches
    }

def calculate_edital_stats(results_by_edital):
    """Calcula estatísticas por edital"""
    edital_stats = {}
    
    for edital_name, results in results_by_edital.items():
        total_documents = len(results)
        total_fields = sum(len(result['matches']) for result in results)
        total_found = sum(sum(1 for match in result['matches'].values() if match['found']) for result in results)
        
        success_rate = (total_found / total_fields * 100) if total_fields > 0 else 0
        
        edital_stats[edital_name] = {
            'total_documents': total_documents,
            'total_fields': total_fields,
            'fields_found': total_found,
            'success_rate': success_rate,
            'results': results
        }
    
    return edital_stats

# Inicializa OCR
ocr = PaddleOCR(use_angle_cls=True, lang='pt')

# Diretório dos documentos
input_dir = 'input_docs'

# Dicionário para armazenar resultados por edital
results_by_edital = {}
all_results = []

# Verifica se input_docs tem subpastas (editais) ou arquivos diretos
has_subdirs = any(os.path.isdir(os.path.join(input_dir, item)) for item in os.listdir(input_dir))

if has_subdirs:
    # Processa por subpastas (editais)
    for edital_name in os.listdir(input_dir):
        edital_path = os.path.join(input_dir, edital_name)
        
        if os.path.isdir(edital_path):
            print(f"\n🏛️ Processando Edital: {edital_name}")
            results_by_edital[edital_name] = []
            
            for filename in os.listdir(edital_path):
                if filename.endswith(('.pdf', '.jpeg', '.jpg', '.png')):
                    # Encontra o JSON correspondente
                    json_filename = filename.rsplit('.', 1)[0] + '.json'
                    json_path = os.path.join(edital_path, json_filename)
                    
                    if os.path.exists(json_path):
                        # Carrega dados do JSON
                        with open(json_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                        
                        # Processa o documento
                        file_path = os.path.join(edital_path, filename)
                        result = process_document(file_path, json_data, ocr, edital_name)
                        results_by_edital[edital_name].append(result)
                        all_results.append(result)
else:
    # Modo compatibilidade: processa arquivos diretos em input_docs
    print("📁 Processando arquivos diretamente em input_docs (modo compatibilidade)")
    results_by_edital['root'] = []
    
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
                result = process_document(file_path, json_data, ocr, 'root')
                results_by_edital['root'].append(result)
                all_results.append(result)

# Calcula estatísticas por edital
edital_stats = calculate_edital_stats(results_by_edital)

# Gera relatório detalhado em TXT
nome_arquivo_saida = 'resultado_ocr_completo.txt'
with open(nome_arquivo_saida, 'w', encoding='utf-8') as arquivo:
    arquivo.write("=== RESULTADO DO OCR - ANÁLISE COMPLETA POR EDITAL ===\n\n")
    arquivo.write(f"Data do processamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    arquivo.write(f"Total de editais processados: {len(edital_stats)}\n")
    arquivo.write(f"Total de documentos processados: {len(all_results)}\n\n")
    
    # Resumo por edital
    arquivo.write("=== RESUMO POR EDITAL ===\n\n")
    for edital_name, stats in edital_stats.items():
        display_name = "Arquivos Diretos" if edital_name == 'root' else edital_name
        arquivo.write(f"🏛️ {display_name}:\n")
        arquivo.write(f"  📄 Documentos: {stats['total_documents']}\n")
        arquivo.write(f"  🔍 Campos totais: {stats['total_fields']}\n")
        arquivo.write(f"  ✅ Campos encontrados: {stats['fields_found']}\n")
        arquivo.write(f"  📊 Taxa de sucesso: {stats['success_rate']:.1f}%\n\n")
    
    # Detalhes por edital
    for edital_name, stats in edital_stats.items():
        display_name = "Arquivos Diretos" if edital_name == 'root' else edital_name
        arquivo.write(f"\n{'='*60}\n")
        arquivo.write(f"EDITAL: {display_name}\n")
        arquivo.write(f"{'='*60}\n\n")
        
        for i, result in enumerate(stats['results'], 1):
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

# Gera JSON consolidado por edital
edital_consolidado_path = os.path.join(output_dir, 'resumo_por_edital.json')
edital_consolidado = {
    "data_processamento": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
    "total_editais": len(edital_stats),
    "total_documentos": len(all_results),
    "estatisticas_por_edital": {}
}

for edital_name, stats in edital_stats.items():
    display_name = "arquivos_diretos" if edital_name == 'root' else edital_name
    edital_consolidado["estatisticas_por_edital"][display_name] = {
        "nome_edital": "Arquivos Diretos" if edital_name == 'root' else edital_name,
        "total_documentos": stats['total_documents'],
        "total_campos": stats['total_fields'],
        "campos_encontrados": stats['fields_found'],
        "taxa_sucesso_percentual": f"{stats['success_rate']:.1f}%",
        "taxa_sucesso_decimal": round(stats['success_rate'] / 100, 3)
    }

with open(edital_consolidado_path, 'w', encoding='utf-8') as json_file:
    json.dump(edital_consolidado, json_file, ensure_ascii=False, indent=2)

print(f"📊 Resumo por edital salvo: {edital_consolidado_path}")

# Gera JSONs individuais por documento
for result in all_results:
    filename = os.path.basename(result['file_path'])
    edital_prefix = "" if result['edital'] == 'root' else f"{result['edital']}_"
    json_filename = f"{edital_prefix}{filename.rsplit('.', 1)[0]}_resultado.json"
    json_path = os.path.join(output_dir, json_filename)
    
    # Prepara dados para JSON
    json_data = {
        "arquivo_processado": filename,
        "edital": "Arquivos Diretos" if result['edital'] == 'root' else result['edital'],
        "caminho_completo": result['file_path'],
        "data_processamento": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        "dados_esperados": result['json_data'],
        "resumo_matches": {
            "total_campos": len(result['matches']),
            "campos_encontrados": sum(1 for match in result['matches'].values() if match['found']),
            "taxa_sucesso": f"{(sum(1 for match in result['matches'].values() if match['found']) / len(result['matches']) * 100):.1f}%" if len(result['matches']) > 0 else "0.0%"
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
print(f"\n=== RELATÓRIO RESUMIDO POR EDITAL ===")
print(f"Total de editais: {len(edital_stats)}")
print(f"Total de documentos: {len(all_results)}")

for edital_name, stats in edital_stats.items():
    display_name = "Arquivos Diretos" if edital_name == 'root' else edital_name
    print(f"\n🏛️ {display_name}:")
    print(f"  📄 Documentos: {stats['total_documents']}")
    print(f"  ✅ Taxa de sucesso: {stats['success_rate']:.1f}%")
    print(f"  🔍 Campos: {stats['fields_found']}/{stats['total_fields']}")

print(f"\n📊 Relatório detalhado salvo em: {nome_arquivo_saida}")
print(f"📊 Resumo por edital salvo em: {edital_consolidado_path}")
print(f"🔍 Processamento concluído com sucesso!")