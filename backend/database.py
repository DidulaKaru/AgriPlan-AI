import os
import chromadb

# Initialize ephemeral ChromaDB client
client = chromadb.EphemeralClient()

# Get or create the collection for market trends
collection = client.get_or_create_collection(name="market_trends")

def initialize_vector_store():
    # 1. Read the market_trends.txt raw text
    with open("data/market_trends.txt", "r") as f:
        raw_data = f.read()
    
    # 2. Split by distinct paragraphs to keep crop records logically unified
    chunks = [chunk.strip() for chunk in raw_data.split("\n\n") if chunk.strip()]
    
    # 3. Add to ChromaDB collection
    # (ChromaDB handles generating the text embeddings behind the scenes via its default model)
    collection.add(
        documents=chunks,
        ids=[f"crop_data_{i}" for i in range(len(chunks))]
    )

def initialize_database():
    """
    Checks for a local file 'data/market_trends.txt'.
    If it doesn't exist, creates it with sample crop market trend paragraphs.
    Chunks, embeds, and stores this data in ChromaDB using paragraph-based chunking.
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
            f.write("\n\n".join(sample_trends))
            
    # Read, chunk, and store using paragraph-based chunking
    initialize_vector_store()

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
