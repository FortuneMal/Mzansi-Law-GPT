import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

# Load API keys (.env file needs QDRANT_URL and QDRANT_API_KEY)
load_dotenv()

def generate_popia_sample_data(file_path):
    """Creates a local text file with actual, core sections of POPIA."""
    print("Generating local POPIA legal data...")
    
    popia_text = """
    Protection of Personal Information Act (POPIA) - Core Sections

    Section 5: Rights of data subjects
    A data subject has the right to have his, her or its personal information processed in accordance with the conditions for the lawful processing of personal information, including the right—
    (a) to be notified that personal information about him, her or it is being collected;
    (b) to be notified that his, her or its personal information has been accessed or acquired by an unauthorised person;
    (c) to establish whether a responsible party holds personal information of that data subject and to request access to his, her or its personal information.

    Section 8: Accountability
    The responsible party must ensure that the conditions set out in this Chapter, and all the measures that give effect to such conditions, are complied with at the time of the determination of the purpose and means of the processing and during the processing itself.

    Section 9: Processing limitation
    Personal information must be processed—
    (a) lawfully; and
    (b) in a reasonable manner that does not infringe the privacy of the data subject.

    Section 10: Lawfulness of processing
    Personal information may only be processed if, given the purpose for which it is processed, it is adequate, relevant and not excessive.

    Section 11: Consent, justification and objection
    Personal information may only be processed if—
    (a) the data subject or a competent person where the data subject is a child consents to the processing;
    (b) processing is necessary to carry out actions for the conclusion or performance of a contract to which the data subject is party;
    (c) processing protects a legitimate interest of the data subject;
    (d) processing is necessary for pursuing the legitimate interests of the responsible party or of a third party to whom the information is supplied.

    Section 14: Retention and restriction of records
    Records of personal information must not be retained any longer than is necessary for achieving the purpose for which the information was collected or subsequently processed, unless—
    (a) retention of the record is required or authorised by law;
    (b) the responsible party reasonably requires the record for lawful purposes related to its functions or activities.

    Section 19: Security measures on integrity and confidentiality of personal information
    A responsible party must secure the integrity and confidentiality of personal information in its possession or under its control by taking appropriate, reasonable technical and organisational measures to prevent—
    (a) loss of, damage to or unauthorised destruction of personal information; and
    (b) unlawful access to or processing of personal information.
    """
    
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(popia_text)
    
    print(f"Successfully created {file_path}")

def load_and_chunk_text(file_path):
    """Reads the generated text file and chunks it for the database."""
    print("Reading and chunking data...")
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
        
    sections = text.split("\n    Section ")
    legal_documents = []
    
    for i, section_text in enumerate(sections):
        if i == 0: continue 
        
        full_text = "Section " + section_text.strip()
        section_num = full_text.split(":")[0].replace("Section ", "").strip()
        
        legal_documents.append(
            Document(
                page_content=full_text,
                metadata={
                    "act": "POPIA",
                    "section": section_num,
                    "source": "Local MVP Data"
                }
            )
        )
        
    print(f"Created {len(legal_documents)} documents ready for vectorization.")
    return legal_documents

def embed_and_upload_to_qdrant(documents, collection_name="mzansi_law_popia"):
    """Generates local embeddings and uploads documents to Qdrant."""
    
    # 100% FREE LOCAL EMBEDDINGS
    print("Initializing HuggingFace Embeddings (all-MiniLM-L6-v2)...")
    print("(Note: This may take a minute to download the model the very first time you run it)")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url or not qdrant_api_key:
        print("Uploading to local in-memory Qdrant...")
        QdrantVectorStore.from_documents(documents, embeddings, location=":memory:", collection_name=collection_name)
    else:
        print(f"Uploading to Qdrant Cloud cluster: {collection_name}...")
        QdrantVectorStore.from_documents(documents, embeddings, url=qdrant_url, api_key=qdrant_api_key, collection_name=collection_name)
        
    print("Upload complete! Vector database is populated.")

# --- Execution ---
if __name__ == "__main__":
    LOCAL_TEXT_FILE = "popia_core.txt"
    
    print("--- Starting Mzansi Law GPT Data Pipeline ---")
    generate_popia_sample_data(LOCAL_TEXT_FILE)
    final_documents = load_and_chunk_text(LOCAL_TEXT_FILE)
    embed_and_upload_to_qdrant(final_documents)
    print("--- Pipeline Execution Finished ---")