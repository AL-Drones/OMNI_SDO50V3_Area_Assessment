"""
AL Drones - Safety Margins Generator
Generates 4 safety layers from input KML for drone operations.
"""

import os
import argparse
from math import sqrt
import simplekml
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


# KML styling configuration
STYLES = {
    'Flight Geography': {'fill': '3300ff00', 'outline': 'ff00ff00', 'width': 2},
    'Contingency Volume': {'fill': '1a00ffff', 'outline': 'ff00ffff', 'width': 2},
    'Ground Risk Buffer': {'fill': '1a0000ff', 'outline': 'ff0000ff', 'width': 2},
    'Adjacent Area': {'fill': '00ff0000', 'outline': 'ffff0000', 'width': 1},
}


def calculate_grb_size(height):
    """
    Calculate Ground Risk Buffer size based on flight height.
    
    Args:
        height (float): Flight height in meters
        
    Returns:
        float: GRB size in meters
    """
    if height <= 120:
        height_cv = height + 15
        return height_cv
    else:
        height_cv = height + 15
        return 25 * sqrt(2 * height_cv / 9.81) + 1.485


def generate_safety_margins(
    input_kml_path,
    output_kml_path=None,
    fg_size=0,
    height=100,
    cv_size=50,
    grb_size=None,
    adj_size=5000,
    corner_style='square'
):
    """
    Generate safety margin layers from input KML.
    
    Args:
        input_kml_path (str): Path to input KML file
        output_kml_path (str): Path for output KML file (optional)
        fg_size (float): Flight Geography buffer size in meters (0 for polygons)
        height (float): Flight height in meters
        cv_size (float): Contingency Volume buffer size in meters (min: 215m)
        grb_size (float): Ground Risk Buffer size in meters (optional, calculated if None)
        adj_size (float): Adjacent Area buffer size in meters (default 5000)
        corner_style (str): 'square' or 'rounded' for buffer corners
        
    Returns:
        str: Path to generated KML file
    """
    
    # Read and reproject to metric CRS (SIRGAS 2000 / UTM zone 23S)
    gdf = gpd.read_file(input_kml_path).to_crs(epsg=31983)
    
    # Check if geometry contains polygons
    has_polygon = gdf.geometry.type.isin(['Polygon', 'MultiPolygon']).any()
    
    # If input is polygon, no need for Flight Geography buffer
    if has_polygon:
        fg_size = 0
    
    # Set join style for corners
    join_style = 2 if corner_style == 'square' else 1
    
    # Calculate Ground Risk Buffer size if not provided
    if grb_size is None:
        grb_size = calculate_grb_size(height)
    else:
        # Validate that custom GRB is not less than calculated minimum
        grb_minimum = calculate_grb_size(height)
        if grb_size < grb_minimum:
            print(f"⚠️  Warning: GRB size ({grb_size}m) is less than calculated minimum ({grb_minimum:.2f}m)")
            print(f"   Using minimum value: {grb_minimum:.2f}m")
            grb_size = grb_minimum
    
    # Validate Contingency Volume minimum
    if cv_size < 215:
        print(f"⚠️  Warning: CV size ({cv_size}m) is less than minimum (215m)")
        print(f"   Using minimum value: 215m")
        cv_size = 215
    
    # Create buffers
    buffers = {
        'Flight Geography': fg_size,
        'Contingency Volume': cv_size + fg_size,
        'Ground Risk Buffer': grb_size + cv_size + fg_size,
    }
    
    layers = {}
    for name, buffer_size in buffers.items():
        layer = gdf.copy()
        if buffer_size > 0:
            # Use flat cap for Flight Geography points, round cap for others
            cap_style = 3 if name == 'Flight Geography' and not has_polygon else 1
            layer["geometry"] = gdf.geometry.buffer(
                buffer_size,
                cap_style=cap_style,
                join_style=join_style
            )
        layers[name] = layer.to_crs(epsg=4326)
    
    # Adjacent Area uses Contingency Volume as base
    adj_layer = layers['Contingency Volume'].copy()
    adj_layer["geometry"] = (
        layers['Contingency Volume']
        .to_crs(epsg=31983)
        .geometry.buffer(adj_size, join_style=1)
    )
    layers['Adjacent Area'] = adj_layer.to_crs(epsg=4326)
    
    # Create KML with all polygons
    kml = simplekml.Kml()
    folder = kml.newfolder(name="Safety Margins")
    
    for name, layer in layers.items():
        for _, row in layer.iterrows():
            geom = row['geometry']
            polygons = (
                [geom] if isinstance(geom, Polygon)
                else (geom.geoms if isinstance(geom, MultiPolygon) else [])
            )
            
            for poly in polygons:
                if isinstance(poly, Polygon):
                    coords = list(zip(*poly.exterior.coords.xy))
                    pol = folder.newpolygon(name=name, outerboundaryis=coords)
                    pol.style.polystyle.color = STYLES[name]['fill']
                    pol.style.polystyle.fill = 1
                    pol.style.linestyle.color = STYLES[name]['outline']
                    pol.style.linestyle.width = STYLES[name]['width']
    
    # Determine output path
    if output_kml_path is None:
        base_name = os.path.splitext(input_kml_path)[0]
        output_kml_path = f"{base_name}_safety_margins.kml"
    
    # Save KML
    kml.save(output_kml_path)
    
    print(f"✓ Safety margins KML generated: {output_kml_path}")
    print(f"  - Flight Geography: {fg_size}m buffer")
    print(f"  - Contingency Volume: {cv_size}m buffer")
    print(f"  - Ground Risk Buffer: {grb_size:.2f}m (height: {height}m)")
    print(f"  - Adjacent Area: {adj_size}m buffer")
    
    return output_kml_path


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Generate drone safety margin layers from KML'
    )
    parser.add_argument(
        'input_kml',
        help='Input KML file path'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output KML file path (optional)',
        default=None
    )
    parser.add_argument(
        '--fg-size',
        type=float,
        default=0,
        help='Flight Geography buffer size in meters (default: 0 for polygons)'
    )
    parser.add_argument(
        '--height',
        type=float,
        default=100,
        help='Flight height in meters (default: 100)'
    )
    parser.add_argument(
        '--cv-size',
        type=float,
        default=215,
        help='Contingency Volume buffer size in meters (default: 215, minimum: 215)'
    )
    parser.add_argument(
        '--grb-size',
        type=float,
        default=None,
        help='Ground Risk Buffer size in meters (optional, calculated from height if not provided)'
    )
    parser.add_argument(
        '--adj-size',
        type=float,
        default=5000,
        help='Adjacent Area buffer size in meters (default: 5000)'
    )
    parser.add_argument(
        '--corner-style',
        choices=['square', 'rounded'],
        default='square',
        help='Corner style for buffers (default: square)'
    )
    
    args = parser.parse_args()
    
    generate_safety_margins(
        input_kml_path=args.input_kml,
        output_kml_path=args.output,
        fg_size=args.fg_size,
        height=args.height,
        cv_size=args.cv_size,
        grb_size=args.grb_size,
        adj_size=args.adj_size,
        corner_style=args.corner_style
    )


if __name__ == '__main__':
    main()
