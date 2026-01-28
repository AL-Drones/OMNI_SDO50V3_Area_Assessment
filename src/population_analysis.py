"""
AL Drones - Population Analysis Tool
Analyzes population density in drone flight areas using IBGE data.
"""

import os
import argparse
import requests
import zipfile
import io
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap
import numpy as np


# Configuration
COLORS = {
    'Flight Geography': '#00AA00',  # Verde mais vibrante
    'Contingency Volume': '#FF8C00',  # Laranja mais vibrante
    'Ground Risk Buffer': '#DC143C',  # Vermelho mais vibrante
    'Adjacent Area': '#1E90FF',  # Azul mais vibrante
}

# Portuguese names mapping
NAMES_PT = {
    'Flight Geography': 'Geografia de Voo',
    'Contingency Volume': 'Volume de Contingência',
    'Ground Risk Buffer': 'Buffer de Risco no Solo',
    'Adjacent Area': 'Área Adjacente',
}

# Default buffer values (can be overridden)
DEFAULT_BUFFER_INFO = {
    'Flight Geography': {'buffer': 0, 'height': None},
    'Contingency Volume': {'buffer': 10, 'height': None},  # 10m buffer padrão
    'Ground Risk Buffer': {'buffer': 295, 'height': None},  # exemplo
    'Adjacent Area': {'buffer': 5000, 'height': None},  # 5km
}

ALBERS_BR = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 "
    "+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)

# Cache for loaded grids
_GRID_CACHE = {}
_QUADRANT_INDEX = None


