from paddleocr import PaddleOCR
import pprint
import os
import json
import re
from difflib import SequenceMatcher
from datetime import datetime

# Importações para geração de PDF
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ Bibliotecas de PDF não encontradas. Instale com: pip install reportlab")

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

def create_header_footer(canvas, doc):
    """Cria cabeçalho e rodapé personalizados para o PDF"""
    canvas.saveState()
    
    # Cabeçalho
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(colors.darkblue)
    canvas.drawString(inch, A4[1] - 0.5*inch, "Relatório de Processamento OCR")
    
    # Rodapé
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(inch, 0.5*inch, f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    canvas.drawRightString(A4[0] - inch, 0.5*inch, f"Página {doc.page}")
    
    canvas.restoreState()

def generate_pdf_report(json_data, output_path):
    """Gera relatório PDF completo baseado nos dados do JSON"""
    if not PDF_AVAILABLE:
        print("❌ Não foi possível gerar PDF - bibliotecas não instaladas")
        return None
    
    # Configura estilos
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkgreen
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=5
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    # Cria o documento PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=1.2*inch,
        bottomMargin=inch
    )
    
    # Lista para armazenar os elementos do PDF
    story = []
    
    # Título principal
    title = Paragraph("Relatório de Processamento OCR", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Tabela de resumo geral
    resumo_data = [
        ['Métrica', 'Valor'],
        ['Data de Processamento', json_data['data_processamento']],
        ['Total de Editais', str(json_data['total_editais'])],
        ['Total de Documentos', str(json_data['total_documentos'])],
    ]
    
    resumo_table = Table(resumo_data, colWidths=[3*inch, 2*inch])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(resumo_table)
    story.append(Spacer(1, 30))
    
    # Seção de análise por edital
    section_header = Paragraph("Análise Detalhada por Edital", section_style)
    story.append(section_header)
    
    # Cria tabela com estatísticas detalhadas
    stats_data = [['Edital', 'Documentos', 'Campos Total', 'Campos Encontrados', 'Taxa de Sucesso']]
    
    total_documentos = 0
    total_campos = 0
    total_encontrados = 0
    
    for edital_name, stats in json_data['estatisticas_por_edital'].items():
        stats_data.append([
            stats['nome_edital'],
            str(stats['total_documentos']),
            str(stats['total_campos']),
            str(stats['campos_encontrados']),
            stats['taxa_sucesso_percentual']
        ])
        
        total_documentos += stats['total_documentos']
        total_campos += stats['total_campos']
        total_encontrados += stats['campos_encontrados']
    
    # Linha de totais
    taxa_geral = (total_encontrados / total_campos * 100) if total_campos > 0 else 0
    stats_data.append([
        'TOTAL GERAL',
        str(total_documentos),
        str(total_campos),
        str(total_encontrados),
        f'{taxa_geral:.1f}%'
    ])
    
    # Ajuste de larguras: aumenta colunas de campos e taxa para melhorar legibilidade
    stats_table = Table(stats_data, colWidths=[2.2*inch, 1.0*inch, 1.4*inch, 1.6*inch, 1.2*inch])
    # Paleta de cores padronizada: header azul escuro, corpo branco, linha de total azul claro, grid cinza claro
    header_bg = colors.HexColor('#1f4e79')  # azul escuro
    body_bg = colors.whitesmoke
    total_bg = colors.HexColor('#cfe2f3')  # azul claro
    grid_color = colors.HexColor('#d9d9d9')

    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), body_bg),
        ('BACKGROUND', (0, -1), (-1, -1), total_bg),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, grid_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Análise individual por edital
    for edital_name, stats in json_data['estatisticas_por_edital'].items():
        story.append(PageBreak())
        
        # Título do edital
        edital_title = Paragraph(f"Análise: {stats['nome_edital']}", subtitle_style)
        story.append(edital_title)
        story.append(Spacer(1, 15))
        
        # Informações detalhadas do edital
        info_text = f"""
        <b>Resumo do Edital:</b><br/>
        • Nome: {stats['nome_edital']}<br/>
        • Total de documentos processados: {stats['total_documentos']}<br/>
        • Total de campos analisados: {stats['total_campos']}<br/>
        • Campos encontrados com sucesso: {stats['campos_encontrados']}<br/>
        • Taxa de sucesso: {stats['taxa_sucesso_percentual']}<br/><br/>
        
        <b>Interpretação dos Resultados:</b><br/>
        """
        
        # Adiciona interpretação baseada na taxa de sucesso
        taxa_decimal = stats['taxa_sucesso_decimal']
        if taxa_decimal >= 0.9:
            interpretacao = "Excelente! A taxa de sucesso indica um processamento muito eficiente dos documentos."
        elif taxa_decimal >= 0.7:
            interpretacao = "Bom! A maioria dos campos foi identificada corretamente, mas há espaço para melhorias."
        elif taxa_decimal >= 0.5:
            interpretacao = "Moderado. Cerca de metade dos campos foi identificada. Recomenda-se revisar a qualidade das imagens."
        else:
            interpretacao = "Baixo. A taxa de sucesso indica possíveis problemas na qualidade das imagens ou na configuração do OCR."
        
        info_text += f"• {interpretacao}<br/><br/>"
        
        # Recomendações
        info_text += "<b>Recomendações:</b><br/>"
        if taxa_decimal < 0.7:
            info_text += "• Verificar a qualidade e resolução das imagens<br/>"
            info_text += "• Considerar pré-processamento das imagens<br/>"
            info_text += "• Revisar os padrões de busca utilizados<br/>"
        else:
            info_text += "• Manter o padrão atual de processamento<br/>"
            info_text += "• Considerar otimizações pontuais nos campos não encontrados<br/>"
        
        info_paragraph = Paragraph(info_text, normal_style)
        story.append(info_paragraph)
        story.append(Spacer(1, 20))
    
    # Conclusões e recomendações gerais
    story.append(PageBreak())
    conclusion_title = Paragraph("Conclusões e Recomendações Gerais", subtitle_style)
    story.append(conclusion_title)
    
    conclusion_text = f"""
    <b>Análise Geral do Processamento:</b><br/><br/>
    
    O sistema de OCR processou um total de <b>{json_data['total_documentos']} documentos</b> 
    distribuídos em <b>{json_data['total_editais']} editais</b> diferentes. 
    
    A taxa de sucesso geral do sistema foi de <b>{taxa_geral:.1f}%</b>, 
    indicando um nível {'excelente' if taxa_geral >= 90 else 'bom' if taxa_geral >= 70 else 'moderado' if taxa_geral >= 50 else 'baixo'} 
    de eficiência na extração de informações.<br/><br/>
    
    <b>Principais Observações:</b><br/>
    • Total de campos analisados: {total_campos}<br/>
    • Campos identificados com sucesso: {total_encontrados}<br/>
    • Campos não identificados: {total_campos - total_encontrados}<br/><br/>
    
    <b>Recomendações para Melhorias:</b><br/>
    • Implementar validação cruzada dos resultados<br/>
    • Considerar treinamento específico do modelo OCR para documentos similares<br/>
    • Estabelecer pipeline de pré-processamento de imagens<br/>
    • Criar sistema de feedback para melhoria contínua<br/>
    • Desenvolver métricas de qualidade por tipo de documento<br/><br/>
    
    <b>Próximos Passos:</b><br/>
    • Analisar individualmente os documentos com menor taxa de sucesso<br/>
    • Implementar melhorias baseadas nos padrões identificados<br/>
    • Estabelecer processo de monitoramento contínuo da qualidade<br/>
    """
    
    conclusion_paragraph = Paragraph(conclusion_text, normal_style)
    story.append(conclusion_paragraph)
    
    # Constrói o PDF
    doc.build(story, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
    
    return output_path

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

# Gera o relatório PDF baseado no JSON consolidado
if PDF_AVAILABLE:
    try:
        # Define o caminho do PDF
        pdf_path = edital_consolidado_path.replace('.json', '_relatorio.pdf')
        
        # Gera o PDF
        generate_pdf_report(edital_consolidado, pdf_path)
        print(f"📄 Relatório PDF gerado: {pdf_path}")
        
        # Exibe informações sobre o arquivo gerado
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"📏 Tamanho do arquivo PDF: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
    except Exception as e:
        print(f"⚠️ Erro ao gerar PDF: {e}")
        print("💡 Certifique-se de que as dependências estão instaladas: pip install reportlab")
else:
    print("💡 Para gerar relatório PDF, instale as dependências: pip install reportlab")

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