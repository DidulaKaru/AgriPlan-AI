import os
import json
import time
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

def call_llm_with_retry(func, *args, **kwargs):
    max_retries = 5
    backoff = 2
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                if attempt == max_retries - 1:
                    raise e
                time.sleep(backoff)
                backoff *= 2
            else:
                raise e 

def climate_agent(state: AgentState) -> dict:
    """
    Climate Agent: Analyzes climate and weather viability for the farmer's location.
    """
    farmer_data = state.get("farmer_data")
    if not farmer_data:
        return {"climate_data": {"error": "No farmer data provided."}}
        
    lat = farmer_data.get("lat")
    lon = farmer_data.get("lon")
    soil_npk = farmer_data.get("soil_npk") or {}
    
    # Retrieve relevant crop/NPK requirements context from local ChromaDB
    rag_context = query_market_trends("crop NPK soil requirements agro-ecological compatibility")
    
    prompt = f"""You are an Agricultural Climate and Soil expert. Analyze the climate conditions for a farm located at:
Latitude: {lat}
Longitude: {lon}
Soil NPK values: {soil_npk}

Below are the crop soil and climate requirements from our database:
---
{rag_context}
---

Provide a short summary (under 120 words) analyzing the climate viability and general soil health suitability.
Explicitly state if any of the soil nutrients (N, P, K) are depleted.
"""

    response = call_llm_with_retry(
        client.chat.completions.create,
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a professional agronomist specializing in climate analysis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    analysis = response.choices[0].message.content.strip()
    
    n = soil_npk.get("N", 0) if isinstance(soil_npk, dict) else getattr(soil_npk, "N", 0)
    p = soil_npk.get("P", 0) if isinstance(soil_npk, dict) else getattr(soil_npk, "P", 0)
    k = soil_npk.get("K", 0) if isinstance(soil_npk, dict) else getattr(soil_npk, "K", 0)
    soil_amendment_required = n < 30 or p < 30 or k < 30
    
    return {
        "climate_data": {
            "summary": analysis,
            "soil_amendment_required": soil_amendment_required
        }
    }

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

    response = call_llm_with_retry(
        client.chat.completions.create,
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
        land_area = farmer_data.get("land_area", 0.0)
        machinery = farmer_data.get("machinery", [])
        soil_npk = farmer_data.get("soil_npk") or {}
    elif farmer_data is not None:
        budget = getattr(farmer_data, "budget", 0.0)
        land_area = getattr(farmer_data, "land_area", 0.0)
        machinery = getattr(farmer_data, "machinery", [])
        soil_npk = getattr(farmer_data, "soil_npk", {})
    else:
        budget = 0.0
        land_area = 0.0
        machinery = []
        soil_npk = {}

    n = soil_npk.get("N", 0) if isinstance(soil_npk, dict) else getattr(soil_npk, "N", 0)
    p = soil_npk.get("P", 0) if isinstance(soil_npk, dict) else getattr(soil_npk, "P", 0)
    k = soil_npk.get("K", 0) if isinstance(soil_npk, dict) else getattr(soil_npk, "K", 0)

    climate_data = state.get("climate_data") or {}
    ecological_limits = climate_data.get("summary", "No climate data available.")
    soil_amendment_required = climate_data.get("soil_amendment_required", False)

    market_trends = state.get("market_trends") or {}
    market_context = market_trends.get("analysis", "No market trends data available.")

    system_prompt = (
        "You are a hard-nosed agricultural economist. Evaluate the input text data and choose "
        "the single most viable crop strategy.\n\n"
        "Strict Mathematical Cost Verification:\n"
        "- Convert all database LKR cost metrics to USD using the rate: 1 USD = 300 LKR.\n"
        "- Calculate: Total Cost (USD) = (Crop Cultivation Cost Per Acre in USD) * (Land Area in Acres).\n\n"
        "Hard Budget Rule:\n"
        "- If Total Cost (USD) > Farmer's Available Capital (Budget), you MUST reject open-field farming for that crop.\n\n"
        "Soil & Resource Pivot Rule:\n"
        "- If the crop fails the budget check OR the soil is completely depleted (soil_amendment_required is True, or any of N, P, K is < 30 mg/kg),\n"
        "  evaluate if the farmer has 'Greenhouse Frame' or sufficient capital to pivot to a controlled environment method\n"
        "  (such as Greenhouse or Drip Irrigation System) for high-value micro-crops (like chilies or salad greens) on a fraction of their land area (e.g. 0.1 to 0.25 acres).\n\n"
        "Fertilizer & Amendment Guidelines:\n"
        "- If soil amendments are needed, calculate the approximate fertilizer addition guidelines based on the missing NPK margins (crop requirements vs current soil NPK)\n"
        "  and write it out clearly in 'fertilizer_advice'. If no amendment is required, output 'None'.\n\n"
        "Ensure all output fields in the Pydantic schema (CropRecommendation) are precisely populated, especially 'reasoning', explaining "
        "how the budget, land area, and machinery forced this choice.\n\n"
        "Formatting Constraints for 'reasoning':\n"
        "- DO NOT use raw '$' symbols or wrap variables in equation/LaTeX formats.\n"
        "- Instead of '$150,000', write '150,000 USD'.\n"
        "- Instead of using math layout/equation formats like 'N=3, P=2', write plain text descriptions like 'Nitrogen: 3 mg/kg, Phosphorus: 2 mg/kg'.\n"
        "- This is critical to prevent front-end markdown parsing corruption."
    )

    user_prompt = f"""
Please evaluate the following information and recommend the single best crop strategy:

Farmer's Available Capital (Budget): ${budget}
Land Area: {land_area} acres
Available Machinery/Infrastructure: {", ".join(machinery) if machinery else "none"}

Soil Nutrient Levels: N={n} mg/kg, P={p} mg/kg, K={k} mg/kg
Soil Amendment Required (NPK < 30 mg/kg): {soil_amendment_required}

Ecological & Climate Limits: {ecological_limits}
Market Trends & Pricing Context: {market_context}
"""

    response = call_llm_with_retry(
        client.beta.chat.completions.parse,
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
            farming_method="N/A",
            estimated_yield="N/A",
            total_estimated_cost_usd=0.0,
            soil_amendment_required=False,
            fertilizer_advice="None",
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

    response = call_llm_with_retry(
        client.chat.completions.create,
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
