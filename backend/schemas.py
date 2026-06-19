from pydantic import BaseModel
from typing import Dict, List

class FarmerInput(BaseModel):
    lat: float
    lon: float
    soil_npk: Dict[str, int]
    budget: float
    land_area: float  # in acres
    machinery: List[str]  # e.g., ["tractor", "tillers", "drip_irrigation", "none"]

class CropRecommendation(BaseModel):
    crop_name: str
    farming_method: str  # e.g., "Open Field", "Greenhouse", "Hydroponic Pivot"
    estimated_yield: str
    total_estimated_cost_usd: float
    soil_amendment_required: bool
    fertilizer_advice: str  # Provide exact N-P-K correction steps if true, otherwise "None"
    reasoning: str  # Explicitly explaining how budget, land area, and machinery forced this choice
