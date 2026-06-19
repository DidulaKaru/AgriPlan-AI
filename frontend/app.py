import streamlit as st
import requests

# Page Configuration
st.set_page_config(
    page_title="AgriPlan AI - Intelligent Crop Planning",
    page_icon="🌾",
    layout="wide",
)

# Custom Premium CSS Injection
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Font styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Title Gradient Banner */
    .title-banner {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(56, 239, 125, 0.2);
    }
    
    .title-banner h1 {
        font-weight: 800;
        margin: 0;
        font-size: 2.8rem;
        color: white;
    }
    
    .title-banner p {
        font-weight: 300;
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Cards for recommendations */
    .crop-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #11998e;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .crop-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .crop-name {
        color: #11998e;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .yield-badge {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.8rem;
    }
    
    .reasoning-text {
        color: #455a64;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    /* Feasibility Report card */
    .report-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .report-title {
        color: #166534;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .report-content {
        color: #1f2937;
        line-height: 1.6;
    }
    
    /* Form sections */
    div[data-testid="stForm"] {
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        background-color: #fafafa;
    }
    </style>
""", unsafe_allow_html=True)

# Header Banner
st.markdown("""
    <div class="title-banner">
        <h1>AgriPlan AI</h1>
        <p>Intelligent, multi-agent agricultural planning and crop recommendations powered by RAG and LangGraph.</p>
    </div>
""", unsafe_allow_html=True)

# Main container split
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.markdown("### 🗺️ Farm Inputs")
    with st.form("input_form", clear_on_submit=False):
        st.write("Enter your location, soil composition, and budget details:")
        
        # Geolocation
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=37.7749, format="%.4f")
        with subcol2:
            lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=-122.4194, format="%.4f")
            
        st.markdown("**🌱 Soil N-P-K Composition**")
        n = st.slider("Nitrogen (N) - mg/kg", min_value=0, max_value=300, value=140)
        p = st.slider("Phosphorus (P) - mg/kg", min_value=0, max_value=300, value=50)
        k = st.slider("Potassium (K) - mg/kg", min_value=0, max_value=300, value=200)
        
        budget = st.number_input("Budget ($)", min_value=0.0, value=5000.0, step=500.0)
        
        submit = st.form_submit_button("Generate Recommendations", use_container_width=True)

with col2:
    st.markdown("### 📋 Analysis & Recommendations")
    
    if submit:
        payload = {
            "lat": lat,
            "lon": lon,
            "soil_npk": {
                "N": n,
                "P": p,
                "K": k
            },
            "budget": budget
        }
        
        with st.spinner("Invoking multi-agent coordination loop (Climate, Market, Feasibility)..."):
            try:
                response = requests.post("http://localhost:8000/recommend", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    
                    report = data.get("report", "No report text returned from agents.")
                    recommendations = data.get("recommendations", [])
                    
                    # Feasibility Report
                    st.markdown(f"""
                        <div class="report-card">
                            <div class="report-title">🌾 Executive Feasibility Report</div>
                            <div class="report-content">{report}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Crop recommendations
                    st.markdown("#### Recommended Crops")
                    if recommendations:
                        # Render cards
                        for rec in recommendations:
                            crop_name = rec.get("crop_name", "Unknown Crop")
                            yield_desc = rec.get("estimated_yield", "N/A")
                            reasoning = rec.get("reasoning", "No explanation provided.")
                            
                            st.markdown(f"""
                                <div class="crop-card">
                                    <div class="crop-name">🌱 {crop_name}</div>
                                    <div class="yield-badge">Est. Yield: {yield_desc}</div>
                                    <div class="reasoning-text"><strong>Reasoning:</strong> {reasoning}</div>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No crop recommendations generated for current inputs.")
                        
                else:
                    st.error(f"Error from API backend (Status {response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to the backend server. Make sure FastAPI is running on http://localhost:8000. Details: {e}")
    else:
        st.info("Fill out the farm details form on the left and submit to view recommendations.")
