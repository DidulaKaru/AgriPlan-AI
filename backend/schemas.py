from pydantic import BaseModel
from typing import Dict

class FarmerInput(BaseModel):
    lat: float
    lon: float
    soil_npk: Dict[str, int]
    budget: float

class CropRecommendation(BaseModel):
    crop_name: str
    estimated_yield: str
    reasoning: str
