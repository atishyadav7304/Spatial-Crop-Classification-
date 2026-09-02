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

st.set_page_config(page_title="Step 3: Population Stats", layout="wide")

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
st.title("Step 3: Population Zonal Statistics")

if st.session_state['grid_gdf'] is None:
    st.warning("⚠️ Please complete Step 2 (Centroids & Grid Generation) before proceeding.")
else:
    st.write("Upload a population raster layer. The tool will calculate the total population (pixel sum) for each 5km grid.")

    pop_raster = st.file_uploader("Upload Population Raster (.tif)", type=["tif"])
    
    if pop_raster:
        if st.button("Calculate Population Sum per Grid"):
            with st.spinner("Extracting zonal sums from raster..."):
                grid_gdf = st.session_state['grid_gdf'].copy()
                pop_path = save_uploaded_raster(pop_raster)
                
                # --- NEW FIX: Align CRS before zonal stats to prevent memory crash ---
                with rasterio.open(pop_path) as src:
                    raster_crs = src.crs
                
                # Reproject a temporary copy of the grid to match the raster perfectly
                grid_for_stats = grid_gdf.to_crs(raster_crs)
                
                # Execute zonal statistics on the perfectly aligned geometries
                stats = zonal_stats(grid_for_stats, pop_path, stats="sum")
                
                # Extract sums and handle potential None values (grids outside raster extent)
                grid_gdf['Population'] = [s['sum'] if s['sum'] else 0 for s in stats]
                
                st.session_state['pop_done'] = grid_gdf

# Display Results if Data is Processed
if st.session_state.get('pop_done') is not None:
    st.success("Population statistics calculated successfully!")
    df_pop = st.session_state['pop_done']
    id_col = st.session_state.get('id_col', 'Grid_ID')
    
    # Grand Total Metric
    total_pop = df_pop['Population'].sum()
    st.info(f"### 📊 Total Population in Processed Grids: **{total_pop:,.0f}**")
    
    view_mode = st.radio("Choose Preview Mode:", ["Interactive Map", "Attribute Table"], horizontal=True)
    
    if view_mode == "Interactive Map":
        st.subheader("Population Grid Map (Click Grids for Details)")
        
        # Reproject for Leafmap visualization
        display_gdf = df_pop.to_crs(epsg=4326)
        
        m = leafmap.Map()
        # Add Study Area as background reference if available
        if st.session_state['study_gdf'] is not None:
            study_display = st.session_state['study_gdf'].to_crs(epsg=4326)
            m.add_gdf(study_display, layer_name="Command Area", fill_colors=["none"], weight=2)
            
        # Add Populated Grids
        m.add_gdf(display_gdf, layer_name="Population Grids", fill_colors=["orange"], info_mode="on_click")
        
        m.to_streamlit(height=500)
        
    elif view_mode == "Attribute Table":
        st.subheader("Shapefile Attribute Table")
        # Ensure geometry is dropped for clean tabular rendering
        df_attributes = pd.DataFrame(df_pop.drop(columns='geometry'))
        
        # Safely Reorder columns to show ID and Population first
        available_cols = df_attributes.columns.tolist()
        if id_col in available_cols:
            cols = [id_col, 'Population'] + [c for c in available_cols if c not in [id_col, 'Population']]
        else:
            cols = ['Population'] + [c for c in available_cols if c != 'Population']
            
        st.dataframe(df_attributes[cols])
    
    st.divider()
    st.markdown("### Export")
    zip_data = create_shapefile_zip(df_pop, "population_grids")
    st.download_button(
        label="Download Population Grid Shapefile (ZIP)", 
        data=zip_data, 
        file_name="population_grids.zip", 
        mime="application/zip"
    )