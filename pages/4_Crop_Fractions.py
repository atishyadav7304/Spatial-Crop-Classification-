import streamlit as st
import geopandas as gpd
import pandas as pd
import tempfile
import os
import rasterio
from rasterstats import zonal_stats
import zipfile
import io
import leafmap.foliumap as leafmap

st.set_page_config(page_title="Step 5: Seasonal Crop Fractions", layout="wide")

# ---------------------------------------------------------
# INITIALIZE SHARED MEMORY
# ---------------------------------------------------------
state_keys = ['study_gdf', 'clipped_centroids', 'grid_gdf', 'pop_done', 'crop_done', 'id_col']
for key in state_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def save_uploaded_raster(uploaded_file):
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as out_file:
        out_file.write(uploaded_file.read())
    return file_path

def create_shapefile_zip(gdf, filename):
    temp_dir = tempfile.mkdtemp()
    shp_path = os.path.join(temp_dir, f"{filename}.shp")
    gdf.to_file(shp_path)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
            file_path = os.path.join(temp_dir, f"{filename}{ext}")
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=f"{filename}{ext}")
    zip_buffer.seek(0)
    return zip_buffer

# ---------------------------------------------------------
# UI & PROCESSING
# ---------------------------------------------------------
st.title("Step 5: Seasonal Crop Area Fractions & Final Export")

# Fallback to get the most updated grid geometries (prefer pop_done if available)
base_gdf = st.session_state.get('pop_done')
if base_gdf is None:
    base_gdf = st.session_state.get('grid_gdf')

if base_gdf is None:
    st.warning("⚠️ Please complete Grid Generation (Step 2) and Population (Step 3) before proceeding.")
else:
    st.write("Upload your categorical crop classification rasters for different seasons. The tool will calculate the spatial fraction of each crop class assuming a constant 5km x 5km grid area.")

    num_seasons = st.number_input("How many seasonal rasters do you want to upload?", min_value=1, max_value=10, value=1, step=1)
    
    seasonal_inputs = []
    st.markdown("#### 🌾 Define Seasons and Upload Rasters")
    
    for i in range(num_seasons):
        col1, col2 = st.columns([1, 2])
        with col1:
            season_name = st.text_input(f"Season {i+1} Name (e.g., 2022-23 Rabi):", value=f"Season_{i+1}", key=f"name_{i}")
        with col2:
            raster_file = st.file_uploader(f"Upload Crop Raster for {season_name} (.tif)", type=["tif"], key=f"file_{i}")
            
        if raster_file is not None:
            seasonal_inputs.append((season_name, raster_file))
            
    st.divider()
    
    if len(seasonal_inputs) > 0 and st.button("Calculate Seasonal Crop Fractions"):
        with st.spinner("Extracting categorical statistics and computing fractions for all seasons..."):
            grid_gdf = base_gdf.copy()
            
            # Constant area for a 5km x 5km grid in square meters
            FIXED_GRID_AREA_SQM = 5000 * 5000  # 25,000,000 sq meters
            
            for season_name, crop_raster in seasonal_inputs:
                crop_path = save_uploaded_raster(crop_raster)
                
                # 1. Get pixel resolution using rasterio
                with rasterio.open(crop_path) as src:
                    transform = src.transform
                    pixel_area_sq_m = abs(transform[0] * transform[4])
                
                # Calculate the exact number of pixels that fit in a 5x5 km grid
                total_pixels_5km = FIXED_GRID_AREA_SQM / pixel_area_sq_m
                
                # 2. Run categorical zonal stats (this returns the pixel counts per class)
                stats = zonal_stats(grid_gdf, crop_path, categorical=True)
                
                # 3. Compute fractions based on the fixed 5x5km pixel count
                for i, stat in enumerate(stats):
                    for val, count in stat.items():
                        # Fraction = (pixels of crop in grid) / (total pixels in 5x5km grid)
                        fraction = count / total_pixels_5km
                        
                        # Replace spaces with underscores for clean column names
                        clean_season = season_name.replace(" ", "_")
                        grid_gdf.at[grid_gdf.index[i], f'{clean_season}_C{val}_Frac'] = round(fraction, 4)
            
            # Fill missing crop classes in grids where they don't appear with 0
            grid_gdf = grid_gdf.fillna(0)
            st.session_state['crop_done'] = grid_gdf

# Display Results & Final Exports
if st.session_state.get('crop_done') is not None:
    st.success("Seasonal crop fractions calculated! Final dataset is ready.")
    df_final = st.session_state['crop_done']
    
    view_mode = st.radio("Choose Preview Mode:", ["Interactive Map", "Attribute Table"], horizontal=True)
    
    if view_mode == "Interactive Map":
        st.subheader("Final Spatial Distribution (Click Grids for All Metrics)")
        
        display_gdf = df_final.to_crs(epsg=4326)
        m = leafmap.Map()
        
        if st.session_state['study_gdf'] is not None:
            study_display = st.session_state['study_gdf'].to_crs(epsg=4326)
            m.add_gdf(study_display, layer_name="Command Area", fill_colors=["none"], weight=2)
            
        # Add grids - clicking them will reveal Population, Demand, and Crop fractions
        m.add_gdf(display_gdf, layer_name="Analyzed Grids", fill_colors=["green"], info_mode="on_click")
        m.to_streamlit(height=500)
        
    elif view_mode == "Attribute Table":
        st.subheader("Final Attribute Table")
        df_attributes = pd.DataFrame(df_final.drop(columns='geometry'))
        st.dataframe(df_attributes)
    
    st.divider()
    st.markdown("### Final Exports")
    st.write("Download your fully processed dataset containing grid geometries, population totals, domestic water demand, and seasonal crop fractions.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        zip_data = create_shapefile_zip(df_final, "final_geospatial_grids")
        st.download_button(
            label="Download Final Shapefile (ZIP)", 
            data=zip_data, 
            file_name="final_geospatial_grids.zip", 
            mime="application/zip"
        )
        
    with col2:
        output_excel = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        pd.DataFrame(df_final.drop(columns='geometry')).to_excel(output_excel.name, index=False)
        with open(output_excel.name, 'rb') as f:
            st.download_button(
                label="Download Final Excel Report (.xlsx)", 
                data=f, 
                file_name="Geospatial_Final_Report.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
