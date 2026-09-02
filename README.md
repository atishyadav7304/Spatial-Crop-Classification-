# 🌍 Geospatial Dashboard

An automated, multi-page Streamlit web application designed for Land and Water Resources Engineering. This tool streamlines the complex spatial data processing required for distributed hydrological models (such as NHM-I), converting raw remote sensing datasets and coordinate points into structured, gapless grid frameworks with extracted zonal statistics.

## 📖 Project Overview

Preparing spatial inputs for basin-scale hydrological and agricultural water management models often requires tedious GIS processing. This dashboard automates the pipeline from raw command area shapefiles to fully attributed grid frameworks. It is specifically optimized to handle coordinate reference system (CRS) synchronizations dynamically, preventing common memory allocation failures when extracting data from high-resolution raster datasets.

The processed outputs are structured to support downstream advanced analytics, including eventual integration with LSTM-based prediction models and water demand modules.

## 🚀 Core Pipeline & Features

### 1. Command Area Initialization (`1_Study_Area_Upload.py`)
* **Dynamic CRS Handling:** Automatically detects and aligns the projection system of the uploaded study area shapefile.
* **Interactive Visualization:** Integrates `leafmap` and `folium` to render QGIS-style, interactive web maps directly in the browser for instant boundary verification.

### 2. Gapless Grid Generation (`2_Centroids_and_Grid.py`)
* **Voronoi (Thiessen) Polygon Math:** Solves the common issue of overlapping or gapped fishnet grids caused by projection distortion. The tool mathematically calculates the exact midpoints between adjacent input centroids to generate a 100% continuous, gapless spatial mesh.
* **Precision Clipping:** Applies a strict bounding box filter to optimize processing times, followed by a precise clip of the generated mesh to the exact boundaries of the command area.

### 3. Continuous Zonal Statistics (`3_Population_Stats.py`)
* **Memory-Optimized Extraction:** Prevents `numpy._core._exceptions._ArrayMemoryError` crashes by dynamically matching the CRS of the generated grid to the native projection of the input raster *before* processing.
* **Total Population Metrics:** Calculates the exact continuous pixel sum (e.g., Total Population) isolated within each 5km grid cell.

### 4. Categorical Area Fractions (`4_Crop_Fractions.py`)
* **Agricultural Zonal Stats:** Processes classified categorical rasters (e.g., crop classification maps).
* **Fractional Analysis:** Computes the true physical area of each pixel and calculates the exact spatial fraction of different crop classes within every individual grid cell.
* **Data Export:** Compiles all spatial geometries, population metrics, and crop fractions into downloadable Zipped Shapefiles and tabular `.xlsx` Excel reports.

## 🛠️ Technology Stack

* **Frontend Framework:** [Streamlit](https://streamlit.io/)
* **Geospatial Processing:** `geopandas`, `shapely`
* **Raster Analytics:** `rasterio`, `rasterstats`
* **Interactive Mapping:** `leafmap`, `streamlit-folium`, `folium`
* **Data Manipulation:** `pandas`, `numpy`

## 📂 Repository Architecture

```text
├── Home.py                      # Main landing page & session state architecture
├── requirements.txt             # Python environment dependencies
└── pages/
    ├── 1_Study_Area_Upload.py   # Step 1: Boundary upload and map rendering
    ├── 2_Centroids_and_Grid.py  # Step 2: Gapless Voronoi grid math & spatial clipping
    ├── 3_Population_Stats.py    # Step 3: Continuous raster zonal stats (Population)
    └── 4_Crop_Fractions.py      # Step 4: Categorical raster stats (Crop Fractions) & Export
