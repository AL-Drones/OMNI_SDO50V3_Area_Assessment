# 📚 API Documentation - AL Drones Population Analysis Tool

## Módulo 1: generate_safety_margins

### `generate_safety_margins()`

Gera camadas de margem de segurança a partir de um arquivo KML.

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `input_kml_path` | `str` | *obrigatório* | Caminho para o arquivo KML de entrada |
| `output_kml_path` | `str` | `None` | Caminho para o arquivo KML de saída (se None, gera automaticamente) |
| `fg_size` | `float` | `0` | Tamanho do buffer Flight Geography em metros |
| `height` | `float` | `100` | Altura de voo em metros |
| `cv_size` | `float` | `50` | Tamanho do buffer Contingency Volume em metros |
| `adj_size` | `float` | `5000` | Tamanho do buffer Adjacent Area em metros |
| `corner_style` | `str` | `'square'` | Estilo dos cantos: 'square' ou 'rounded' |

**Retorna:**
- `str`: Caminho do arquivo KML gerado

**Exceções:**
- `FileNotFoundError`: Arquivo KML de entrada não encontrado
- `ValueError`: Parâmetros inválidos
- `IOError`: Erro ao salvar arquivo de saída

**Exemplo:**

```python
from src.generate_safety_margins import generate_safety_margins

output_path = generate_safety_margins(
    input_kml_path='input.kml',
    height=120,
    cv_size=75,
    corner_style='square'
)

print(f"KML gerado: {output_path}")
```

---

### `calculate_grb_size()`

Calcula o tamanho do Ground Risk Buffer baseado na altura de voo.

**Fórmula:**
- Se altura ≤ 120m: GRB = altura
- Se altura > 120m: GRB = 25 × √(2 × altura / 9.81) + 1.485

**Parâmetros:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `height` | `float` | Altura de voo em metros |

**Retorna:**
- `float`: Tamanho do GRB em metros

**Exemplo:**

```python
from src.generate_safety_margins import calculate_grb_size

grb = calculate_grb_size(150)
print(f"GRB para 150m: {grb:.2f}m")
# Output: GRB para 150m: 139.56m
```

---

## Módulo 2: population_analysis

### `analyze_population()`

Realiza análise de densidade populacional das camadas de segurança.

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `kml_file` | `str` | *obrigatório* | Caminho para o KML com margens de segurança |
| `output_dir` | `str` | `'results'` | Diretório para salvar mapas gerados |

**Retorna:**
- `dict`: Estatísticas por camada
  ```python
  {
      'Flight Geography': {
          'total_pessoas': int,
          'area_total_km2': float,
          'densidade_media': float
      },
      'Ground Risk Buffer': {...},
      'Adjacent Area': {...}
  }
  ```

**Exceções:**
- `FileNotFoundError`: KML não encontrado
- `ValueError`: KML inválido ou sem camadas necessárias
- `ConnectionError`: Falha ao baixar dados IBGE

**Exemplo:**

```python
from src.population_analysis import analyze_population

results = analyze_population(
    kml_file='safety_margins.kml',
    output_dir='results/'
)

for layer, stats in results.items():
    print(f"{layer}:")
    print(f"  População: {stats['total_pessoas']:,}")
    print(f"  Densidade: {stats['densidade_media']:.2f} hab/km²")
```

---

### `extrair_layers_kml()`

Extrai e unifica geometrias de camadas específicas do KML.

**Parâmetros:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `kml_filename` | `str` | Caminho do arquivo KML |
| `layer_names` | `list[str]` | Lista de nomes das camadas a extrair |

**Retorna:**
- `dict`: Dicionário {nome_camada: geometria_unificada}

**Exemplo:**

```python
from src.population_analysis import extrair_layers_kml

layers = extrair_layers_kml(
    'safety_margins.kml',
    ['Flight Geography', 'Contingency Volume']
)

for name, geom in layers.items():
    print(f"{name}: {geom.type}, área = {geom.area:.2f}")
```

---

### `carregar_grid_ibge()`

Baixa e carrega grid estatístico do IBGE com cache.

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `grade_id` | `int` | *obrigatório* | ID do quadrante IBGE |
| `use_cache` | `bool` | `True` | Usar cache em memória |

**Retorna:**
- `tuple`: (GeoDataFrame, grade_id) ou (None, grade_id) se erro

