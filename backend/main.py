from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from backend.schemas import FarmerInput
from backend.graph import app as graph_app
from backend.database import initialize_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize ChromaDB and RAG setup on startup
    initialize_database()
    yield

app = FastAPI(title="AgriPlan AI API", lifespan=lifespan)

@app.post("/recommend")
async def recommend_crops(farmer_input: FarmerInput):
    try:
        # Explicit state initialization to ensure absolute compatibility with worker nodes
        initial_state = {
            "farmer_data": {
                "lat": farmer_input.lat,
                "lon": farmer_input.lon,
                "budget": farmer_input.budget,
                "land_area": farmer_input.land_area,
                "machinery": farmer_input.machinery
            },
            # Map soil metrics at the root level AND inside farmer data to prevent key errors
            "soil_data": farmer_input.soil_npk, 
            "soil_npk": farmer_input.soil_npk,
            
            "climate_data": {},
            "market_trends": "",
            "feasibility_report": None,
            
            # Explicitly set the initial target node string so the graph router triggers correctly
            "next_node": "climate_agent" 
        }
        
        # Invoke the multi-agent graph execution loop
        final_state = graph_app.invoke(initial_state)
        
        # Extract the final report payload
        report = final_state.get("feasibility_report")
        
        # If the graph returned a Pydantic object model, convert it to a clean JSON dict for the frontend
        if hasattr(report, "model_dump"):
            return report.model_dump()
            
        return report if report else {}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))