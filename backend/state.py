from typing import TypedDict, Dict, Any, Optional, Union
from backend.schemas import FarmerInput, CropRecommendation

class AgentState(TypedDict):
    farmer_data: Optional[FarmerInput]
    climate_data: Dict[str, Any]
    market_trends: Dict[str, Any]
    feasibility_report: Optional[Union[CropRecommendation, Dict[str, Any]]]
    next_node: Optional[str]
