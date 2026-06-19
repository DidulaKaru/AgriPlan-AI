# AgriPlan AI

AgriPlan AI is an intelligent, multi-agent agricultural planning and crop recommendation system. It leverages a LangGraph orchestration workflow, local RAG retrieval via ChromaDB, a FastAPI backend, and a premium Streamlit frontend interface to provide customized, data-driven farming insights.

---

## 🏗️ System Architecture

The system utilizes a multi-agent supervisor pattern to sequence research tasks before summarizing final feasibility.

```mermaid
graph TD
    UI[Streamlit Frontend] <-->|POST /recommend| API[FastAPI Backend]
    API <-->|invoke| Graph[LangGraph Workflow]
    
    subgraph Agents [LangGraph Orchestration]
        Supervisor{Supervisor Agent}
        Climate[Climate Agent]
        Market[Market Agent]
        Feasibility[Feasibility Agent]
    end
    
    Graph --> Supervisor
    Supervisor -->|routes| Climate
    Supervisor -->|routes| Market
    Supervisor -->|routes| Feasibility
    
    Climate -->|updates climate_data| Supervisor
    Market -->|updates market_trends| Supervisor
    Feasibility -->|updates feasibility_report| Supervisor
    
    Market <-->|Semantic Query| RAG[ChromaDB Local Vector DB]
```

### Agents Workflows:
1. **Supervisor Agent**: Monitors the `AgentState`. Programmatically and agentically decides which task to run next based on what data is missing, routing back to `__end__` once all workers finish.
2. **Climate Agent**: Analyzes farm geolocation (latitude, longitude) and soil N-P-K composition to evaluate weather suitability and general soil health.
3. **Market Agent**: Integrates local ChromaDB retrieval to search for real-time market trends and demand fluctuations of target crops.
4. **Feasibility Agent**: Synthesizes the climate reports, market insights, and the farmer's budget limits to output final JSON-structured crop recommendations.

---

## 📂 Project Structure

```text
agriplan-ai/
├── backend/
│   ├── main.py          # FastAPI endpoints & Lifespan setup
│   ├── state.py         # LangGraph shared state (AgentState)
│   ├── agents.py        # OpenAI SDK agent worker & supervisor definitions
│   ├── graph.py         # LangGraph StateGraph routing & compilation
│   ├── database.py      # ChromaDB EphemeralClient setup & RAG loading
│   └── schemas.py       # Pydantic schemas (FarmerInput, CropRecommendation)
├── frontend/
│   └── app.py           # Streamlit UI
├── data/
│   └── market_trends.txt# Seed data for vector store RAG
├── requirements.txt     # Project dependencies
└── README.md            # System documentation
```

---

## 🚀 Setup & Execution

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Configure Environment
Set your OpenAI API key in your terminal/environment:
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# Linux/macOS
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Run the Backend API
Start the FastAPI server (running on `http://localhost:8000` by default):
```bash
python -m uvicorn backend.main:app --reload
```

### 5. Run the Streamlit Dashboard
Launch the frontend application:
```bash
python -m streamlit run frontend/app.py
```
Open `http://localhost:8501` in your browser to interact with the application.
