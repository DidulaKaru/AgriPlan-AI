import os
import json
from openai import OpenAI
from backend.state import AgentState
from backend.database import query_market_trends

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
    climate_data = state.get("climate_data", {})
    market_trends = state.get("market_trends", {})
    
    budget = farmer_data.get("budget") if farmer_data else 0.0
    climate_summary = climate_data.get("summary", "No climate data available.")
    market_analysis = market_trends.get("analysis", "No market trends data available.")
    
    prompt = f"""You are a senior agricultural advisor. Synthesize the following information to produce a feasibility report and crop recommendations.
Farmer Budget: ${budget}
Climate & Soil Suitability: {climate_summary}
Market Trends: {market_analysis}

Return a structured JSON with:
1. "report": A high-level feasibility report text (under 100 words).
2. "recommendations": A list of crop recommendation objects, each containing:
   - "crop_name": name of the crop
   - "estimated_yield": estimated yield description
   - "reasoning": brief explanation why it fits budget/climate/market
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a professional agricultural advisor. You must output valid JSON matching the requested structure."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    
    try:
        report_data = json.loads(response.choices[0].message.content.strip())
    except Exception:
        # Fallback if JSON parsing fails
        report_data = {
            "report": "Failed to parse feasibility report.",
            "recommendations": []
        }
        
    return {"feasibility_report": report_data}

def supervisor_agent(state: AgentState) -> dict:
    """
    Supervisor Agent: Reads the state and determines which node to visit next.
    Options: 'climate_agent', 'market_agent', 'feasibility_agent', or 'end'.
    """
    climate_done = "summary" in state.get("climate_data", {})
    market_done = "analysis" in state.get("market_trends", {})
    feasibility_done = "report" in state.get("feasibility_report", {})
    
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
