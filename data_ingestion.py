import os
import re
import argparse
import requests
from bs4 import BeautifulSoup
import pypdf
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

def load_and_chunk_text(file_path, act_name=None):
    """Reads a text file (generated or downloaded Act) and chunks it flexibly for the vector database."""
    print(f"Reading and chunking TXT data: {file_path}...")
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
        
    # Check if this is the exact original popia_core.txt with "\n    Section " splitting
    if "\n    Section " in text and not act_name:
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

    # Dynamic parsing for all downloaded/scraped text Acts
    # Extract title if present at the start or from act_name / filename
    extracted_title = act_name
    if not extracted_title:
        title_match = re.search(r'^TITLE:\s*(.+)$', text, re.MULTILINE)
        if title_match:
            extracted_title = title_match.group(1).strip()
        else:
            first_line = text.strip().split("\n")[0]
            if len(first_line) < 120 and ("ACT" in first_line.upper() or "POPIA" in first_line.upper() or "BCEA" in first_line.upper() or "CONSTITUTION" in first_line.upper()):
                extracted_title = first_line.strip()
            else:
                extracted_title = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ").title()

    # Split into sections or chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\nSection ", "\n    Section ", "\nCHAPTER ", "\nChapter ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_text(text)
    
    legal_documents = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        # Extract section number if present
        section_match = re.search(r'(?:Section|s)\s*([0-9]+[A-Za-z]?)', chunk, re.IGNORECASE)
        section_num = section_match.group(1) if section_match else f"Chunk_{i+1}"
        
        legal_documents.append(
            Document(
                page_content=chunk.strip(),
                metadata={
                    "act": extracted_title,
                    "section": section_num,
                    "source": os.path.basename(file_path),
                    "type": "txt_legislation"
                }
            )
        )
        
    print(f"Created {len(legal_documents)} documents from TXT file ready for vectorization.")
    return legal_documents

def load_and_chunk_pdf(file_path, act_name=None):
    """Reads a PDF legal document (Act/Regulation) and chunks it."""
    print(f"Reading and chunking PDF file: {file_path}...")
    reader = pypdf.PdfReader(file_path)
    full_text = ""
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            full_text += f"\n--- Page {page_num + 1} ---\n" + page_text

    act_title = act_name or os.path.splitext(os.path.basename(file_path))[0].replace("_", " ")
    
    # Try splitting by section headers or use recursive character splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\nSection ", "\nCHAPTER ", "\nPart ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_text(full_text)
    
    legal_documents = []
    for i, chunk in enumerate(chunks):
        # Extract section number if present
        section_match = re.search(r'(?:Section|s)\s*([0-9]+[A-Za-z]?)', chunk, re.IGNORECASE)
        section_num = section_match.group(1) if section_match else f"Chunk_{i+1}"
        
        legal_documents.append(
            Document(
                page_content=chunk.strip(),
                metadata={
                    "act": act_title,
                    "section": section_num,
                    "source": os.path.basename(file_path),
                    "type": "pdf_legislation"
                }
            )
        )
        
    print(f"Created {len(legal_documents)} documents from PDF ready for vectorization.")
    return legal_documents

def scrape_and_chunk_saflii(url, act_name=None):
    """Scrapes South African legislation or case law directly from SAFLII (www.saflii.org) and chunks it."""
    print(f"Scraping legal document from SAFLII: {url}...")
    headers = {
        "User-Agent": "Mzansi-Law-GPT Open-Source Legal RAG Assistant (Public Interest / Educational)"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Remove unwanted navigation/scripts/styles
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()
        
    # Attempt to get the main content area or body
    content_area = soup.find("div", class_="content") or soup.find("body") or soup
    raw_text = content_area.get_text(separator="\n")
    
    # Clean up excessive newlines and whitespace
    clean_text = re.sub(r'\n\s*\n', '\n\n', raw_text).strip()
    
    # Try to extract the title if act_name not provided
    if not act_name:
        title_elem = soup.find("h1") or soup.find("title")
        act_name = title_elem.get_text().strip() if title_elem else "SAFLII Scraped Document"
        
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\nSection ", "\nCHAPTER ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_text(clean_text)
    
    legal_documents = []
    for i, chunk in enumerate(chunks):
        section_match = re.search(r'(?:Section|s)\s*([0-9]+[A-Za-z]?)', chunk, re.IGNORECASE)
        section_num = section_match.group(1) if section_match else f"Chunk_{i+1}"
        
        legal_documents.append(
            Document(
                page_content=chunk.strip(),
                metadata={
                    "act": act_name,
                    "section": section_num,
                    "source": url,
                    "type": "saflii_web"
                }
            )
        )
        
    print(f"Created {len(legal_documents)} documents from SAFLII ready for vectorization.")
    return legal_documents

def ingest_local_directory(directory_path="data/raw_acts", collection_name="mzansi_law_acts", force_local=False):
    """Ingests all PDF, TXT, and HTML legal files from a local directory into Qdrant."""
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist yet. Creating it...")
        os.makedirs(directory_path, exist_ok=True)
        print(f"Please place your PDF or TXT legal files in '{directory_path}' and run again.")
        return []
        
    all_documents = []
    files = os.listdir(directory_path)
    print(f"Found {len(files)} files in {directory_path}...")
    
    for file_name in files:
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path):
            if file_name.lower().endswith(".pdf"):
                docs = load_and_chunk_pdf(file_path)
                all_documents.extend(docs)
            elif file_name.lower().endswith(".txt"):
                docs = load_and_chunk_text(file_path)
                all_documents.extend(docs)
                
    if all_documents:
        embed_and_upload_to_qdrant(all_documents, collection_name=collection_name, force_local=force_local)
    else:
        print("No documents found or processed from directory.")
    return all_documents

