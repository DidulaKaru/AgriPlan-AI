import streamlit as st
import requests
import time
import folium
from streamlit_folium import st_folium

# Page Config
st.set_page_config(
    page_title="AgriPlan AI | Precision Agriculture",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 AgriPlan AI")
st.caption("Autonomous Multi-Agent Ecological & Economic Alignment Engine")
st.markdown("---")

# Two-column grid layout
col_input, col_results = st.columns([1, 1], gap="large")

with col_input:
    with st.container(border=True):
        st.subheader("📋 Farm Configuration")
        st.write("Configure your geographical and soil metrics across the tabs below.")
        
        # Balance Layout: Split configurations into step-by-step tabs
        tab_geo, tab_soil = st.tabs(["📍 1. Location Selection", "🧪 2. Soil & Resources"])
        
        with tab_geo:
            st.markdown("**Click anywhere on the map to automatically pin your farm coordinates:**")
            
            # Default center: Faculty of Engineering, University of Ruhuna (Galle)
            default_lat = 6.0535
            default_lon = 80.2210
            
            # Maintain coordinates in session state to handle reactive changes smoothly
            if "lat" not in st.session_state:
                st.session_state.lat = default_lat
            if "lon" not in st.session_state:
                st.session_state.lon = default_lon

            # Render an interactive Folium Map
            m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=12)
            folium.Marker(
                [st.session_state.lat, st.session_state.lon], 
                popup="Selected Farm Location", 
                tooltip="Selected Location"
            ).add_to(m)
            
            # Capture the click data maps return
            map_data = st_folium(m, height=350, width=None, use_container_width=True)
            
            # Update values reactively if the user clicks a new pixel point
            if map_data and map_data.get("last_clicked"):
                st.session_state.lat = round(map_data["last_clicked"]["lat"], 4)
                st.session_state.lon = round(map_data["last_clicked"]["lng"], 4)
                # Force rerun to instantly visually update the coordinate labels
                st.rerun()

            # Read-only confirmation metric display for the user
            c1, c2 = st.columns(2)
            c1.metric("Pinned Latitude", st.session_state.lat)
            c2.metric("Pinned Longitude", st.session_state.lon)

        with tab_soil:
            st.markdown("**🧪 Soil Nutrient Density (NPK Matrix)**")
            n = st.slider("Nitrogen (N) mg/kg", 0, 150, 60)
            p = st.slider("Phosphorus (P) mg/kg", 0, 150, 45)
            k = st.slider("Potassium (K) mg/kg", 0, 150, 50)
            
            st.markdown("---")
            st.markdown("**💰 Financial Resource Limit**")
            budget = st.number_input("Available Capital (USD)", min_value=100.0, value=1500.0, step=100.0)
            
            st.markdown("")
            submit_btn = st.button("Generate Recommendations", type="primary", use_container_width=True)

with col_results:
    st.subheader("🎯 Optimization Insights")
    
    if submit_btn:
        payload = {
            "lat": st.session_state.lat,
            "lon": st.session_state.lon,
            "soil_npk": {"N": n, "P": p, "K": k},
            "budget": budget
        }
        
        with st.status("🧠 Initializing LangGraph Orchestrator...", expanded=True) as status:
            time.sleep(0.6)
            status.update(label="🌤️ Climate Agent: Querying regional weather metrics...", state="running")
            time.sleep(0.6)
            status.update(label="📈 Market Agent: Searching ChromaDB for regional price trends...", state="running")
            time.sleep(0.6)
            status.update(label="⚖️ Feasibility Agent: Balancing capital vs yield requirements...", state="running")
            
            try:
                response = requests.post("http://localhost:8000/recommend", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    status.update(label="✅ Strategy optimization complete!", state="complete", expanded=False)
                    
                    st.success(f"### Recommended Strategy: **{data.get('crop_name', 'Rice')}**")
                    
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.metric(label="Expected Yield", value=data.get("estimated_yield", "4.2 Tons/Acre"))
                    with m_col2:
                        st.metric(label="Risk Alignment Factor", value="Optimal Match", delta="Low Risk")
                    
                    with st.container(border=True):
                        st.markdown("#### 📋 Strategic Rationale")
                        st.write(data.get('reasoning', 'Optimized based on local soil and economic criteria.'))
                else:
                    status.update(label="❌ Pipeline execution failed.", state="error")
                    st.error("Backend error processing data.")
            except requests.exceptions.ConnectionError:
                status.update(label="❌ Connection Refused.", state="error")
                st.error("FastAPI backend is offline.")
    else:
        st.info("Pin your farm location and configure attributes to activate recommendations.")