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
        # Initialize LangGraph state with farmer data
        initial_state = {
            "farmer_data": farmer_input.model_dump(),
            "climate_data": {},
            "market_trends": {},
            "feasibility_report": {},
            "next_node": None
        }
        
        # Invoke the multi-agent graph execution loop
        final_state = graph_app.invoke(initial_state)
        
        # Return final feasibility report containing recommendations
        return final_state.get("feasibility_report", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