def extrair_layers_kml(kml_filename, layer_names):
    """Extract and union geometries from KML layers."""
    gdf = gpd.read_file(kml_filename, driver='KML')
    layers_poligonos = {}
    
    for name in layer_names:
        sel = gdf[gdf['Name'] == name]
        if sel.empty:
            print(f"⚠ Layer '{name}' not found in KML.")
            continue
        
        sel = sel[sel.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        if sel.empty:
            print(f"⚠ Layer '{name}' has no polygons.")
            continue
        
        layers_poligonos[name] = sel.geometry.union_all()
        print(f"✓ Layer '{name}' extracted.")
    
    return layers_poligonos


def carregar_indice_quadrantes():
    """
    Load the 500km aggregated grid to use as spatial index for quadrants.
    This grid shows which quadrants (grade_id) exist and their boundaries.
    """
    global _QUADRANT_INDEX
    
    if _QUADRANT_INDEX is not None:
        return _QUADRANT_INDEX
    
    url = "https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/grade_estatistica/censo_2022/grade_500km/BR500KM.zip"
    pasta = "dados_ibge/grade_500km"
    shp_path = os.path.join(pasta, "BR500KM.shp")
    
    if not os.path.exists(shp_path):
        os.makedirs(pasta, exist_ok=True)
        print("⬇ Downloading 500km grid index (one-time operation)...")
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                z.extractall(pasta)
        except Exception as e:
            print(f"✗ Error downloading 500km grid: {e}")
            return None
    
    # Load and convert to WGS84 for easy intersection with KML polygons
    _QUADRANT_INDEX = gpd.read_file(shp_path).to_crs(epsg=4326)
    print(f"✓ Quadrant index loaded: {len(_QUADRANT_INDEX)} cells")
    return _QUADRANT_INDEX


def identificar_grades_relevantes(area_geom):
    """
    Identify which IBGE grade_id quadrants intersect with the area of interest.
    Uses the 500km grid as spatial index.
    """
    quadrant_index = carregar_indice_quadrantes()
    
    if quadrant_index is None:
        print("✗ Error: Could not load quadrant index")
        return []
    
    # Find quadrants that intersect the area
    intersecting = quadrant_index[quadrant_index.intersects(area_geom)]
    
    if intersecting.empty:
        print("⚠ Warning: No quadrants found intersecting the polygon")
        print(f"  Polygon bounds: {area_geom.bounds}")
        return []
    
    # Extract unique QUADRANTE values (these correspond to grade_id numbers)
    grades_raw = sorted(intersecting['QUADRANTE'].unique().tolist())
    grades_relevantes = [int(g.replace("ID_", "")) for g in grades_raw]
    
    return grades_relevantes


def carregar_grid_ibge(grade_id, use_cache=True):
    """
    Download and load IBGE statistical grid shapefile with caching.
    
    Uses the standard IBGE Statistical Grid (Census 2022):
    - Mixed resolution: 1km x 1km (rural) and 200m x 200m (urban)
    - Albers Equal Area projection (SIRGAS2000)
    """
    if use_cache and grade_id in _GRID_CACHE:
        return _GRID_CACHE[grade_id], grade_id
    
    url = f"https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/grade_estatistica/censo_2022/grade_estatistica/grade_id{grade_id}.zip"
    pasta = f"dados_ibge/grade_id{grade_id}"
    shp_path = os.path.join(pasta, f"grade_id{grade_id}.shp")
    
    if not os.path.exists(shp_path):
        os.makedirs(pasta, exist_ok=True)
        print(f"  ⬇ Downloading grade_id{grade_id}...")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                z.extractall(pasta)
        except Exception as e:
            print(f"  ✗ Error downloading grade_id{grade_id}: {e}")
            return None, grade_id
    
    dados = gpd.read_file(shp_path)
    
    if use_cache:
        _GRID_CACHE[grade_id] = dados
    
    return dados, grade_id


def calcular_area_km2(geom):
    """Calculate area in km² for a geometry in WGS84."""
    geom_projected = gpd.GeoSeries([geom], crs='EPSG:4326').to_crs(ALBERS_BR)
    return float(geom_projected.area.iloc[0] / 1e6)


def desenhar_contornos(ax, layers_poligonos, layer_order):
    """Draw layer boundaries with improved styling."""
    for name in layer_order:
        if name in layers_poligonos:
            gpd.GeoSeries([layers_poligonos[name]]).boundary.plot(
                ax=ax, color=COLORS[name], linewidth=2.5, linestyle='-', zorder=10
            )


def criar_legenda_areas(layers_poligonos, layers_para_mostrar, buffer_info=None):
    """Create legend elements with buffer and height information in Portuguese."""
    if buffer_info is None:
        buffer_info = DEFAULT_BUFFER_INFO
    
    legend_elements = []
    
    for name in layers_para_mostrar:
        if name in layers_poligonos:
            name_pt = NAMES_PT.get(name, name)
            info = buffer_info.get(name, {})
            buffer_m = info.get('buffer', 0)
            height_m = info.get('height')
            
            # Format label
            if buffer_m == 0 and height_m:
                label = f"{name_pt}\n(Altura: {height_m}m)"
            elif buffer_m > 0 and height_m:
                label = f"{name_pt}\n(Buffer: {buffer_m}m, Altura: {height_m}m)"
            elif buffer_m > 0:
                label = f"{name_pt}\n(Buffer: {buffer_m}m)"
            else:
                label = name_pt
            
            legend_elements.append(
                Patch(facecolor='none', edgecolor=COLORS[name], 
                      linewidth=2.5, label=label)
            )
    
    return legend_elements


def criar_colormap_melhorado():
    """Create an improved colormap from white to yellow to red."""
    # Colormap que vai de branco → amarelo → laranja → vermelho
    colors = ['#FFFFFF', '#FFF9E6', '#FFF3CC', '#FFECB3', '#FFE599',
              '#FFDB80', '#FFD166', '#FFC14D', '#FFB133', '#FFA31A',
              '#FF9500', '#FF8700', '#FF7A00', '#FF6D00', '#FF5500',
              '#FF3D00', '#FF2500', '#FF0D00', '#E60000', '#CC0000']
    n_bins = 100
    cmap = LinearSegmentedColormap.from_list('population', colors, N=n_bins)
    return cmap


def determinar_zoom_adequado(area_km2):
    """Determine appropriate zoom level based on area size."""
    if area_km2 < 1:
        return 16
    elif area_km2 < 5:
        return 15
    elif area_km2 < 20:
        return 14
    elif area_km2 < 100:
        return 13
    elif area_km2 < 500:
        return 12
    else:
        return 11


def calcular_estatisticas(dados_intersec, area_geom=None):
    """
    Calculate statistics from filtered grid.
    
    Args:
        dados_intersec: GeoDataFrame with population data in metric projection
        area_geom: Optional - actual polygon geometry to use for area calculation
    
    Returns:
        tuple: (total_pessoas, area_km2, densidade_media, densidade_maxima)
    """
    if dados_intersec.empty:
        return 0, 0.0, 0.0, 0.0
    
    total_pessoas = float(dados_intersec['TOTAL'].sum())
    
    # Use actual polygon area if provided, otherwise sum of cell areas
    if area_geom is not None:
        # Convert to metric projection and calculate area
        area_geom_projected = gpd.GeoSeries([area_geom], crs='EPSG:4326').to_crs(ALBERS_BR)
        area_km2 = float(area_geom_projected.area.iloc[0] / 1e6)
    else:
        area_km2 = float((dados_intersec.geometry.area.sum()) / 1e6)
    
    densidade_media = (total_pessoas / area_km2) if area_km2 > 0 else 0.0
    densidade_maxima = float(dados_intersec['densidade_pop_km2'].max()) if not dados_intersec.empty else 0.0
    
    return total_pessoas, area_km2, densidade_media, densidade_maxima


def processar_todas_grades(area_geom, titulo, layers_poligonos, layers_para_mostrar, 
                          buffer_info=None, output_path=None):
    """
    Process all relevant IBGE grids and create a single combined map.
    Uses 500km grid as spatial index to identify relevant quadrants.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {titulo}")
    print(f"{'='*60}")
    
    # Identify relevant grids using 500km index
    grades_relevantes = identificar_grades_relevantes(area_geom)
    
    if not grades_relevantes:
        print("⚠ No relevant grids found for this area.")
        return None
    
    print(f"✓ Identified {len(grades_relevantes)} relevant quadrants: {grades_relevantes}")
    
    # Collect data from all relevant grids
    todos_dados = []
    
    for grade_id in grades_relevantes:
        grid, _ = carregar_grid_ibge(grade_id)
        
        if grid is None:
            continue
        
        # Use spatial index for fast filtering
        try:
            possible_matches_idx = list(grid.sindex.intersection(area_geom.bounds))
            if not possible_matches_idx:
                continue
            
            possible_matches = grid.iloc[possible_matches_idx]
            dados_filtrados = possible_matches[possible_matches.intersects(area_geom)].copy()
            
            if not dados_filtrados.empty:
                print(f"  ✓ grade_id{grade_id}: {len(dados_filtrados)} cells found")
                todos_dados.append(dados_filtrados)
        except Exception as e:
            print(f"  ✗ grade_id{grade_id}: Error - {e}")
            continue
    
    if not todos_dados:
        print("⚠ No data found in any grid for this area.")
        return None
    
    # Combine all data
    dados_combinados = gpd.GeoDataFrame(pd.concat(todos_dados, ignore_index=True))
    print(f"✓ Total cells: {len(dados_combinados)}")
    
    # Calculate density in metric projection
    dados_area = dados_combinados.to_crs(ALBERS_BR)
    dados_area['area_km2'] = dados_area.geometry.area / 1e6
    dados_area['densidade_pop_km2'] = dados_area['TOTAL'] / dados_area['area_km2']
    dados_combinados['densidade_pop_km2'] = dados_area['densidade_pop_km2'].values
    
    # Create improved colormap
    cmap = criar_colormap_melhorado()
    
    # Determine figure size based on area
    area_analise_km2 = calcular_area_km2(area_geom)
    fig_size = min(30, max(20, area_analise_km2 * 0.5))
    
    # Plot with improved settings
    fig, ax = plt.subplots(figsize=(fig_size, fig_size), dpi=150)
    
    # Plot population density with improved colormap
    dados_combinados.plot(
        column='densidade_pop_km2',
        ax=ax,
        legend=True,
        cmap=cmap,
        alpha=0.7,
        edgecolor='gray',
        linewidth=0.15,
        legend_kwds={
            'shrink': 0.5, 
            'label': 'Densidade Populacional (hab/km²)',
            'orientation': 'vertical',
            'pad': 0.02
        },
        vmin=0  # Garante que a escala começa do zero
    )
    
    # Draw boundaries
    desenhar_contornos(ax, layers_poligonos, layers_para_mostrar)
    
    # Add legend for areas
    legend_elements = criar_legenda_areas(layers_poligonos, layers_para_mostrar, buffer_info)
    if legend_elements:
        ax.legend(
            handles=legend_elements,
            loc='upper left',
            fontsize=14,  # Aumentado de 11 para 14
            framealpha=0.95,
            edgecolor='black',
            title='Áreas Analisadas',
            title_fontsize=15  # Aumentado de 12 para 15
        )
    
    ax.set_title(titulo, fontsize=24, fontweight='bold', pad=20)  # Aumentado de 20 para 24
    ax.set_xlabel("Longitude [°]", fontsize=16, fontweight='bold')  # Aumentado de 14 para 16
    ax.set_ylabel("Latitude [°]", fontsize=16, fontweight='bold')  # Aumentado de 14 para 16
    
    # Add basemap with appropriate zoom and higher quality
    zoom_level = determinar_zoom_adequado(area_analise_km2)
    try:
        # Use higher zoom for better resolution
        cx.add_basemap(
            ax,
            crs=dados_combinados.crs.to_string(),
            source=cx.providers.OpenStreetMap.Mapnik,
            alpha=0.5,
            zoom=zoom_level + 1  # +1 para maior resolução
        )
    except Exception as e:
        print(f"⚠ Could not add basemap: {e}")
    
    # Statistics box with improved formatting
    total_pessoas, area_km2, densidade_media, densidade_maxima = calcular_estatisticas(dados_area, area_geom)
    
    info_texto = (
        f"ESTATÍSTICAS\n"
        f"População Total: {int(total_pessoas):,} habitantes\n"
        f"Área do Polígono: {area_km2:.2f} km²\n"
        f"Densidade Média: {densidade_media:.2f} hab/km²\n"
        f"Densidade Máxima: {densidade_maxima:.2f} hab/km²"
    ).replace(",", ".")
    
    ax.text(
        0.02, 0.02,
        info_texto,
        transform=ax.transAxes,
        fontsize=13,  # Aumentado de 11 para 13
        verticalalignment='bottom',
        bbox=dict(
            facecolor='white', 
            alpha=0.95, 
            edgecolor='black',
            boxstyle='round,pad=0.8'
        ),
        family='Segoe UI'
    )
    
    # Improve grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.tick_params(labelsize=12)  # Aumentado de 11 para 12
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ Map saved: {output_path}")
    
    plt.close()
    
    return {
        'total_pessoas': total_pessoas,
        'area_km2': area_km2,
        'densidade_media': densidade_media,
        'densidade_maxima': densidade_maxima
    }


def analyze_population(kml_file, output_dir='results', buffer_info=None, height=None):
    """
    Main function to analyze population density from safety margins KML.
    
    Args:
        kml_file (str): Path to KML file with safety margins
        output_dir (str): Directory to save output maps
        buffer_info (dict): Optional dictionary with buffer values for each layer
                           Format: {'fg_size': 0, 'cv_size': 215, 'grb_size': 295, 'adj_size': 5000}
        height (float): Optional flight height in meters
        
    Returns:
        dict: Statistics for each analyzed layer
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Build buffer_info for legend display
    if buffer_info is None:
        buffer_info_display = DEFAULT_BUFFER_INFO
    else:
        # Map the buffer values to layer names
        buffer_info_display = {
            'Flight Geography': {
                'buffer': buffer_info.get('fg_size', 0),
                'height': height
            },
            'Contingency Volume': {
                'buffer': buffer_info.get('cv_size', 215),
                'height': None
            },
            'Ground Risk Buffer': {
                'buffer': buffer_info.get('grb_size', 0),
                'height': None
            },
            'Adjacent Area': {
                'buffer': buffer_info.get('adj_size', 5000),
                'height': None
            }
        }
    
    layers_kml = ["Flight Geography", "Contingency Volume", "Ground Risk Buffer", "Adjacent Area"]
    
    print("="*60)
    print("AL DRONES - Population Analysis Tool")
    print("="*60)
    
    # Extract KML polygons
    layers_poligonos = extrair_layers_kml(kml_file, layers_kml)
    
    if not layers_poligonos:
        print("✗ No valid layers found in KML")
        return None
    
    results = {}
    
    # Plot 1 — Flight Geography
    stats = processar_todas_grades(
        area_geom=layers_poligonos['Flight Geography'],
        titulo="Densidade Populacional - Geografia de Voo (SDO 50 V3)",
        layers_poligonos=layers_poligonos,
        layers_para_mostrar=['Flight Geography'],
        buffer_info=buffer_info_display,
        output_path=os.path.join(output_dir, 'map_flight_geography.png')
    )
    if stats:
        results['Flight Geography'] = stats
    
    # Plot 2 — Ground Risk Buffer
    stats = processar_todas_grades(
        area_geom=layers_poligonos['Ground Risk Buffer'],
        titulo="Densidade Populacional - Distância de Segurança no Solo (SDO 50 V3)",
        layers_poligonos=layers_poligonos,
        layers_para_mostrar=['Flight Geography', 'Contingency Volume', 'Ground Risk Buffer'],
        buffer_info=buffer_info_display,
        output_path=os.path.join(output_dir, 'map_ground_risk_buffer.png')
    )
    if stats:
        results['Ground Risk Buffer'] = stats
    
    # Plot 3 — Adjacent Area ring
    # Adjacent Area is built 5km from CV, but analyzed area is between GRB and Adjacent Area
    if 'Adjacent Area' in layers_poligonos and 'Ground Risk Buffer' in layers_poligonos:
        area_anel = layers_poligonos['Adjacent Area'].difference(layers_poligonos['Ground Risk Buffer'])
        stats = processar_todas_grades(
            area_geom=area_anel,
            titulo="Densidade Populacional - Área Adjacente (SDO 50 V3)",
            layers_poligonos=layers_poligonos,
            layers_para_mostrar=['Flight Geography', 'Contingency Volume', 'Ground Risk Buffer', 'Adjacent Area'],
            buffer_info=buffer_info_display,
            output_path=os.path.join(output_dir, 'map_adjacent_area.png')
        )
        if stats:
            results['Adjacent Area'] = stats
    else:
        print("⚠ Cannot generate Adjacent Area plot: missing required layers.")
    
    print("\n" + "="*60)
    print("✓ Analysis complete!")
    print("="*60)
    
    return results


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Analyze population density in drone flight areas'
    )
    parser.add_argument(
        'kml_file',
        help='KML file with safety margins (output from generate_safety_margins.py)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='results',
        help='Output directory for maps (default: results/)'
    )
    parser.add_argument(
        '--height',
        type=float,
        help='Flight height in meters (optional)'
    )
    
    args = parser.parse_args()
    
    # Example: customize buffer info if you know the values
    # You can modify these values or read them from a config file
    buffer_info = DEFAULT_BUFFER_INFO.copy()
    
    # If height is provided, add it to Flight Geography
    if args.height:
        buffer_info['Flight Geography']['height'] = args.height
    
    analyze_population(args.kml_file, args.output_dir, buffer_info)


if __name__ == '__main__':
    main()
