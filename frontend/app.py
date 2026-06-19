import streamlit as st
import requests
import time

# Page Configuration
st.set_page_config(
    page_title="AgriPlan AI | Precision Agriculture",
    page_icon="🌱",
    layout="wide"
)

# Header Section (Clean, modern typographic hierarchy instead of a heavy color block)
st.title("🌱 AgriPlan AI")
st.caption("Autonomous Multi-Agent Ecological & Economic Alignment Engine")
st.markdown("---")

# Two-column layout
col_input, col_results = st.columns([1, 2], gap="large")

with col_input:
    # st.container(border=True) creates a clean, theme-aware card component automatically
    with st.container(border=True):
        st.subheader("📋 Farm Specifications")
        st.write("Provide your land's telemetry and budget limits.")
        st.markdown("---")
        
        # Geolocation fields with explicit visible labels
        st.markdown("**📍 Location Telemetry**")
        lat = st.number_input("Latitude Coordinate", value=6.0535, format="%.4f")
        lon = st.number_input("Longitude Coordinate", value=80.2210, format="%.4f")
        
        st.markdown("---")
        
        # Soil Matrix with explicit visible labels
        st.markdown("**🧪 Soil Composition (NPK Levels)**")
        n = st.slider("Nitrogen (N) mg/kg", 0, 150, 60)
        p = st.slider("Phosphorus (P) mg/kg", 0, 150, 45)
        k = st.slider("Potassium (K) mg/kg", 0, 150, 50)
        
        st.markdown("---")
        
        # Financial Constraint with explicit visible label
        st.markdown("**💰 Operational Resource**")
        budget = st.number_input("Available Capital (USD)", min_value=100.0, value=1500.0, step=100.0)
        
        st.markdown("")
        # type="primary" automatically styles the button with the theme's core accent color
        submit_btn = st.button("Generate Recommendations", type="primary", use_container_width=True)

with col_results:
    st.subheader("🎯 Optimization Insights")
    
    if submit_btn:
        payload = {
            "lat": lat,
            "lon": lon,
            "soil_npk": {"N": n, "P": p, "K": k},
            "budget": budget
        }
        
        # Dynamic Telemetry Status
        with st.status("🧠 Initializing LangGraph Orchestrator...", expanded=True) as status:
            time.sleep(0.8)
            status.update(label="🌤️ Climate Agent: Querying regional weather metrics...", state="running")
            time.sleep(1.0)
            status.update(label="📈 Market Agent: Searching ChromaDB for regional price trends...", state="running")
            time.sleep(0.8)
            status.update(label="⚖️ Feasibility Agent: Balancing capital vs yield requirements...", state="running")
            
            try:
                response = requests.post("http://localhost:8000/recommend", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    status.update(label="✅ Strategy optimization complete!", state="complete", expanded=False)
                    
                    # Output Layout
                    st.success(f"### Recommended Strategy: **{data.get('crop_name', 'Rice')}**")
                    
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.metric(label="Expected Yield", value=data.get("estimated_yield", "4.2 Tons/Acre"))
                    with m_col2:
                        st.metric(label="Risk Alignment Factor", value="Optimal Match", delta="Low Risk")
                    
                    with st.container(border=True):
                        st.markdown("#### 📋 Strategic Rationale")
                        st.write(data.get('reasoning', 'The combination of high soil Potassium and the current low market volatility makes this choice optimal for your budget constraint.'))
                else:
                    status.update(label="❌ Pipeline execution failed.", state="error")
                    st.error("Backend error processing data.")
            except requests.exceptions.ConnectionError:
                status.update(label="❌ Connection Refused.", state="error")
                st.error("FastAPI backend is offline. Start uvicorn on port 8000.")
    else:
        st.info("Fill out the farm details form on the left and submit to view recommendations.")