import os
import json
from openai import OpenAI
from backend.state import AgentState
from backend.database import query_market_trends
from backend.schemas import CropRecommendation

# Redirect the OpenAI SDK to use OpenRouter's endpoint
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Use a highly capable, free open-source model that supports tool calling
MODEL_NAME = "openrouter/free" 

def climate_agent(state: AgentState) -> dict:
    """
    Climate Agent: Analyzes climate and weather viability for the farmer's location.
    """
    farmer_data = state.get("farmer_data")
    if not farmer_data:
        return {"climate_data": {"error": "No farmer data provided."}}
        
    lat = farmer_data.get("lat")
    lon = farmer_data.get("lon")
    soil_npk = farmer_data.get("soil_npk")
    
    prompt = f"""You are an Agricultural Climate expert. Analyze the climate conditions for a farm located at:
Latitude: {lat}
Longitude: {lon}
Soil NPK values: {soil_npk}

Provide a short summary (under 100 words) of the climate viability, expected weather conditions, and general soil health suitability."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a professional agronomist specializing in climate analysis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    analysis = response.choices[0].message.content.strip()
    return {"climate_data": {"summary": analysis}}

def market_agent(state: AgentState) -> dict:
    """
    Market Agent: Evaluates market conditions and demand trends using ChromaDB semantic lookup.
    """
    # Retrieve relevant market trends context from local ChromaDB
    query = "crop demand pricing trends market forecast"
    rag_context = query_market_trends(query)
    
    prompt = f"""You are an Agricultural Economist. Analyze market trends for crops based on the following current market reports:
---
{rag_context}
---

Provide a brief analysis (under 100 words) identifying high-demand crops, price trends, and potential market opportunities."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an agricultural market economist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    analysis = response.choices[0].message.content.strip()
    return {"market_trends": {"analysis": analysis}}

def feasibility_agent(state: AgentState) -> dict:
    """
    Feasibility Agent: Synthesizes climate and market data to output a final feasibility and crop recommendation.
    """
    farmer_data = state.get("farmer_data")
    if isinstance(farmer_data, dict):
        budget = farmer_data.get("budget", 0.0)
    elif farmer_data is not None:
        budget = getattr(farmer_data, "budget", 0.0)
    else:
        budget = 0.0

    climate_data = state.get("climate_data") or {}
    ecological_limits = climate_data.get("summary", "No climate data available.")

    market_trends = state.get("market_trends") or {}
    market_context = market_trends.get("analysis", "No market trends data available.")

    system_prompt = (
        "You are a hard-nosed agricultural economist. Evaluate the input text data and choose "
        "the single most viable crop strategy. "
        "Absolute restriction: If a crop's cultivation cost per acre exceeds the farmer's available capital "
        "(budget), it must be rejected instantly, regardless of its market popularity or potential yield. "
        "Select the single most viable crop that fits within the budget and aligns with the climate/ecological limits and market trends."
    )

    user_prompt = f"""
Please evaluate the following information and recommend the single best crop strategy:

Farmer's Available Capital (Budget): ${budget}
Ecological & Climate Limits: {ecological_limits}
Market Trends & Pricing Context: {market_context}
"""

    response = client.beta.chat.completions.parse(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=CropRecommendation,
        temperature=0.2
    )

    feasibility_report = response.choices[0].message.parsed
    if not feasibility_report:
        feasibility_report = CropRecommendation(
            crop_name="Failed to recommend",
            estimated_yield="N/A",
            reasoning="Pydantic parsing failed or model returned invalid structure."
        )

    return {
        "feasibility_report": feasibility_report,
        "next_node": "__end__"
    }

def supervisor_agent(state: AgentState) -> dict:
    """
    Supervisor Agent: Reads the state and determines which node to visit next.
    Options: 'climate_agent', 'market_agent', 'feasibility_agent', or 'end'.
    """
    if state.get("next_node") == "__end__":
        return {"next_node": "end"}

    climate_done = "summary" in state.get("climate_data", {})
    market_done = "analysis" in state.get("market_trends", {})
    
    feasibility_report = state.get("feasibility_report", {})
    feasibility_done = False
    if feasibility_report:
        if isinstance(feasibility_report, dict):
            feasibility_done = "report" in feasibility_report or "crop_name" in feasibility_report
        else:
            feasibility_done = hasattr(feasibility_report, "crop_name")
    
    prompt = f"""You are the supervisor agent for a multi-agent system.
Your job is to route to the correct next step.
Current progress state:
- Climate Data analyzed: {climate_done}
- Market Trends analyzed: {market_done}
- Feasibility Report created: {feasibility_done}

Routing rules:
1. If climate data is not yet analyzed, route to 'climate_agent'.
2. If market trends are not yet analyzed, route to 'market_agent'.
3. If feasibility report is not yet created (but climate and market trends are done), route to 'feasibility_agent'.
4. If everything is completed, route to 'end'.

Respond with ONLY the name of the next step: 'climate_agent', 'market_agent', 'feasibility_agent', or 'end'."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a workflow routing manager. Respond ONLY with the requested node name, no other text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    next_step = response.choices[0].message.content.strip().lower()
    # Normalize step names
    if "climate" in next_step:
        next_node = "climate_agent"
    elif "market" in next_step:
        next_node = "market_agent"
    elif "feasibility" in next_step:
        next_node = "feasibility_agent"
    else:
        next_node = "end"
        
    return {"next_node": next_node}