**Cache:**
- Grids carregados são mantidos em `_GRID_CACHE`
- Acelera análises subsequentes
- Limpar cache: reiniciar aplicação

**Exemplo:**

```python
from src.population_analysis import carregar_grid_ibge

grid, grade_id = carregar_grid_ibge(1023)

if grid is not None:
    print(f"Grade {grade_id} carregada: {len(grid)} células")
    print(f"População total: {grid['TOTAL'].sum()}")
```

---

### `identificar_grades_relevantes()`

Identifica quais quadrantes IBGE intersectam com área de interesse.

**Parâmetros:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `area_geom` | `shapely.geometry` | Geometria da área (WGS84) |

**Retorna:**
- `list[int]`: Lista de IDs de quadrantes relevantes

**Exemplo:**

```python
from shapely.geometry import Point
from src.population_analysis import identificar_grades_relevantes

# Criar buffer de 5km ao redor de um ponto
ponto = Point(-46.6333, -23.5505)  # São Paulo
area = ponto.buffer(0.05)  # ~5km em graus

grades = identificar_grades_relevantes(area)
print(f"Quadrantes relevantes: {grades}")
```

---

### `processar_todas_grades()`

Processa todos os grids relevantes e gera mapa de densidade.

**Parâmetros:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `area_geom` | `shapely.geometry` | Geometria da área a analisar |
| `titulo` | `str` | Título do mapa |
| `layers_poligonos` | `dict` | Dicionário de camadas para desenhar |
| `layers_para_mostrar` | `list[str]` | Lista de camadas a exibir |
| `output_path` | `str` | Caminho para salvar mapa (opcional) |

**Retorna:**
- `dict` ou `None`: Estatísticas se sucesso, None se falha

**Exemplo:**

```python
from src.population_analysis import (
    extrair_layers_kml,
    processar_todas_grades
)

layers = extrair_layers_kml('safety_margins.kml', ['Flight Geography'])

stats = processar_todas_grades(
    area_geom=layers['Flight Geography'],
    titulo="Densidade Populacional - Flight Geography",
    layers_poligonos=layers,
    layers_para_mostrar=['Flight Geography'],
    output_path='map.png'
)

if stats:
    print(f"População: {stats['total_pessoas']}")
```

---

## Estruturas de Dados

### Camadas KML

As 4 camadas de segurança seguem esta hierarquia:

```
Flight Geography (menor)
├── Contingency Volume
    ├── Ground Risk Buffer
        └── Adjacent Area (maior)
```

**Propriedades de cada camada:**

```python
STYLES = {
    'Flight Geography': {
        'fill': '3300ff00',      # Verde translúcido
        'outline': 'ff00ff00',   # Verde sólido
        'width': 2
    },
    'Contingency Volume': {
        'fill': '1a00ffff',      # Amarelo translúcido
        'outline': 'ff00ffff',   # Amarelo sólido
        'width': 2
    },
    'Ground Risk Buffer': {
        'fill': '1a0000ff',      # Vermelho translúcido
        'outline': 'ff0000ff',   # Vermelho sólido
        'width': 2
    },
    'Adjacent Area': {
        'fill': '00ff0000',      # Azul translúcido (sem preenchimento)
        'outline': 'ffff0000',   # Azul sólido
        'width': 1
    }
}
```

### Grade Estatística IBGE

**Estrutura do GeoDataFrame:**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `ID_UNICO` | `str` | Identificador único da célula |
| `QUADRANTE` | `str` | ID do quadrante (ex: "ID_1023") |
| `TIPO` | `str` | Tipo de grid: "1" (rural) ou "2" (urbano) |
| `TOTAL` | `int` | População total da célula |
| `geometry` | `Polygon` | Geometria da célula (Albers) |

**Resolução:**
- Grid Tipo 1 (rural): 1km × 1km
- Grid Tipo 2 (urbano): 200m × 200m

---

## Constantes

### Projeções

```python
# SIRGAS 2000 / UTM zone 23S (métrica, para buffers)
EPSG_31983 = 'epsg:31983'

# WGS 84 (geográfica, para KML)
EPSG_4326 = 'epsg:4326'

# Albers Equal Area Brasil (métrica, dados IBGE)
ALBERS_BR = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)
```

### URLs IBGE

