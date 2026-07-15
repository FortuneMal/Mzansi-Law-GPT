import os
import re
import argparse
from typing import List, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv
import pypdf
import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from openai import OpenAI

load_dotenv()

# ANSI Color Codes for Terminal Polish
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def load_contract(file_path: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Reads a contract file (.pdf, .docx, .txt) and splits it into logical clauses.
    Returns full_text and a list of clause dictionaries: [{'number': 'Clause 3', 'text': '...'}]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Contract file not found: {file_path}")
        
    print(f"{Colors.CYAN}[INFO] Loading contract from: {file_path}{Colors.ENDC}")
    ext = os.path.splitext(file_path)[1].lower()
    full_text = ""
    
    if ext == ".pdf":
        reader = pypdf.PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt:
                full_text += f"\n--- Page {i+1} ---\n" + txt
    elif ext == ".docx":
        doc = docx.Document(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    else:
        # Default read as TXT
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()
            
    # Clean excessive newlines
    full_text = re.sub(r'\n\s*\n', '\n\n', full_text).strip()
    
    # Split into logical clauses or paragraphs
    # We attempt to detect Clause/Section numbered headers
    clause_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\nClause ", "\nCLAUSE ", "\nSection ", "\nSECTION ", "\nArticle ", "\nARTICLE ", "\n\n", "\n"]
    )
    raw_chunks = clause_splitter.split_text(full_text)
    
    clauses = []
    for i, chunk in enumerate(raw_chunks):
        if not chunk.strip():
            continue
        # Extract clause title or number
        clause_match = re.search(r'^(?:Clause|Section|Article|s)\s*([0-9]+(?:\.[0-9]+)*[A-Za-z]?[:\s-]*[^\n]*)', chunk.strip(), re.IGNORECASE)
        if clause_match:
            title = clause_match.group(0).strip()
        else:
            # Check first line
            first_line = chunk.strip().split('\n')[0]
            if len(first_line) < 60 and any(char.isdigit() for char in first_line[:5]):
                title = first_line.strip()
            else:
                title = f"Clause / Excerpt {i+1}"
                
        clauses.append({
            "id": f"C_{i+1}",
            "title": title[:70],
            "text": chunk.strip()
        })
        
    print(f"{Colors.GREEN}[SUCCESS] Extracted {len(clauses)} clauses/sections from document.{Colors.ENDC}")
    return full_text, clauses

def get_qdrant_vector_store(collection_name="mzansi_law_acts", force_local=False) -> QdrantVectorStore:
    """Connects to Qdrant Cloud or Local Disk vector store."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    local_db_path = "qdrant_db"

    client = None
    if not force_local and qdrant_url and qdrant_api_key:
        try:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=10)
            if not client.collection_exists(collection_name):
                client = None
        except Exception:
            client = None

    if client is None:
        if not os.path.exists(local_db_path):
            raise RuntimeError(f"Local vector database '{local_db_path}' not found. Please run 'python data_ingestion.py --dir data/raw_acts' first.")
        client = QdrantClient(path=local_db_path)

    return QdrantVectorStore(client=client, collection_name=collection_name, embedding=embeddings)

def retrieve_statutory_context(vector_store: QdrantVectorStore, query: str, k: int = 3) -> str:
    """Retrieves top k relevant South African statutory sections from the vector store."""
    results = vector_store.similarity_search(query, k=k)
    if not results:
        return "No specific statutory context retrieved."
    return "\n\n".join([f"[Act: {doc.metadata.get('act')} | Section: {doc.metadata.get('section')}]\n{doc.page_content}" for doc in results])

def audit_contract_domain(domain_name: str, domain_description: str, contract_text: str, vector_store: QdrantVectorStore, openai_client: OpenAI) -> dict:
    """
    Audits the contract specifically for a key compliance domain (e.g. BCEA Working Hours & Leave, POPIA Data Privacy).
    Retrieves statutory grounding and generates a redlined compliance finding.
    """
    print(f"\n{Colors.BLUE}[AUDITING DOMAIN] {domain_name}...{Colors.ENDC}")
    
    # Retrieve statutory context specifically relevant to this domain and contract text
    search_query = f"{domain_name} {domain_description} mandatory rules requirements violations south africa law"
    statutory_context = retrieve_statutory_context(vector_store, search_query, k=4)
    
    system_prompt = """
You are 'Mzansi Law GPT', a Senior South African Statutory Compliance Auditor and Legal Specialist.
Your task is to conduct a rigorous legal review of the provided Contract Excerpts against South African Legislation (specifically BCEA, POPIA, CPA, Companies Act, or LRA depending on the contract type).

Instructions:
1. Examine every clause in the contract text against the retrieved South African statutory context AND your authoritative knowledge of South African law.
2. Identify ANY clause or omission that violates South African law (e.g., working hours over 45 hours/week, overtime pay less than 1.5x, annual leave less than 21 consecutive days/17 worked days, indefinite data retention without consent, unlawful deductions, unfair consumer disclaimers).
3. Output your response EXACTLY in the following structured format (if multiple issues are found in this domain, list them as Finding 1, Finding 2, etc.):

### FINDING STATUS: [COMPLIANT] or [NON-COMPLIANT / VIOLATION] or [RISK / REQUIRES CLARIFICATION]
**Statutory Authority:** [Cite exact Act and Section, e.g., Basic Conditions of Employment Act 75 of 1997, Section 9 & 10]
**Contract Clause / Issue:** [Quote or summarize the exact problematic wording from the contract]
**Legal Compliance Analysis:** [Explain clearly why this violates or complies with South African legislation]
**Recommended Redline Amendment:** [Provide exact replacement wording or clause addition that ensures 100% statutory compliance]
"""

    user_prompt = f"""
--- RETRIEVED SOUTH AFRICAN STATUTORY CONTEXT ---
{statutory_context}

--- CONTRACT TEXT EXCERPTS ---
{contract_text[:12000]}  # Evaluate up to 12k chars for comprehensive coverage

--- AUDIT INSTRUCTION ---
Audit the above contract text specifically focusing on: {domain_name} ({domain_description}).
Identify any unlawful, unfair, or non-compliant terms under South African Law.
If all clauses within this domain are fully compliant with the law, state FINDING STATUS: [COMPLIANT] and explain why.
"""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )
    
    finding_text = response.choices[0].message.content.strip()
    status = "COMPLIANT"
    if "NON-COMPLIANT" in finding_text.upper() or "VIOLATION" in finding_text.upper():
        status = "NON-COMPLIANT"
    elif "RISK" in finding_text.upper() or "REQUIRES CLARIFICATION" in finding_text.upper():
        status = "RISK"
        
    return {
        "domain": domain_name,
        "status": status,
        "analysis": finding_text,
        "statutory_context_used": statutory_context
    }

def run_contract_audit(file_path: str, contract_type: str = "auto", output_report: str = None, force_local: bool = False):
    """Executes the full automated contract compliance audit pipeline."""
    start_time = datetime.now()
    print("=" * 70)
    print(f"{Colors.BOLD}{Colors.HEADER}     MZANSI LAW GPT - AUTOMATED CONTRACT COMPLIANCE AUDITOR     {Colors.ENDC}")
    print("=" * 70)
    
    # 1. Load and parse contract
    full_text, clauses = load_contract(file_path)
    
    # 2. Determine audit domains based on contract type
    if contract_type == "auto":
        upper_text = full_text[:3000].upper()
        if "EMPLOY" in upper_text or "SALARY" in upper_text or "WAGE" in upper_text or "JOB" in upper_text or "LEAVE" in upper_text:
            contract_type = "employment"
        elif "LEASE" in upper_text or "TENANT" in upper_text or "LANDLORD" in upper_text or "RENT" in upper_text:
            contract_type = "lease"
        elif "TERMS AND CONDITIONS" in upper_text or "SERVICE AGREEMENT" in upper_text or "CONSUMER" in upper_text:
            contract_type = "consumer_terms"
        else:
            contract_type = "general"
            
    print(f"{Colors.CYAN}[INFO] Detected Contract Type: {Colors.BOLD}{contract_type.upper()}{Colors.ENDC}")
    
    # Define targeted compliance domains
    domains = []
    if contract_type == "employment":
        domains = [
            ("BCEA Working Hours & Overtime", "Ordinary hours of work (max 45h/week, 9h/day), overtime limits (max 10h/week, 3h/day) and mandatory overtime compensation (at least 1.5x regular wage or time off)."),
            ("BCEA Leave Policies", "Annual leave (minimum 21 consecutive days or 1 day for 17 worked), sick leave (6 weeks paid over 36-month cycle), maternity leave (4 months), and family responsibility leave (3 days)."),
            ("POPIA Employee Data Protection", "Lawful collection, processing, security safeguards, consent, and retention of employee personal information and records."),
            ("LRA Termination & Disciplinary Procedures", "Notice periods for termination, fair procedure, unfair dismissal protections, and dispute resolution via CCMA/Bargaining Council.")
        ]
    elif contract_type == "lease" or contract_type == "consumer_terms":
        domains = [
            ("CPA Consumer Rights & Quality Warranty", "Right to safe, good quality goods/services, implied warranty of quality (6 months repair/replace/refund), and prohibition of unfair/unconscionable terms."),
            ("CPA Cooling-Off & Direct Marketing", "Consumer right to rescind agreements resulting from direct marketing within 5 business days without penalty."),
            ("POPIA Customer Data Processing", "Lawful processing, third-party disclosure, security, and retention of customer personal and financial information."),
            ("Unilateral Penalties & Liability Disclaimers", "Prohibition of excessive cancellation penalties, unilateral rent/fee increases without fair notice, and unfair exclusion of liability for gross negligence.")
        ]
    else:
        domains = [
            ("POPIA Data Protection & Privacy", "Protection, processing, and retention of personal information under POPIA Act 4 of 2013."),
            ("General Statutory Compliance & Fair Terms", "Compliance with basic contractual fairness, Companies Act (if applicable), and avoidance of illegal disclaimers.")
        ]
        
    # 3. Connect to vector store and initialize OpenAI
    vector_store = get_qdrant_vector_store(force_local=force_local)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in .env file.")
    openai_client = OpenAI(api_key=openai_api_key)
    
    # 4. Execute domain audits
    audit_results = []
    violation_count = 0
    for domain_name, desc in domains:
        res = audit_contract_domain(domain_name, desc, full_text, vector_store, openai_client)
        audit_results.append(res)
        if res["status"] == "NON-COMPLIANT":
            violation_count += 1
            
    # 5. Print CLI Executive Summary & Findings
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}EXECUTIVE COMPLIANCE AUDIT SUMMARY{Colors.ENDC}")
    print("=" * 70)
    print(f"Document Name:   {os.path.basename(file_path)}")
    print(f"Contract Type:   {contract_type.upper()}")
    print(f"Clauses Audited: {len(clauses)}")
    print(f"Audit Domains:   {len(domains)}")
    
    if violation_count == 0:
        print(f"Overall Status:  {Colors.GREEN}{Colors.BOLD}PASSED (No critical statutory violations detected){Colors.ENDC}")
    else:
        print(f"Overall Status:  {Colors.FAIL}{Colors.BOLD}FAILED ({violation_count} statutory violation(s) identified){Colors.ENDC}")
    print("-" * 70)
    
    for res in audit_results:
        color = Colors.GREEN if res["status"] == "COMPLIANT" else (Colors.FAIL if res["status"] == "NON-COMPLIANT" else Colors.WARNING)
        print(f"\n{Colors.BOLD}[Domain: {res['domain']}]{Colors.ENDC}")
        print(f"Status: {color}{Colors.BOLD}{res['status']}{Colors.ENDC}")
        print("-" * 50)
        print(res["analysis"])
        
    print("\n" + "=" * 70)
    
    # 6. Save full markdown report if requested or default
    if not output_report:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_report = f"audit_report_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
    os.makedirs("audit_reports", exist_ok=True)
    report_path = os.path.join("audit_reports", os.path.basename(output_report))
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Mzansi Law GPT - Contract Compliance Audit Report\n\n")
        f.write(f"- **Document Audited:** `{os.path.basename(file_path)}`\n")
        f.write(f"- **Contract Type:** `{contract_type.upper()}`\n")
        f.write(f"- **Date of Audit:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")
        f.write(f"- **Overall Findings:** **{violation_count} Critical Violation(s) Identified**\n\n")
        f.write("---\n\n")
        
        for res in audit_results:
            f.write(f"## Domain: {res['domain']} | Status: `{res['status']}`\n\n")
            f.write(f"{res['analysis']}\n\n")
            f.write("---\n\n")
            
        f.write("\n*Disclaimer: This compliance audit report was generated by Mzansi Law GPT, an AI legal assistant grounded in South African legislation. It does not constitute formal professional legal advice. Consult a qualified South African attorney before executing or amending binding agreements.*\n")
        
    print(f"{Colors.GREEN}[SUCCESS] Full Detailed Audit Report saved to: {report_path}{Colors.ENDC}\n")
    return report_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated South African Contract Review & Statutory Compliance Auditor.")
    parser.add_argument("contract_path", type=str, help="Path to the contract file (.pdf, .docx, .txt)")
    parser.add_argument("--type", type=str, default="auto", choices=["auto", "employment", "lease", "consumer_terms", "general"], help="Specify contract type (default: auto-detect)")
    parser.add_argument("--report", type=str, help="Custom filename for the output markdown audit report")
    parser.add_argument("--local", action="store_true", help="Force using local disk vector store ('qdrant_db') instead of Qdrant Cloud")
    
    args = parser.parse_args()
    run_contract_audit(args.contract_path, contract_type=args.type, output_report=args.report, force_local=args.local)