def embed_and_upload_to_qdrant(documents, collection_name="mzansi_law_popia", force_local=False):
    """Generates local embeddings and uploads documents to Qdrant (Cloud or Local Disk)."""
    if not documents:
        print("No documents provided to vectorize.")
        return

    # 100% FREE LOCAL EMBEDDINGS
    print("Initializing HuggingFace Embeddings (all-MiniLM-L6-v2)...")
    print("(Note: This may take a minute to download the model the very first time you run it)")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    local_db_path = "qdrant_db"

    if force_local or not qdrant_url or not qdrant_api_key:
        print(f"Saving vector database to local disk path '{local_db_path}' (collection: {collection_name})...")
        QdrantVectorStore.from_documents(documents, embeddings, path=local_db_path, collection_name=collection_name)
    else:
        print(f"Uploading to Qdrant Cloud cluster: {collection_name}...")
        try:
            QdrantVectorStore.from_documents(documents, embeddings, url=qdrant_url, api_key=qdrant_api_key, collection_name=collection_name)
            print("Successfully uploaded to Qdrant Cloud!")
        except Exception as e:
            print(f"[WARNING] Could not connect to Qdrant Cloud ({e}). Falling back to local disk storage...")
            print(f"Saving vector database to local disk path '{local_db_path}' (collection: {collection_name})...")
            QdrantVectorStore.from_documents(documents, embeddings, path=local_db_path, collection_name=collection_name)
            
    print("Upload complete! Vector database is populated.")

# --- Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mzansi Law GPT Data Ingestion Pipeline")
    parser.add_argument("--saflii", type=str, help="Scrape and ingest an Act directly from a SAFLII URL")
    parser.add_argument("--pdf", type=str, help="Ingest a specific PDF legal file")
    parser.add_argument("--dir", type=str, help="Ingest all PDF/TXT files from a directory (default: data/raw_acts)")
    parser.add_argument("--act-name", type=str, help="Optional custom name for the Act being ingested")
    parser.add_argument("--collection", type=str, default="mzansi_law_acts", help="Target Qdrant collection name")
    parser.add_argument("--local", action="store_true", help="Force saving vector store to local disk path ('qdrant_db') instead of Qdrant Cloud")
    
    args = parser.parse_args()
    
    print("--- Starting Mzansi Law GPT Data Pipeline ---")
    
    if args.saflii:
        docs = scrape_and_chunk_saflii(args.saflii, act_name=args.act_name)
        embed_and_upload_to_qdrant(docs, collection_name=args.collection, force_local=args.local)
    elif args.pdf:
        docs = load_and_chunk_pdf(args.pdf, act_name=args.act_name)
        embed_and_upload_to_qdrant(docs, collection_name=args.collection, force_local=args.local)
    elif args.dir:
        ingest_local_directory(args.dir, collection_name=args.collection, force_local=args.local)
    else:
        # Default behavior: run POPIA MVP pipeline
        LOCAL_TEXT_FILE = "popia_core.txt"
        generate_popia_sample_data(LOCAL_TEXT_FILE)
        final_documents = load_and_chunk_text(LOCAL_TEXT_FILE)
        embed_and_upload_to_qdrant(final_documents, collection_name="mzansi_law_popia", force_local=args.local)
        
    print("--- Pipeline Execution Finished ---")