```python
# Grid 500km (índice espacial)
IBGE_500KM_URL = (
    "https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/"
    "grade_estatistica/censo_2022/grade_500km/BR500KM.zip"
)

# Grids por quadrante
IBGE_GRID_URL = (
    "https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/"
    "grade_estatistica/censo_2022/grade_estatistica/grade_id{grade_id}.zip"
)
```

---

## Uso como Biblioteca Python

### Instalação

```bash
pip install -e .
```

### Exemplo Completo

```python
#!/usr/bin/env python3
"""Exemplo de uso da biblioteca AL Drones."""

from src.generate_safety_margins import generate_safety_margins
from src.population_analysis import analyze_population

def main():
    # Etapa 1: Gerar margens de segurança
    print("Gerando margens de segurança...")
    safety_kml = generate_safety_margins(
        input_kml_path='input_flight.kml',
        height=120,
        cv_size=50,
        corner_style='square'
    )
    print(f"✓ KML gerado: {safety_kml}")
    
    # Etapa 2: Analisar população
    print("\nAnalisando densidade populacional...")
    results = analyze_population(
        kml_file=safety_kml,
        output_dir='analysis_results/'
    )
    
    # Exibir resultados
    print("\n=== RESULTADOS ===")
    for layer, stats in results.items():
        print(f"\n{layer}:")
        print(f"  População Total: {int(stats['total_pessoas']):,} hab")
        print(f"  Área Total: {stats['area_total_km2']:.2f} km²")
        print(f"  Densidade Média: {stats['densidade_media']:.2f} hab/km²")
        
        # Classificação
        densidade = stats['densidade_media']
        if densidade < 50:
            classificacao = "Rural"
        elif densidade < 500:
            classificacao = "Subúrbio"
        elif densidade < 5000:
            classificacao = "Urbano"
        else:
            classificacao = "Centro Urbano Denso"
        
        print(f"  Classificação: {classificacao}")

if __name__ == '__main__':
    main()
```

---

## Tratamento de Erros

### Erros Comuns

```python
from src.generate_safety_margins import generate_safety_margins
from src.population_analysis import analyze_population

try:
    # Gerar margens
    safety_kml = generate_safety_margins(
        input_kml_path='input.kml',
        height=100
    )
except FileNotFoundError:
    print("❌ Arquivo KML não encontrado")
except ValueError as e:
    print(f"❌ Parâmetros inválidos: {e}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")

try:
    # Analisar população
    results = analyze_population(safety_kml)
except ConnectionError:
    print("❌ Falha ao conectar com IBGE")
    print("   Verifique sua conexão de internet")
except MemoryError:
    print("❌ Memória insuficiente")
    print("   Tente reduzir a área de análise")
except Exception as e:
    print(f"❌ Erro na análise: {e}")
```

---

## Performance

### Benchmarks

Configuração de teste:
- CPU: Intel i5 @ 2.4GHz
- RAM: 8GB
- SSD
- Conexão: 50 Mbps

| Operação | Tempo Médio | Cache |
|----------|-------------|-------|
| Gerar margens de segurança | 2-5s | N/A |
| Download grid IBGE (primeiro) | 30-60s | Não |
| Carregar grid IBGE (cache) | 1-2s | Sim |
| Processar 1000 células | 5-10s | N/A |
| Gerar mapa | 10-20s | N/A |
| **Análise completa** | **3-5 min** | **Primeira vez** |
| **Análise completa** | **1-2 min** | **Com cache** |

### Otimizações

```python
# Usar cache de grids
from src.population_analysis import carregar_grid_ibge

# Primeira chamada: download
grid1, _ = carregar_grid_ibge(1023, use_cache=True)

# Segunda chamada: instantânea (cache)
grid2, _ = carregar_grid_ibge(1023, use_cache=True)

# Limpar cache se necessário
from src.population_analysis import _GRID_CACHE
_GRID_CACHE.clear()
```

---

## Referências

- [IBGE - Grade Estatística](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-grade-estatistica.html)
- [GeoPandas Documentation](https://geopandas.org/)
- [Shapely Manual](https://shapely.readthedocs.io/)
- [RBAC 94/2022 - ANAC](https://www.anac.gov.br/assuntos/legislacao/legislacao-1/rbha-e-rbac/rbac/rbac-94)

---

**© 2025 AL Drones** - Documentação da API v1.0
