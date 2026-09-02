import streamlit as st
import geopandas as gpd
import pandas as pd
import tempfile
import os
import zipfile
import io
import leafmap.foliumap as leafmap
from shapely.geometry import box

st.set_page_config(page_title="Step 2: Centroids & Grids", layout="wide")

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
st.title("Step 2: Grid Generation & Clipping")

if st.session_state['study_gdf'] is None:
    st.warning("⚠️ Please complete Step 1 (Upload Command Area) before proceeding.")
else:
    st.write("Upload your centroid points. The tool will perfectly center a continuous 5km mesh on each point with no gaps, and clip the results strictly to your study area boundary.")

    centroid_files = st.file_uploader(
        "Upload Centroid Shapefile (.shp, .shx, .dbf, .prj)", 
        type=["shp", "shx", "dbf", "prj"], 
        accept_multiple_files=True
    )
    
    if centroid_files and len([f for f in centroid_files if f.name.endswith('.shp')]) > 0:
        shp_path = save_uploaded_shapefile(centroid_files)
        native_centroids = gpd.read_file(shp_path)
        
        id_col = st.selectbox("Select Attribute Field for Grid Naming:", native_centroids.columns)
        
        if st.button("Generate & Clip Grids"):
            with st.spinner("Building perfectly centered contiguous grids..."):
                study_gdf = st.session_state['study_gdf']
                
                # 1. Ensure Centroids have a CRS
                if native_centroids.crs is None: 
                    native_centroids.set_crs(epsg=4326, inplace=True)
                
                # 2. Convert geographic coordinates to UTM ONLY IF NECESSARY
                # If they are already metric (which is likely if they spaced perfectly), keep the native CRS.
                process_crs = native_centroids.crs
                if process_crs.is_geographic:
                    process_crs = native_centroids.estimate_utm_crs()
                    cents_to_process = native_centroids.to_crs(process_crs)
                else:
                    cents_to_process = native_centroids
                
                # 3. Filter centroids by the study area's bounding box to speed up processing
                study_in_process_crs = study_gdf.to_crs(process_crs)
                buffered_bounds = study_in_process_crs.geometry.buffer(6000).total_bounds
                clip_box = box(*buffered_bounds)
                clip_gdf = gpd.GeoDataFrame(geometry=[clip_box], crs=process_crs)
                
                cents_filtered = gpd.clip(cents_to_process, clip_gdf)
                
                # 4. Generate the 5km Grid strictly in the native/metric geometry BEFORE projecting
                # This guarantees that if the points were perfectly spaced, the grids will perfectly touch.
                half = 2500.0
                grid_polys = [
                    box(geom.x - half, geom.y - half, geom.x + half, geom.y + half) 
                    for geom in cents_filtered.geometry
                ]
                
                perfect_grid_gdf = gpd.GeoDataFrame({id_col: cents_filtered[id_col]}, geometry=grid_polys, crs=process_crs)
                
                # 5. NOW reproject the perfect mesh and the filtered points to match the Study Area
                grid_aligned = perfect_grid_gdf.to_crs(study_gdf.crs)
                cents_aligned = cents_filtered.to_crs(study_gdf.crs)
                
                # 6. Clip the grids directly against the precise boundary of the Command Area
                clipped_grids = gpd.clip(grid_aligned, study_gdf)
                clipped_cents = gpd.clip(cents_aligned, study_gdf)
                
                # Save results
                st.session_state['clipped_centroids'] = clipped_cents
                st.session_state['grid_gdf'] = clipped_grids
                st.session_state['id_col'] = id_col

# Display Results
if st.session_state.get('grid_gdf') is not None:
    st.success("Grids Centered, Gapless, and Clipped Successfully!")
    
    view_mode = st.radio("Choose Preview Mode:", ["Interactive Map", "Attribute Table"], horizontal=True)
    
    if view_mode == "Interactive Map":
        st.subheader("Centered Grid Map Preview")
        
        m = leafmap.Map()
        
        # Reproject for Leafmap visualization
        study_display = st.session_state['study_gdf'].to_crs(epsg=4326)
        grid_display = st.session_state['grid_gdf'].to_crs(epsg=4326)
        cents_display = st.session_state['clipped_centroids'].to_crs(epsg=4326)
        
        m.add_gdf(study_display, layer_name="Command Area", fill_colors=["none"], weight=2)
        m.add_gdf(grid_display, layer_name="Clipped Grids", fill_colors=["blue"])
        m.add_gdf(cents_display, layer_name="Relevant Centroids", color="red")
        
        m.to_streamlit(height=500)
        
    elif view_mode == "Attribute Table":
        st.subheader("Clipped Grid Attribute Table")
        df_attributes = pd.DataFrame(st.session_state['grid_gdf'].drop(columns='geometry'))
        st.dataframe(df_attributes)
    
    st.divider()
    st.markdown("### Export")
    
    col1, col2 = st.columns(2)
    with col1:
        cent_zip = create_shapefile_zip(st.session_state['clipped_centroids'], "filtered_centroids")
        st.download_button("Download Filtered Centroids (ZIP)", data=cent_zip, file_name="filtered_centroids.zip")
    with col2:
        grid_zip = create_shapefile_zip(st.session_state['grid_gdf'], "gapless_grids")
        st.download_button("Download Gapless Grids (ZIP)", data=grid_zip, file_name="gapless_grids.zip")