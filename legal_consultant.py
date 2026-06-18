import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from openai import OpenAI

# 1. Configuration and Loading
load_dotenv()

def get_legal_consultant_response(user_query, collection_name="mzansi_law_popia"):
    """Consults the legal database and provides a GPT-powered answer."""
    
    # Initialize components
    print(f"\n--- Consulting Mzansi Law Database for: '{user_query}' ---")
    
    # Use the same embeddings as ingestion
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not all([qdrant_url, qdrant_api_key, openai_api_key]):
        print("Error: Missing credentials (QDRANT or OPENAI_API_KEY) in .env file.")
        return

    # Connect to Qdrant
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    # 2. Retrieve Context (Relevant Legal Sections)
    print("Searching for relevant legal sections...")
    results = vector_store.similarity_search(user_query, k=3)

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
    1. If the context does not contain the answer, say you don't know and suggest visiting 'https://laws.africa/'.
    2. Always cite the section number you are referring to.
    3. Use a professional but accessible tone.
    4. Mention that you are an AI and not a substitute for professional legal advice.
    """

    user_prompt = f"""
    Context from the South African Legislation:
    {context}
    
    User Question: {user_query}
    
    Please provide a helpful response.
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
    test_query = "What rights do I have when my personal data is being collected?"
    get_legal_consultant_response(test_query)
