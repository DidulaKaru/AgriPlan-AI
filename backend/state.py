from typing import TypedDict, Dict, Any, Optional
from backend.schemas import FarmerInput

class AgentState(TypedDict):
    farmer_data: Optional[FarmerInput]
    climate_data: Dict[str, Any]
    market_trends: Dict[str, Any]
    feasibility_report: Dict[str, Any]
    next_node: Optional[str]
