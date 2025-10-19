# Script OCR com PaddleOCR

Este script utiliza PaddleOCR para extrair texto de documentos (PDFs e imagens) e compara com valores esperados definidos em arquivos JSON. **Suporta análise por editais através de subpastas organizadas.**

## 📋 Funcionalidades

- **Extração de texto**: Utiliza PaddleOCR para extrair texto de documentos
- **Busca inteligente**: Compara texto extraído com valores esperados usando similaridade
- **Análise por editais**: Processa documentos organizados em subpastas (editais) com estatísticas consolidadas
- **Relatórios detalhados**: Gera relatórios em TXT e JSON com resultados da análise por edital
- **Compatibilidade**: Funciona com arquivos diretos em `input_docs/` ou organizados em subpastas
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

### Opção 1: Organização por Editais (Recomendado)

Organize seus documentos em subpastas dentro de `input_docs/`, onde cada subpasta representa um edital:

```
input_docs/
├── edital_001/
│   ├── documento1.pdf          # Documento do edital 001
│   ├── documento1.json         # Valores esperados para documento1
│   ├── nota_fiscal.jpeg        # Outro documento do edital 001
│   └── nota_fiscal.json        # Valores esperados para nota_fiscal
├── edital_002/
│   ├── recibo.pdf              # Documento do edital 002
│   ├── recibo.json             # Valores esperados para recibo
│   └── contrato.jpeg           # Outro documento do edital 002
└── licitacao_2025/
    ├── proposta.pdf
    └── proposta.json
```

### Opção 2: Arquivos Diretos (Compatibilidade)

Funciona como antes, com arquivos diretos em `input_docs/`:

```
input_docs/
├── documento1.pdf          # Documento a ser processado
├── documento1.json         # Valores esperados para documento1
├── nota_fiscal.jpeg        # Imagem a ser processada
└── nota_fiscal.json        # Valores esperados para nota_fiscal
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
   - **Para análise por editais**: Crie subpastas em `input_docs/` para cada edital
   - **Para análise simples**: Coloque arquivos diretamente em `input_docs/`
   - Crie arquivos JSON correspondentes com os valores a serem pesquisados

2. **Executar o script**:
   ```bash
   python teste_ocr.py
   ```

3. **Verificar resultados**:
   - Relatório detalhado: `resultado_ocr_completo.txt`
   - Resumo por edital: `resultados_json/resumo_por_edital.json`
   - JSONs individuais: pasta `resultados_json/`

## 📊 Resultados

### Arquivos gerados:

- **`resultado_ocr_completo.txt`**: Relatório detalhado organizado por edital
- **`resultados_json/resumo_por_edital.json`**: Estatísticas consolidadas por edital
- **`resultados_json/`**: JSONs individuais para cada documento processado

### Exemplo de resumo por edital (`resumo_por_edital.json`):

```json
{
  "data_processamento": "19/10/2025 14:30:45",
  "total_editais": 2,
  "total_documentos": 5,
  "estatisticas_por_edital": {
    "edital_001": {
      "nome_edital": "edital_001",
      "total_documentos": 3,
      "total_campos": 15,
      "campos_encontrados": 12,
      "taxa_sucesso_percentual": "80.0%",
      "taxa_sucesso_decimal": 0.8
    },
    "edital_002": {
      "nome_edital": "edital_002",
      "total_documentos": 2,
      "total_campos": 10,
      "campos_encontrados": 9,
      "taxa_sucesso_percentual": "90.0%",
      "taxa_sucesso_decimal": 0.9
    }
  }
}
```

### Estrutura do JSON individual:

```json
{
  "arquivo_processado": "nota_fiscal.jpeg",
  "edital": "edital_001",
  "data_processamento": "19/10/2025 14:30:45",
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

## 🔍 Como Funciona

1. **Detecção**: O script detecta automaticamente se há subpastas (editais) ou arquivos diretos
2. **Processamento por Edital**: Se houver subpastas, processa cada uma como um edital separado
3. **OCR**: Executa PaddleOCR em cada documento
4. **Normalização**: Limpa e normaliza o texto extraído
5. **Comparação**: Compara com valores esperados usando similaridade
6. **Consolidação**: Calcula estatísticas por edital e geral
7. **Relatórios**: Gera relatórios detalhados e resumos consolidados

## 📈 Relatórios Console

O script exibe no console um resumo por edital:

```
=== RELATÓRIO RESUMIDO POR EDITAL ===
Total de editais: 2
Total de documentos: 5

🏛️ edital_001:
  📄 Documentos: 3
  ✅ Taxa de sucesso: 80.0%
  🔍 Campos: 12/15

🏛️ edital_002:
  📄 Documentos: 2
  ✅ Taxa de sucesso: 90.0%
  🔍 Campos: 9/10
```

## 📝 Exemplos de Uso

### Exemplo 1: Análise por Editais
```
input_docs/
├── licitacao_obras_2025/
│   ├── proposta_empresa_a.pdf
│   ├── proposta_empresa_a.json
│   ├── proposta_empresa_b.pdf
│   └── proposta_empresa_b.json
└── pregao_servicos_2025/
    ├── orcamento_fornecedor_x.jpeg
    ├── orcamento_fornecedor_x.json
    ├── orcamento_fornecedor_y.pdf
    └── orcamento_fornecedor_y.json
```

**proposta_empresa_a.json**:
```json
{
  "cnpj_proponente": "11.222.333/0001-44",
  "valor_proposta": "R$ 150.000,00",
  "prazo_execucao": "90 dias"
}
```

### Exemplo 2: Modo Compatibilidade
```
input_docs/
├── nota_fiscal_123.pdf
├── nota_fiscal_123.json
├── recibo_pagamento.jpeg
└── recibo_pagamento.json
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

4. **Subpastas não reconhecidas**:
   - Certifique-se que há pelo menos uma subpasta em `input_docs/`
   - Evite misturar arquivos diretos com subpastas

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