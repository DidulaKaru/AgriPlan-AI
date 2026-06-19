import os
import chromadb

# Initialize ephemeral ChromaDB client
client = chromadb.EphemeralClient()

# Get or create the collection for market trends
collection = client.get_or_create_collection(name="market_trends")

def initialize_database():
    """
    Checks for a local file 'data/market_trends.txt'.
    If it doesn't exist, creates it with 3 sample lines of crop market trend text.
    Chunks, embeds, and stores this data in ChromaDB.
    """
    data_dir = "data"
    file_path = os.path.join(data_dir, "market_trends.txt")
    
    # Ensure data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # Check and create the file if it does not exist
    if not os.path.exists(file_path):
        sample_trends = [
            "High demand for organic quinoa in urban areas driving prices up by 15% this season.",
            "Drought conditions in major grain belts are expected to reduce soybean supply, increasing market rates.",
            "Government subsidies for smart irrigation systems are boosting productivity for leafy green vegetable farming."
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sample_trends))
            
    # Read, chunk (by line), and store data
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        
    if lines:
        ids = [f"trend_{i}" for i in range(len(lines))]
        collection.add(
            documents=lines,
            ids=ids
        )

def query_market_trends(query: str) -> str:
    """
    Queries ChromaDB and returns the top semantic matches as a single string.
    """
    results = collection.query(
        query_texts=[query],
        n_results=2
    )
    
    documents = results.get("documents", [])
    if documents and len(documents) > 0:
        return "\n".join(documents[0])
    return ""
