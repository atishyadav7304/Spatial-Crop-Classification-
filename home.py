import streamlit as st

st.set_page_config(
    page_title="Geospatial Dashboard",
    page_icon="🌍",
    layout="wide"
)

# ---------------------------------------------------------
# INITIALIZE SHARED MEMORY
# ---------------------------------------------------------
state_keys = ['study_gdf', 'clipped_centroids', 'grid_gdf', 'pop_done', 'crop_done', 'id_col']
for key in state_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------------------------------------------------
# MAIN LANDING PAGE CONTENT
# ---------------------------------------------------------
st.title("🌍 Geospatial Dashboard")
st.markdown("### Automated Grid Generation & Zonal Statistics Pipeline")

st.markdown("""
Welcome to the spatial processing dashboard. This tool streamlines the extraction of continuous population totals 
and categorical crop classification fractions across gapless grid meshes for agricultural and hydrological analysis.

---

### 📋 Workflow Steps:
1. **Step 1: Upload Command Area** — Upload study area boundary shapefiles and verify geometry.
2. **Step 2: Centroids & Grids** — Generate gapless Voronoi mesh grids centered on point attributes and clipped to study area boundaries.
3. **Step 3: Population Stats** — Calculate continuous pixel sums (Total Population) per grid cell.
4. **Step 4: Crop Fractions** — Compute categorical crop area fractions and export final Shapefiles and Excel reports.
""")

st.divider()

# ---------------------------------------------------------
# SAMPLE DATA DOWNLOAD SECTION
# ---------------------------------------------------------
st.subheader("🧪 Sample Datasets for Testing")
st.write("If you don't have your own spatial data, you can download a complete set of trial shapefiles and rasters below to test the workflow.")

# PASTE YOUR GOOGLE DRIVE LINK IN THE QUOTES BELOW
drive_link = "https://drive.google.com/drive/folders/1WcvOUwSM6pK-tozNW2yZLnCvw2SUkLA3?usp=drive_link"

st.link_button("☁️ Download Sample Data from Google Drive", drive_link, type="primary")

st.divider()
st.info("👈 Use the left sidebar to navigate to **Step 1** to begin processing.")
