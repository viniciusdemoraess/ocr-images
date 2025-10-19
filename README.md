# Script OCR com PaddleOCR

Este script utiliza PaddleOCR para extrair texto de documentos (PDFs e imagens) e compara com valores esperados definidos em arquivos JSON.

## 📋 Funcionalidades

- **Extração de texto**: Utiliza PaddleOCR para extrair texto de documentos
- **Busca inteligente**: Compara texto extraído com valores esperados usando similaridade
- **Relatórios detalhados**: Gera relatórios em TXT e JSON com resultados da análise
- **Suporte múltiplos formatos**: PDF, JPEG, JPG, PNG
- **Análise de confiança**: Calcula similaridade e confiança OCR para cada match

## 🚀 Instalação

### 1. Instalar dependências

```bash
pip install paddlepaddle
pip install paddleocr
```

### 2. Configurar ambiente (opcional)
```bash
# Criar virtual environment
python -m venv venv

# Ativar virtual environment (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install paddlepaddle paddleocr
```

## 📁 Estrutura de Arquivos

O script processa arquivos na pasta `input_docs/`. Para cada documento, deve existir um arquivo JSON correspondente com os valores a serem pesquisados.

```
input_docs/
├── documento1.pdf          # Documento a ser processado
├── documento1.json         # Valores esperados para documento1
├── nota_fiscal.jpeg        # Imagem a ser processada
├── nota_fiscal.json        # Valores esperados para nota_fiscal
└── ...
```

### Exemplo de arquivo JSON com valores esperados:

```json
{
  "cnpj": "12.345.678/0001-90",
  "razao_social": "Empresa Exemplo LTDA",
  "valor_total": "1.250,00",
  "numero_nota": "123456",
  "data_emissao": "15/10/2024"
}
```

**⚠️ Importante**: Campos com valores `null`, `""` ou `"null"` são automaticamente ignorados na análise.

## 🔧 Como Executar

1. **Preparar os arquivos**:
   - Coloque seus documentos (PDF/imagens) na pasta `input_docs/`
   - Crie arquivos JSON correspondentes com os valores a serem pesquisados

2. **Executar o script**:
   ```bash
   python teste_ocr.py
   ```

3. **Verificar resultados**:
   - Relatório detalhado: `resultado_ocr_completo.txt`
   - JSONs individuais: pasta `resultados_json/`

## 📊 Resultados

### Arquivos gerados:

- **`resultado_ocr_completo.txt`**: Relatório detalhado em texto
- **`resultados_json/`**: Pasta com JSONs individuais para cada documento processado

### Estrutura do JSON de resultado:

```json
{
  "arquivo_processado": "nota_fiscal.jpeg",
  "resumo_matches": {
    "total_campos": 5,
    "campos_encontrados": 4,
    "taxa_sucesso": "80.0%"
  },
  "detalhes_matches": {
    "cnpj": {
      "encontrado": true,
      "valor_esperado": "12.345.678/0001-90",
      "valor_extraido": "12.345.678/0001-90",
      "similaridade_percentual": "95.0%",
      "confianca_ocr_percentual": "98.5%"
    }
  }
}
```

## ⚙️ Configurações

### Parâmetros ajustáveis no código:

- **`threshold`**: Limite de similaridade (padrão: 0.7 = 70%)
- **`lang`**: Idioma do OCR (padrão: 'pt' para português)
- **`use_angle_cls`**: Correção de rotação (padrão: True)

### Exemplo de personalização:
```python
# No início do arquivo teste_ocr.py
ocr = PaddleOCR(use_angle_cls=True, lang='pt')

# Para alterar o threshold de similaridade
matches = find_matches_in_text(extracted_texts, json_data, threshold=0.8)
```

## 🔍 Como Funciona

1. **Leitura**: O script lê todos os arquivos da pasta `input_docs/`
2. **OCR**: Executa PaddleOCR em cada documento
3. **Normalização**: Limpa e normaliza o texto extraído
4. **Comparação**: Compara com valores esperados usando:
   - Similaridade de sequência
   - Busca por contenção de substring
5. **Relatório**: Gera relatórios detalhados com resultados

## 📝 Exemplos de Uso

### Exemplo 1: Nota Fiscal
```
input_docs/
├── nota_fiscal_123.pdf
└── nota_fiscal_123.json
```

**nota_fiscal_123.json**:
```json
{
  "numero_nota": "000123",
  "cnpj_emissor": "11.222.333/0001-44",
  "valor_total": "R$ 1.500,00"
}
```

### Exemplo 2: Recibo
```
input_docs/
├── recibo_pagamento.jpeg
└── recibo_pagamento.json
```

**recibo_pagamento.json**:
```json
{
  "beneficiario": "João Silva",
  "valor": "500,00",
  "data": "10/10/2024"
}
```

## 🐛 Troubleshooting

### Problemas comuns:

1. **Erro de importação PaddleOCR**:
   ```bash
   pip install --upgrade paddlepaddle paddleocr
   ```

2. **Baixa precisão OCR**:
   - Verifique qualidade da imagem
   - Ajuste threshold de similaridade
   - Use imagens com maior resolução

3. **Campos não encontrados**:
   - Verifique se os valores no JSON estão corretos
   - Valores `null`, `""` são ignorados automaticamente
   - Ajuste threshold se necessário

## 📄 Requisitos do Sistema

- Python 3.7+
- PaddlePaddle
- PaddleOCR
- Espaço em disco suficiente para modelos OCR (~100MB)

## 🤝 Contribuição

Para contribuir com melhorias:
1. Faça fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request