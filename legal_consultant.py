import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from openai import OpenAI

# 1. Configuration and Loading
load_dotenv()

def get_legal_consultant_response(user_query, collection_name="mzansi_law_acts", force_local=False):
    """Consults the legal database and provides a GPT-powered answer."""
    
    # Initialize components
    print(f"\n--- Consulting Mzansi Law Database for: '{user_query}' ---")
    
    # Use the same embeddings as ingestion
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    local_db_path = "qdrant_db"

    if not openai_api_key:
        print("Error: Missing OPENAI_API_KEY in .env file.")
        return

    # Connect to Qdrant (try Cloud first, fallback to local disk)
    client = None
    if not force_local and qdrant_url and qdrant_api_key:
        try:
            print(f"Connecting to Qdrant Cloud cluster ({collection_name})...")
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            # Test connection/collection existence
            if not client.collection_exists(collection_name):
                print(f"[WARNING] Collection '{collection_name}' not found on Qdrant Cloud. Checking local disk...")
                client = None
        except Exception as e:
            print(f"[WARNING] Could not connect to Qdrant Cloud ({e}). Using local disk storage...")
            client = None

    if client is None:
        if not os.path.exists(local_db_path):
            print(f"Error: Local Qdrant database folder '{local_db_path}' not found. Run 'python data_ingestion.py --dir data/raw_acts' first.")
            return
        print(f"Connecting to Local Disk Qdrant database at '{local_db_path}' ({collection_name})...")
        client = QdrantClient(path=local_db_path)

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    # 2. Retrieve Context (Relevant Legal Sections)
    print("Searching for relevant legal sections...")
    results = vector_store.similarity_search(user_query, k=4)

    if not results:
        print("No relevant sections found in the database.")
        return

    # Combine results into context string
    context = "\n\n".join([f"Source: {doc.metadata.get('act')} Section {doc.metadata.get('section')}\nContent: {doc.page_content}" for doc in results])

    # 3. Use GPT-4o to Generate a Detailed Answer
    print("Generating legal assistant response...")
    openai_client = OpenAI(api_key=openai_api_key)
    
    system_prompt = """
    You are 'Mzansi Law GPT', a helpful legal assistant specializing in South African Law.
    Your goal is to provide accurate, concise, and helpful answers based ONLY on the provided legal excerpts.
    
    Instructions:
    1. If the context does not contain the answer, say you don't know and suggest verifying with official sources like SAFLII ('http://www.saflii.org/').
    2. Always cite the Act title and section number you are referring to.
    3. Use a professional but accessible tone suitable for South African citizens and businesses.
    4. Mention that you are an AI assistant and not a substitute for formal professional legal advice.
    """

    user_prompt = f"""
    Context from the South African Legislation:
    {context}
    
    User Question: {user_query}
    
    Please provide a helpful response based strictly on the legislation context above.
    """

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    answer = completion.choices[0].message.content
    
    print("\n" + "="*50)
    print("MZANSI LAW GPT RESPONSE:")
    print("="*50)
    print(answer)
    print("\n" + "="*50)

if __name__ == "__main__":
    test_query = "What rules must a company follow when considering business rescue or if a director has a personal financial interest?"
    get_legal_consultant_response(test_query)
