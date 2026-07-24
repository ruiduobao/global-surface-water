#!/usr/bin/env python3
"""
JRC Global Surface Water Download CLI
======================================
Download JRC Global Surface Water data layers via HTTP direct download.

Privacy Notice:
- This tool sends ONLY the following data to global-surface-water.appspot.com:
  * Tile coordinates (derived from your bounding box)
  * Layer name
- NO personal data, credentials, or device information is sent.
- All data is processed locally except the download request itself.

License: MIT-0 (Public Domain)
Data: JRC Global Surface Water, CC-BY 4.0
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests>=2.28.0")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# ── Constants ──────────────────────────────────────────────────────────────────
# JRC data is available as Cloud-Optimized GeoTIFFs
# The data is organized in 10° x 10° tiles
# Tile naming: occurrence_change_seasonality_recurrence_transition_extent_<lat>_<lon>
# where lat/lon are the lower-left corner of the tile

JRC_PORTAL_URL = "https://global-surface-water.appspot.com"
JRC_DOWNLOAD_BASE = "https://storage.googleapis.com/global-surface-water"

LAYERS = {
    "occurrence": {
        "label": "Water Occurrence",
        "description": "Percentage of water detection (0-100%)",
        "unit": "%",
    },
    "change": {
        "label": "Occurrence Change Intensity",
        "description": "Change in water occurrence (gain/loss)",
        "unit": "dimensionless",
    },
    "seasonality": {
        "label": "Seasonality",
        "description": "Number of months with water (1-12)",
        "unit": "months",
    },
    "recurrence": {
        "label": "Recurrence",
        "description": "Frequency of water recurrence (1-11)",
        "unit": "classes",
    },
    "transition": {
        "label": "Transition",
        "description": "Transitions between water classes",
        "unit": "classes",
    },
    "extent": {
        "label": "Extent",
        "description": "Maximum water extent (binary)",
        "unit": "binary",
    },
    "max_extent": {
        "label": "Max Extent",
        "description": "Maximum water extent layer",
        "unit": "binary",
    },
}

TILE_SIZE = 10  # degrees

# ── Validation ─────────────────────────────────────────────────────────────────
def validate_bbox(bbox):
    """Validate bounding box: west, south, east, north."""
    if len(bbox) != 4:
        raise ValueError("Bounding box must have 4 values: west south east north")
    west, south, east, north = bbox
    if not (-90 <= south <= 90) or not (-90 <= north <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= west <= 180) or not (-180 <= east <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    if south >= north:
        raise ValueError(f"South ({south}) must be less than North ({north})")
    if west >= east:
        raise ValueError(f"West ({west}) must be less than East ({east})")
    return west, south, east, north

def validate_layer(layer):
    """Validate layer name."""
    layer = layer.lower()
    if layer not in LAYERS and layer != "all":
        raise ValueError(f"Unknown layer: {layer}. Valid: {', '.join(LAYERS.keys())}, all")
    return layer

# ── Tile Calculation ───────────────────────────────────────────────────────────
def get_tile_range(bbox, tile_size=TILE_SIZE):
    """Calculate which tiles intersect the bounding box."""
    west, south, east, north = bbox

    # Tile lower-left corners
    tile_lon_start = math.floor(west / tile_size) * tile_size
    tile_lon_end = math.floor(east / tile_size) * tile_size
    tile_lat_start = math.floor(south / tile_size) * tile_size
    tile_lat_end = math.floor(north / tile_size) * tile_size

    tiles = []
    lon = tile_lon_start
    while lon <= tile_lon_end:
        lat = tile_lat_start
        while lat <= tile_lat_end:
            tiles.append((lon, lat))
            lat += tile_size
        lon += tile_size

    return tiles

def get_tile_name(layer, lon, lat):
    """Generate tile filename for a given layer and tile coordinates."""
    # Format: <layer>_<lat>N_<lon>E or <layer>_<lat>S_<lon>W
    lat_str = f"{abs(int(lat))}N" if lat >= 0 else f"{abs(int(lat))}S"
    lon_str = f"{abs(int(lon))}E" if lon >= 0 else f"{abs(int(lon))}W"
    return f"occurrence_{int(lat)}_{int(lon)}"

def get_download_url(layer, lon, lat, version="v1_4"):
    """Generate download URL for a tile."""
    # JRC GSW1_4 tile naming convention
    # occurrence_v1_4_<lat>_<lon>.tif
    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"
    lat_val = abs(int(lat))
    lon_val = abs(int(lon))

    filename = f"{layer}_v1_4_{lat_val}{lat_prefix}_{lon_val}{lon_prefix}.tif"
    url = f"{JRC_DOWNLOAD_BASE}/v1_4/{filename}"
    return url

# ── Download Functions ─────────────────────────────────────────────────────────
def download_file(url, output_path, timeout=300):
    """Download a file with progress bar."""
    try:
        with requests.get(url, stream=True, timeout=timeout) as resp:
            if resp.status_code == 404:
                return False, "File not found (404)"
            resp.raise_for_status()

            total_size = int(resp.headers.get("content-length", 0))

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                if tqdm and total_size > 0:
                    with tqdm(total=total_size, unit="B", unit_scale=True,
                              desc=output_path.name) as pbar:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

            return True, "OK"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP error {resp.status_code}"
    except Exception as e:
        return False, str(e)

# ── CLI Commands ───────────────────────────────────────────────────────────────
def cmd_download(args):
    """Download JRC Global Surface Water data."""
    layer = validate_layer(args.layer)
    bbox = validate_bbox(args.bbox)

    layers_to_download = list(LAYERS.keys()) if layer == "all" else [layer]

    tiles = get_tile_range(bbox)
    print(f"JRC Global Surface Water Download")
    print(f"  Layers: {', '.join(layers_to_download)}")
    print(f"  BBox: {bbox}")
    print(f"  Tiles to check: {len(tiles)}")
    print()

    output_dir = Path(args.output)
    if layer == "all":
        output_dir.mkdir(parents=True, exist_ok=True)

    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    for layer_name in layers_to_download:
        print(f"--- Layer: {LAYERS[layer_name]['label']} ---")

        for lon, lat in tiles:
            url = get_download_url(layer_name, lon, lat)

            if layer == "all":
                layer_dir = output_dir / layer_name
                layer_dir.mkdir(exist_ok=True)
                filename = url.split("/")[-1]
                output_path = layer_dir / filename
            else:
                output_path = output_dir

            if output_path.exists():
                print(f"  Skip {output_path.name} (exists)")
                total_skipped += 1
                continue

            print(f"  Downloading tile ({lon}, {lat})...")
            success, msg = download_file(url, output_path)

            if success:
                total_downloaded += 1
                print(f"    OK")
            else:
                total_failed += 1
                print(f"    Failed: {msg}")
                # Clean up partial file
                if Path(output_path).exists():
                    Path(output_path).unlink()

    print()
    print(f"Summary: {total_downloaded} downloaded, {total_skipped} skipped, {total_failed} failed")

    if total_failed > 0:
        print("\nNote: Some tiles may not exist for all layers.")
        print("The JRC data covers land areas only; ocean tiles are not available.")

def cmd_list_layers(args):
    """List available data layers."""
    print("=" * 70)
    print("JRC Global Surface Water - Available Layers")
    print("=" * 70)
    print(f"{'Layer':<15} {'Label':<30} {'Unit':<15} Description")
    print("-" * 70)
    for layer, info in LAYERS.items():
        print(f"{layer:<15} {info['label']:<30} {info['unit']:<15} {info['description']}")
    print("-" * 70)
    print(f"\nTime range: 1984-2024")
    print(f"Resolution: 30m")
    print(f"Version: v1_4")

def cmd_info(args):
    """Show dataset information."""
    print("=" * 70)
    print("JRC Global Surface Water - Dataset Information")
    print("=" * 70)
    print(f"Dataset: JRC/GSW1_4/GlobalSurfaceWater")
    print(f"Time range: 1984-2024")
    print(f"Spatial resolution: 30m")
    print(f"Temporal resolution: Monthly (derived from Landsat archive)")
    print(f"Spatial coverage: Global (land areas)")
    print(f"Version: v1_4")
    print()
    print("Data Layers:")
    for layer, info in LAYERS.items():
        print(f"  {layer}: {info['label']} - {info['description']}")
    print()
    print("Data Source:")
    print("  Portal: https://global-surface-water.appspot.com/")
    print("  GEE: https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater")
    print("  License: CC-BY 4.0 (EC JRC)")
    print()
    print("Citation:")
    print("  Pekel, J.F., Cottam, A., Gorelick, N., Belward, A.S., 2016.")
    print("  High-resolution mapping of global surface water and its long-term changes.")
    print("  Nature, 540, 418-422.")
    print()
    print("Alternative Access Methods:")
    print("  1. Google Earth Engine (requires earthengine-api):")
    print("     import ee")
    print("     ee.Initialize()")
    print("     dataset = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')")
    print("     occurrence = dataset.select('occurrence')")
    print()
    print("  2. Web portal: https://global-surface-water.appspot.com/")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="global-surface-water",
        description="Download JRC Global Surface Water data layers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s download --layer occurrence --bbox 116.0 39.5 116.8 40.2 \\
    --output ./water/beijing_occurrence.tif

  %(prog)s download --layer seasonality --bbox 73 18 135 54 \\
    --output ./water/china_seasonality.tif

  %(prog)s download --layer all --bbox 116.3 39.8 116.5 40.0 \\
    --output ./water/beijing_all/

  %(prog)s list-layers
  %(prog)s info
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    dl = subparsers.add_parser("download", help="Download surface water data")
    dl.add_argument("--layer", default="occurrence",
                    help="Layer name or 'all' (default: occurrence)")
    dl.add_argument("--bbox", nargs=4, type=float, required=True,
                    metavar=("W", "S", "E", "N"),
                    help="Bounding box: west south east north")
    dl.add_argument("--output", default="./surface_water/",
                    help="Output file or directory (default: ./surface_water/)")
    dl.add_argument("--version", default="v1_4",
                    help="Dataset version (default: v1_4)")
    dl.set_defaults(func=cmd_download)

    # List layers command
    ll = subparsers.add_parser("list-layers", help="List available data layers")
    ll.set_defaults(func=cmd_list_layers)

    # Info command
    info = subparsers.add_parser("info", help="Show dataset information")
    info.set_defaults(func=cmd_info)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except ValueError as e:
        print(f"Validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)

if __name__ == "__main__":
    main()
