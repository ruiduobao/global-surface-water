---
name: global-surface-water
display_name: JRC 全球地表水下载
version: 0.1.0
author: ruiduobao
license: MIT-0
description: |
  Download JRC Global Surface Water data layers including occurrence, change, seasonality,
  recurrence, transition, and extent. Data derived from 3+ years of Landsat imagery
  (1984-2024) at 30m resolution. Supports bbox clipping and GeoTIFF output.
runtime: python>=3.8
tags: [gis, remote-sensing, water, surface-water, jrc, landsat, gee]
---

# JRC Global Surface Water Download

Download surface water data from the JRC Global Surface Water Explorer — derived from
30+ years of Landsat imagery at 30m resolution.

## Overview

The JRC Global Surface Water dataset maps the location and temporal distribution of
surface water from 1984 to 2024. It uses the entire Landsat 5, 7, and 8 archive to
produce 6 data layers describing surface water dynamics.

## Data Layers

| Layer | ID | Description |
|-------|----|-------------|
| occurrence | occurrence | Percentage of water detection (0-100%) |
| change | change | Change in water occurrence (gain/loss) |
| seasonality | seasonality | Number of months with water (1-12) |
| recurrence | recurrence | Frequency of water recurrence (1-11) |
| transition | transition | Transitions between water classes |
| extent | extent | Maximum water extent (binary) |
| max_extent | max_extent | Maximum water extent layer |

## Features

- **6 data layers**: occurrence, change, seasonality, recurrence, transition, extent
- **30m resolution**: full Landsat resolution
- **Bbox clipping**: download only your area of interest
- **GeoTIFF output**: standard georeferenced raster
- **Multiple access methods**: HTTP direct download or GEE-based access
- **Fallback options**: works with or without Google Earth Engine

## Access Methods

### Method 1: Direct HTTP Download (Recommended)

The JRC data is tiled globally. This skill generates download URLs for the tiles
intersecting your bbox and downloads them as GeoTIFF.

### Method 2: Google Earth Engine (Optional)

If you have `geemap` or `earthengine-api` installed, you can use GEE for more
flexible subsetting:

```python
import ee
ee.Initialize()
dataset = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
occurrence = dataset.select('occurrence')
```

## Usage

```bash
# Download water occurrence for a region
python scripts/global_surface_water.py download \
  --layer occurrence \
  --bbox 116.0 39.5 116.8 40.2 \
  --output ./water/beijing_occurrence.tif

# Download seasonality layer
python scripts/global_surface_water.py download \
  --layer seasonality \
  --bbox 73 18 135 54 \
  --output ./water/china_seasonality.tif

# Download all layers for a small area
python scripts/global_surface_water.py download \
  --layer all \
  --bbox 116.3 39.8 116.5 40.0 \
  --output ./water/beijing_all/

# List available layers
python scripts/global_surface_water.py list-layers

# Show dataset info
python scripts/global_surface_water.py info
```

## Parameters

- `--layer`: Layer name (occurrence, change, seasonality, recurrence, transition, extent, max_extent, all)
- `--bbox`: Bounding box as `west south east north`
- `--output`: Output file path or directory
- `--version`: Dataset version (default: v1_4)
- `--tile-size`: Tile size in degrees (default: 10)

## Data Tiling

The JRC Global Surface Water data is organized in 10° × 10° tiles. Each tile is
approximately 300-600 MB. The skill automatically identifies which tiles intersect
your bounding box and downloads them.

## Installation

```bash
# Install dependencies
pip install requests>=2.28.0 tqdm

# Or install from requirements.txt
pip install -r scripts/requirements.txt
```

## Data Source

- **Dataset**: JRC/GSW1_4/GlobalSurfaceWater
- **Portal**: https://global-surface-water.appspot.com/
- **GEE Catalog**: https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater
- **License**: CC-BY 4.0 (EC JRC)
- **Rate Limit**: No strict limit; recommended max 5 tile requests/minute
- **CRS**: WGS84 (EPSG:4326)
- **Data type**: uint8 (8-bit unsigned integer)
- **NoData value**: 0 (for most layers)

### Citation Format

```bibtex
@article{pekel2016high,
  title={High-resolution mapping of global surface water and its long-term changes},
  author={Pekel, J.F. and Cottam, A. and Gorelick, N. and Belward, A.S.},
  journal={Nature},
  volume={540},
  pages={418--422},
  year={2016},
  doi={10.1038/nature20584}
}
```

### Layer Definitions

**Transition layer classes**:
| Value | Description |
|-------|-------------|
| 1 | Permanent water |
| 2 | New permanent water (gained) |
| 3 | Lost permanent water |
| 4 | Seasonal water |
| 5 | New seasonal water |
| 6 | Lost seasonal water |
| 7 | Permanent to seasonal |
| 8 | Seasonal to permanent |
| 9 | Ephemeral permanent |
| 10 | Ephemeral seasonal |
| 11 | No water |

**Recurrence scale** (1–11):
| Value | Meaning |
|-------|---------|
| 1 | Seasonal (least frequent) |
| 2–5 | Low recurrence |
| 6–8 | Moderate recurrence |
| 9–10 | High recurrence |
| 11 | Permanent (most frequent) |

**Change layer values**:
| Value | Meaning |
|-------|---------|
| 0 | No change |
| 1 | New water (gain) |
| 2 | Lost water |

**extent vs max_extent**:
- **extent**: Maximum observed water extent during the entire observation period (single binary layer).
- **max_extent**: Same as extent but includes additional processing for data quality.

### Large-Area Download Planning

