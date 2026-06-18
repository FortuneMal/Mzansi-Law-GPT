import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# 1. Load configuration
load_dotenv()

def perform_search(query, collection_name="mzansi_law_popia"):
    """Searches the Qdrant database for the most relevant POPIA sections."""
    
    # Initialize the same embeddings model used during ingestion
    print(f"--- Searching for: '{query}' ---")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url or not qdrant_api_key:
        print("Error: QDRANT_URL or QDRANT_API_KEY not found in .env file.")
        return

    # Connect to the existing Qdrant collection
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    # Perform the search (Retrieve top 3 results)
    results = vector_store.similarity_search(query, k=3)

    if not results:
        print("No matches found in the database.")
    else:
        print(f"\nFound {len(results)} relevant sections:\n")
        for i, doc in enumerate(results, 1):
            print(f"--- Result {i} ---")
            print(f"Source: {doc.metadata.get('act', 'Unknown')} - Section {doc.metadata.get('section', 'Unknown')}")
            print(f"Content Snippet: {doc.page_content[:300]}...")
            print("-" * 30 + "\n")

# --- Interactive Test ---
if __name__ == "__main__":
    print("--- Mzansi Law GPT: Search Test ---")
    
    # You can change this question to test different parts of the data
    user_query = "What rights do I have regarding my personal data?"
    
    perform_search(user_query)
