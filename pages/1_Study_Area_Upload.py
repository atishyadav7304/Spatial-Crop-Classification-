import streamlit as st
import geopandas as gpd
import pandas as pd
import tempfile
import os
import zipfile
import io
import leafmap.foliumap as leafmap

st.set_page_config(page_title="Step 1: Study Area", layout="wide")

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
def save_uploaded_shapefile(uploaded_files):
    temp_dir = tempfile.mkdtemp()
    shp_path = None
    for f in uploaded_files:
        file_path = os.path.join(temp_dir, f.name)
        with open(file_path, "wb") as out_file:
            out_file.write(f.read())
        if f.name.endswith('.shp'):
            shp_path = file_path
    return shp_path

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
st.title("Step 1: Upload Command Area")
st.write("Upload the study area shapefile to define the primary boundaries for your hydrological modeling and spatial analysis.")

study_files = st.file_uploader(
    "Upload Study Area Shapefile (.shp, .shx, .dbf, .prj)", 
    type=["shp", "shx", "dbf", "prj"], 
    accept_multiple_files=True
)

if study_files and len([f for f in study_files if f.name.endswith('.shp')]) > 0:
    if st.button("Load Study Area"):
        with st.spinner("Processing shapefile..."):
            shp_path = save_uploaded_shapefile(study_files)
            gdf = gpd.read_file(shp_path)
            
            # Ensure CRS exists; default to WGS84 if missing
            if gdf.crs is None: 
                gdf.set_crs(epsg=4326, inplace=True)
                
            st.session_state['study_gdf'] = gdf

# Display Results if Data is Loaded
if st.session_state['study_gdf'] is not None:
    st.success("Command Area Loaded Successfully!")
    
    view_mode = st.radio("Choose Preview Mode:", ["Interactive Map", "Attribute Table"], horizontal=True)
    
    if view_mode == "Interactive Map":
        st.subheader("Study Area Map Preview")
        
        # Reproject to EPSG:4326 specifically for Folium/Leafmap visualization
        display_gdf = st.session_state['study_gdf'].to_crs(epsg=4326)
        
        # Initialize Leafmap
        m = leafmap.Map()
        m.add_gdf(display_gdf, layer_name="Command Area", fill_colors=["blue"], info_mode="on_click")
        
        # Render in Streamlit
        m.to_streamlit(height=500)
        
    elif view_mode == "Attribute Table":
        st.subheader("Shapefile Attribute Table")
        df_attributes = pd.DataFrame(st.session_state['study_gdf'].drop(columns='geometry'))
        st.dataframe(df_attributes)
    
    st.divider()
    st.markdown("### Export")
    zip_data = create_shapefile_zip(st.session_state['study_gdf'], "command_area_export")
    st.download_button(
        label="Download Study Area Shapefile (ZIP)", 
        data=zip_data, 
        file_name="command_area_export.zip", 
        mime="application/zip"
    )