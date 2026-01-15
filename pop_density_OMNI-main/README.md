# ALDrones Population Analysis Tool

Sistema de análise de densidade populacional para operações de drones, desenvolvido pela [AL Drones](https://aldrones.com.br/).

## 📋 Descrição

Este sistema processa arquivos KML de zonas de voo de drones e gera análises de densidade populacional usando dados do IBGE, auxiliando em estudos de risco para autorizações BVLOS.

**Fluxo de trabalho:**
1. **Etapa 1:** Upload de KML com geometria de voo → Gera KML com 4 camadas de segurança
2. **Etapa 2:** Análise populacional das camadas usando dados do IBGE Censo 2022

## 🚀 Funcionalidades

### Script 1: Geração de Margens de Segurança (`generate_safety_margins.py`)
- Processa KML de entrada (ponto ou polígono)
- Gera 4 camadas:
  - **Flight Geography** (verde): Área de voo
  - **Contingency Volume** (amarelo): Volume de contingência
  - **Ground Risk Buffer** (vermelho): Buffer de risco ao solo (calculado por altura)
  - **Adjacent Area** (azul): Área adjacente (5km do Contingency Volume)
- Permite escolha de cantos quadrados ou arredondados
- Cálculo automático de GRB baseado na altura de voo

### Script 2: Análise de Densidade Populacional (`population_analysis.py`)
- Carrega dados do IBGE (grade estatística 2022)
- Otimização com índice espacial (grid 500km)
- Gera 3 mapas de densidade populacional:
  1. Flight Geography
  2. Ground Risk Buffer
  3. Adjacent Area (anel)
- Estatísticas: população total, área, densidade média

## 📦 Estrutura do Projeto

```
aldrones-population-tool/
├── README.md
├── requirements.txt
├── .gitignore
├── app.py                          # Aplicação Streamlit
├── src/
│   ├── __init__.py
│   ├── generate_safety_margins.py  # Script 1
│   └── population_analysis.py      # Script 2
├── utils/
│   ├── __init__.py
│   └── kml_processing.py          # Funções auxiliares
├── assets/
│   └── logo.svg                   # Logo ALDrones
└── tests/
    ├── __init__.py
    └── test_scripts.py
```

## 🛠️ Instalação

### Requisitos
- Python 3.8+
- pip

### Instalação das dependências

```bash
# Clone o repositório
git clone https://github.com/aldrones/population-analysis-tool.git
cd population-analysis-tool

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

## 🎯 Como Usar

### Interface Web (Streamlit)

```bash
streamlit run app.py
```

Acesse: `http://localhost:8501`

### Linha de Comando

**Script 1 - Gerar Margens de Segurança:**
```bash
python src/generate_safety_margins.py input.kml --height 100 --cv-size 50 --corner-style square
```

**Script 2 - Análise Populacional:**
```bash
python src/population_analysis.py safety_margins.kml --output-dir results/
```

## 📊 Dados Utilizados

- **IBGE Grade Estatística 2022**
  - Resolução: 1km x 1km (rural) e 200m x 200m (urbano)
  - Projeção: Albers Equal Area (SIRGAS2000)
  - Fonte: https://geoftp.ibge.gov.br/

## 🎨 Identidade Visual

O projeto segue a identidade visual da AL Drones:
- **Cores principais:** Verde (#00ff00), Azul escuro
- **Logo:** Disponível em `assets/logo.svg`

## 📝 Licença

© 2025 AL Drones - Todos os direitos reservados

## 👥 Contato

**AL Drones - Líder em Certificação de Drones**

- Website: https://aldrones.com.br/
- Email: contato@aldrones.com.br
- Instagram: [@aldrones_aviation](https://www.instagram.com/aldrones_aviation/)
- LinkedIn: [AL Drones](https://www.linkedin.com/company/al-drones/)

## 🙏 Agradecimentos

Dados populacionais fornecidos pelo IBGE (Instituto Brasileiro de Geografia e Estatística).
