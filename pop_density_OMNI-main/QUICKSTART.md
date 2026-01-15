# 🚀 Guia Rápido - AL Drones Population Analysis Tool

## 📋 Pré-requisitos

- Python 3.8 ou superior
- 4GB RAM (mínimo)
- Conexão com internet (para download de dados IBGE)

## ⚡ Instalação Rápida

### Opção 1: Via pip (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/aldrones/population-analysis-tool.git
cd population-analysis-tool

# 2. Crie um ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Execute a aplicação
streamlit run app.py
```

### Opção 2: Via Docker

```bash
# 1. Clone o repositório
git clone https://github.com/aldrones/population-analysis-tool.git
cd population-analysis-tool

# 2. Execute com Docker Compose
docker-compose up -d

# 3. Acesse no navegador
# http://localhost:8501
```

## 🎯 Uso Básico

### Interface Web (Streamlit)

1. **Acesse a aplicação**
   - Abra o navegador em `http://localhost:8501`

2. **Etapa 1: Gerar Margens de Segurança**
   - Faça upload do KML com geometria de voo
   - Configure os parâmetros:
     - Flight Geography Buffer (m)
     - Altura de Voo (m)
     - Contingency Volume (m)
     - Estilo de Cantos (square/rounded)
   - Clique em "Gerar Margens de Segurança"
   - Download do KML gerado

3. **Etapa 2: Análise Populacional**
   - Use o KML da Etapa 1 (ou faça novo upload)
   - Clique em "Iniciar Análise Populacional"
   - Aguarde o processamento (pode levar minutos)
   - Visualize mapas e estatísticas
   - Download dos resultados

### Linha de Comando

#### Script 1: Gerar Margens de Segurança

```bash
python src/generate_safety_margins.py input.kml \
  --height 100 \
  --cv-size 50 \
  --corner-style square \
  --output safety_margins.kml
```

**Parâmetros:**
- `input.kml`: Arquivo KML de entrada
- `--height`: Altura de voo em metros (padrão: 100)
- `--cv-size`: Tamanho do Contingency Volume em metros (padrão: 50)
- `--fg-size`: Buffer do Flight Geography (padrão: 0)
- `--adj-size`: Buffer da Adjacent Area (padrão: 5000)
- `--corner-style`: Estilo dos cantos - `square` ou `rounded` (padrão: square)
- `--output`: Arquivo KML de saída (opcional)

#### Script 2: Análise Populacional

```bash
python src/population_analysis.py safety_margins.kml \
  --output-dir results/
```

**Parâmetros:**
- `safety_margins.kml`: KML com as 4 camadas de segurança
- `--output-dir`: Diretório para salvar os mapas (padrão: results/)

## 📊 Resultados

### Arquivos Gerados

**Etapa 1:**
- `*_safety_margins.kml`: KML com 4 camadas:
  - Flight Geography (verde)
  - Contingency Volume (amarelo)
  - Ground Risk Buffer (vermelho)
  - Adjacent Area (azul)

**Etapa 2:**
- `map_flight_geography.png`: Mapa de densidade - Flight Geography
- `map_ground_risk_buffer.png`: Mapa de densidade - Ground Risk Buffer
- `map_adjacent_area.png`: Mapa de densidade - Adjacent Area

### Estatísticas Calculadas

Para cada camada:
- **População Total**: Número de habitantes
- **Área Total**: Área em km²
- **Densidade Média**: Habitantes por km²

## 🎨 Exemplo Completo

```bash
# 1. Gerar margens de segurança
python src/generate_safety_margins.py examples/flight_path.kml \
  --height 120 \
  --cv-size 75 \
  --corner-style square \
  --output output/safety_margins.kml

# Resultado:
# ✓ Safety margins KML generated: output/safety_margins.kml
#   - Flight Geography: 0m buffer
#   - Contingency Volume: 75m buffer
#   - Ground Risk Buffer: 120.00m (height: 120m)
#   - Adjacent Area: 5000m buffer

# 2. Analisar densidade populacional
python src/population_analysis.py output/safety_margins.kml \
  --output-dir results/

# Resultado:
# ✓ Quadrant index loaded: 2574 cells
# ✓ Identified 3 relevant quadrants: [1023, 1024, 1025]
# ✓ Total cells: 4523
# ✓ Map saved: results/map_flight_geography.png
# ...
# ✓ Analysis complete!
```

## 🔧 Configurações Avançadas

### Ajustar Timeout de Download

Se o download dos dados IBGE falhar, ajuste o timeout:

```python
# Em src/population_analysis.py, linha ~70
resp = requests.get(url, timeout=120)  # Aumentar de 60 para 120
```

### Ajustar Qualidade dos Mapas

```python
# Em src/population_analysis.py, linha ~190
plt.savefig(output_path, dpi=300, bbox_inches='tight')  # DPI maior = melhor qualidade
```

### Cache de Dados IBGE

Os dados são salvos em `dados_ibge/` para reuso. Para limpar:

```bash
rm -rf dados_ibge/
```

## ❓ FAQ

### Por que o processamento é lento?

A análise populacional pode levar vários minutos porque:
1. Download de grids IBGE (primeira vez)
2. Processamento de milhares de células
3. Geração de mapas de alta resolução

**Solução:** Os dados são cached. Execuções subsequentes serão mais rápidas.

### Erro: "No relevant grids found"

**Causa:** O polígono está fora do Brasil ou muito pequeno.

**Solução:** 
- Verifique coordenadas do KML
- Aumente o Contingency Volume
- Verifique se o KML usa projeção WGS84

### Erro: "Memory error"

**Causa:** Área de análise muito grande.

**Solução:**
- Dividir análise em áreas menores
- Aumentar RAM do sistema
- Reduzir área de Adjacent Area

### Como interpretar densidade populacional?

- **< 50 hab/km²**: Área rural
- **50-500 hab/km²**: Subúrbio
- **500-5000 hab/km²**: Urbano
- **> 5000 hab/km²**: Centro urbano denso

### Posso usar para outros países?

O sistema atual usa dados do IBGE (Brasil). Para outros países:
- Adaptar fonte de dados
- Ajustar projeção cartográfica
- Modificar URLs de download

## 🆘 Suporte

### Problemas técnicos:
- GitHub Issues: [criar issue](https://github.com/aldrones/population-analysis-tool/issues)
- Email: contato@aldrones.com.br

### Consultoria:
Para análises customizadas ou suporte especializado, entre em contato:
- 🌐 [aldrones.com.br](https://aldrones.com.br)
- 📧 contato@aldrones.com.br
- 📱 [@aldrones_aviation](https://instagram.com/aldrones_aviation)

## 📚 Recursos Adicionais

- [Documentação Completa](README.md)
- [Guia de Deploy](DEPLOYMENT.md)
- [IBGE Grade Estatística](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-grade-estatistica.html)
- [RBAC 94/2022 - ANAC](https://www.anac.gov.br/)

---

**Desenvolvido por AL Drones** - Líder em Certificação de Drones 🚁
