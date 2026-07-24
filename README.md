# JRC Global Surface Water Download

## English

Download JRC Global Surface Water data layers — derived from 30+ years of Landsat imagery.

### Installation

**ClawHub:**
```bash
clawhub install global-surface-water
```

**Claude Code / skills.sh:**
```bash
claude skills install global-surface-water
```

**Manual:**
```bash
git clone <repo-url> global-surface-water
cd global-surface-water
pip install requests tqdm
```

### Quick Start

```bash
# Download water occurrence for a region
python scripts/global_surface_water.py download \
  --layer occurrence \
  --bbox 116.0 39.5 116.8 40.2 \
  --output ./water/beijing_occurrence.tif

# List available layers
python scripts/global_surface_water.py list-layers

# Show dataset info
python scripts/global_surface_water.py info
```

### Data Source

- **Dataset**: JRC/GSW1_4/GlobalSurfaceWater
- **Portal**: https://global-surface-water.appspot.com/
- **License**: CC-BY 4.0 (EC JRC)
- **Citation**: Pekel, J.F., Cottam, A., Gorelick, N., Belward, A.S., 2016. High-resolution mapping of global surface water and its long-term changes. Nature, 540, 418-422.

---

## 中文

下载 JRC 全球地表水数据 —— 基于 30+ 年 Landsat 影像。

### 安装

**ClawHub:**
```bash
clawhub install global-surface-water
```

**Claude Code / skills.sh:**
```bash
claude skills install global-surface-water
```

**手动安装:**
```bash
git clone <repo-url> global-surface-water
cd global-surface-water
pip install requests tqdm
```

### 快速开始

```bash
# 下载北京区域水体出现频率
python scripts/global_surface_water.py download \
  --layer occurrence \
  --bbox 116.0 39.5 116.8 40.2 \
  --output ./water/beijing_occurrence.tif

# 列出可用图层
python scripts/global_surface_water.py list-layers

# 查看数据集信息
python scripts/global_surface_water.py info
```

### 数据来源

- **数据集**: JRC/GSW1_4/GlobalSurfaceWater
- **门户**: https://global-surface-water.appspot.com/
- **许可证**: CC-BY 4.0 (EC JRC)
- **引用**: Pekel, J.F., Cottam, A., Gorelick, N., Belward, A.S., 2016. High-resolution mapping of global surface water and its long-term changes. Nature, 540, 418-422.
