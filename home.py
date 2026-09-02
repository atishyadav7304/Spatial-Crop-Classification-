import streamlit as st

# Configure the main page layout and metadata
st.set_page_config(
    page_title="Geospatial Dashboard",
    page_icon="🌍",
    layout="wide"
)

# ---------------------------------------------------------
# INITIALIZE SHARED MEMORY (Crucial for Multi-Page Apps)
# ---------------------------------------------------------
state_keys = [
    'study_gdf', 
    'clipped_centroids', 
    'grid_gdf', 
    'pop_done', 
    'crop_done', 
    'id_col'
]

for key in state_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------------------------------------------------
# HOME PAGE UI
# ---------------------------------------------------------
st.title("🌍 Geospatial Analysis Dashboard")
st.markdown("### Land & Water Resources Engineering Spatial Tool")

st.write(
    "Welcome to the multi-page spatial analysis hub. This application is designed to handle "
    "end-to-end geospatial workflows including fishnet grid generation, spatial clipping, "
    "and continuous/categorical zonal statistics."
)

st.info("👈 **Select a step from the sidebar to begin processing your data.**")

# Dashboard Overview
st.markdown("---")
st.markdown("**Pipeline Overview:**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.success("**Step 1**\n\nUpload and preview the Command Area (Study Area) boundary.")
with col2:
    st.warning("**Step 2**\n\nClip centroids to the study area and generate a 5km Fishnet Grid.")
with col3:
    st.info("**Step 3**\n\nExtract continuous zonal statistics (Total Population) for each grid.")
with col4:
    st.error("**Step 4**\n\nExtract categorical zonal statistics (Crop Area Fractions) for each grid.")

st.markdown("---")
st.caption("Ensure your `.shp` uploads always include the corresponding `.shx`, `.dbf`, and `.prj` files to maintain accurate coordinate reference systems (CRS) across the pipeline.")