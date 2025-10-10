from paddleocr import PaddleOCR
import pprint

ocr = PaddleOCR(use_angle_cls=True, lang='pt')

img_path = 'nota_fiscal_comagran.jpeg'

result = ocr.predict(img_path)

print("==== Estrutura retornada pelo OCR ====")
pprint.pp(result)
print("======================================")

texto_extraido = []

for res in result:
    if isinstance(res, dict) and 'data' in res:
        linhas = res['data']
    elif isinstance(res, list):
        linhas = res
    elif isinstance(res, dict) and 'rec_texts' in res:
        for i, texto in enumerate(res['rec_texts']):
            confianca = res['rec_scores'][i] if 'rec_scores' in res else 0.0
            print(f"Texto: {texto} | Confiança: {confianca:.2f}")
            texto_extraido.append(f"{texto} (Confiança: {confianca:.2f})")
        continue
    else:
        continue
    
    print(linhas)
    for linha in linhas:
        texto = linha.get('text', '')
        confianca = linha.get('confidence', 0.0)
        print(f"Texto: {texto} | Confiança: {confianca:.2f}")
        texto_extraido.append(f"{texto} (Confiança: {confianca:.2f})")

nome_arquivo_saida = 'resultado_ocr_nota_fiscal.txt'
with open(nome_arquivo_saida, 'w', encoding='utf-8') as arquivo:
    arquivo.write("=== RESULTADO DO OCR - NOTA FISCAL COMAGRAN ===\n\n")
    arquivo.write(f"Arquivo processado: {img_path}\n")
    arquivo.write(f"Total de textos extraídos: {len(texto_extraido)}\n\n")
    arquivo.write("=== TEXTOS EXTRAÍDOS ===\n\n")
    
    for i, texto in enumerate(texto_extraido, 1):
        arquivo.write(f"{i:03d}. {texto}\n")
    
    arquivo.write("\n=== TEXTO CORRIDO (SEM CONFIANÇA) ===\n\n")
    textos_limpos = [linha.split(' (Confiança:')[0] for linha in texto_extraido]
    arquivo.write('\n'.join(textos_limpos))

print(f"\nOCR concluído com sucesso!")
print(f"Resultado salvo em: {nome_arquivo_saida}")
print(f"Total de textos extraídos: {len(texto_extraido)}")