- **Tile size**: 10° × 10° tiles
- **Storage estimate**: ~1 GB per 10° × 10° tile at 30m resolution (all 7 layers)
- **Planning**: For large regions, calculate number of intersecting tiles × ~1 GB to estimate storage needs.
- **Tip**: Download one layer at a time for large areas to manage disk space.

### Visualization

- **Occurrence**: Use single-band pseudocolor in QGIS (blue→white gradient for 0–100%).
- **Change**: Apply discrete color map: green = gain, red = loss, transparent = no change.
- **Recurrence**: Use graduated color ramp (yellow→dark blue) for 1–11 scale.
- **Extent**: Binary display — blue = water, transparent = land.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionError` | Network issue or API down | Check internet connection, retry in 1 minute |
| `HTTP 429` | Rate limit exceeded | Wait 60 seconds before retrying |
| `HTTP 404` | Invalid parameters or date range | Check parameter names and date format |
| `ValueError: bbox` | Invalid bounding box | Ensure format is `west,south,east,north` |
| Empty output | No data for query region/time | Try different date range or check coordinates |
| `ModuleNotFoundError` | Missing dependency | Run `pip install requests tqdm` |
| Disk full | Large tile downloads | Free space or reduce bbox size |

---

## Advanced Usage

### Batch Tile Download
```bash
# Download occurrence layer for multiple tiles
for tile in "40N_110E" "40N_120E" "30N_110E" "30N_120E"; do
  lat=$(echo $tile | grep -oP '^\d+')
  lon=$(echo $tile | grep -oP '_\K\d+')
  python scripts/global_surface_water.py download     --layer occurrence --tile $tile     --output water_${tile}.tif
done
```

### CI/CD Integration (GitHub Actions)
```yaml
# .github/workflows/update-water.yml
name: Update Surface Water
on:
  schedule:
    - cron: '0 0 1 1 *'  # Yearly
jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - run: |
          python scripts/global_surface_water.py download \
            --layer occurrence --tile 40N_110E \
            --output data/water_occ_40N_110E.tif
```

### GIS Integration (QGIS/GDAL)
```bash
# Mosaic multiple tiles
gdal_merge.py -o water_china.tif water_*.tif

# Reproject to UTM
gdalwarp -t_srs EPSG:32649 water_china.tif water_china_utm.tif
```

### PostgreSQL/PostGIS Import
```bash
raster2pgsql -s 4326 -I -C water_china.tif public.jrc_water | psql -d gis_db
```

### Performance Tips
- Tiles are 10°×10°; plan storage (~1-5 GB per layer per tile)
- Use `gdal_translate -a_nodata 0` to set nodata for visualization
- For change detection, download `change` layer and filter pixels with value 1 (gain) or 2 (loss)

---

## 中文说明

下载 JRC 全球地表水数据 —— 基于 30+ 年 Landsat 影像（1984-2024），30 米分辨率。

### 数据图层

| 图层 | ID | 描述 |
|------|-----|------|
| occurrence | occurrence | 水体出现频率 (0-100%) |
| change | change | 水体变化（增加/减少） |
| seasonality | seasonality | 有水月份数 (1-12) |
| recurrence | recurrence | 水体重现频率 (1-11) |
| transition | transition | 水体类型转换 |
| extent | extent | 最大水体范围（二值） |
| max_extent | max_extent | 最大水体范围图层 |

### 核心功能

- **6 种数据图层**：出现频率、变化、季节性、重现性、转换、范围
- **30 米分辨率**：完整 Landsat 分辨率
- **区域裁剪**：仅下载感兴趣区域
- **GeoTIFF 输出**：标准地理参考栅格
- **多种获取方式**：HTTP 直链下载或 GEE 方式
- **回退选项**：有无 Google Earth Engine 均可使用

### 获取方式

#### 方式一：HTTP 直链下载（推荐）

JRC 数据按全球分块存储。本工具自动生成与您的边界框相交的数据块下载链接，
并下载为 GeoTIFF 格式。

#### 方式二：Google Earth Engine（可选）

如果已安装 `geemap` 或 `earthengine-api`，可使用 GEE 进行更灵活的裁剪：

```python
import ee
ee.Initialize()
dataset = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
occurrence = dataset.select('occurrence')
```

### 使用示例

```bash
# 下载北京区域水体出现频率
python scripts/global_surface_water.py download \
  --layer occurrence \
  --bbox 116.0 39.5 116.8 40.2 \
  --output ./water/beijing_occurrence.tif

# 下载中国区域季节性图层
python scripts/global_surface_water.py download \
  --layer seasonality \
  --bbox 73 18 135 54 \
  --output ./water/china_seasonality.tif

# 下载小区域所有图层
python scripts/global_surface_water.py download \
  --layer all \
  --bbox 116.3 39.8 116.5 40.0 \
  --output ./water/beijing_all/

# 列出可用图层
python scripts/global_surface_water.py list-layers

# 查看数据集信息
python scripts/global_surface_water.py info
```

### 数据分块

JRC 全球地表水数据按 10° × 10° 分块存储。每个数据块约 300-600 MB。
工具自动识别与您的边界框相交的数据块并下载。

### 数据来源

- **数据集**: JRC/GSW1_4/GlobalSurfaceWater
- **门户**: https://global-surface-water.appspot.com/
- **GEE 目录**: https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater
- **许可证**: CC-BY 4.0 (EC JRC)
- **引用**: Pekel, J.F., Cottam, A., Gorelick, N., Belward, A.S., 2016. High-resolution mapping of global surface water and its long-term changes. Nature, 540, 418-422.
