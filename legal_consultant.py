import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from openai import OpenAI

# 1. Configuration and Loading
load_dotenv()

def get_legal_consultant_response(user_query, chat_history=None, collection_name="mzansi_law_acts", force_local=False):
    """Consults the legal database and provides a GPT-powered answer using conversational memory."""
    
    if chat_history is None:
        chat_history = []
        
    # Use the same embeddings as ingestion
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    local_db_path = "qdrant_db"

    if not openai_api_key:
        print("Error: Missing OPENAI_API_KEY in .env file.")
        return None

    # Connect to Qdrant (try Cloud first, fallback to local disk)
    client = None
    if not force_local and qdrant_url and qdrant_api_key:
        try:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=5)
            if not client.collection_exists(collection_name):
                client = None
        except Exception:
            client = None

    if client is None:
        if not os.path.exists(local_db_path):
            print(f"Error: Local Qdrant database folder '{local_db_path}' not found.")
            return None
        client = QdrantClient(path=local_db_path)

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    # 2. Retrieve Context (Relevant Legal Sections)
    results = vector_store.similarity_search(user_query, k=4)
    context = "\n\n".join([f"Source: {doc.metadata.get('act')} Section {doc.metadata.get('section')}\nContent: {doc.page_content}" for doc in results]) if results else "No specific context found."

    # 3. Use GPT-4o-mini to Generate a Detailed Answer
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

    messages_payload = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages_payload.append(msg)
    messages_payload.append({"role": "user", "content": user_prompt})

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_payload,
        temperature=0.2
    )

    answer = completion.choices[0].message.content
    
    # Update chat history in place (keep it brief)
    chat_history.append({"role": "user", "content": user_query})
    chat_history.append({"role": "assistant", "content": answer})
    
    return answer

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" MZANSI LAW GPT - INTERACTIVE LEGAL CONSULTANT ".center(70, "="))
    print("="*70)
    print("Type your legal questions below. Type 'exit' or 'quit' to end the session.")
    print("-" * 70)
    
    history = []
    while True:
        try:
            query = input("\nUser > ")
            if query.lower() in ["exit", "quit", "q"]:
                break
            if not query.strip():
                continue
                
            print("\nConsulting laws...")
            response = get_legal_consultant_response(query, chat_history=history)
            
            if response:
                print("\n" + "="*50)
                print("MZANSI LAW GPT:")
                print("="*50)
                print(response)
                print("="*50)
        except KeyboardInterrupt:
            break
            
    print("\nSession ended. Stay compliant!")
