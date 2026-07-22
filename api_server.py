import os
import shutil
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# Import internal modules
from download_core_acts import CORE_ACTS
from contract_review import load_contract, get_qdrant_vector_store, audit_contract_domain

load_dotenv()

app = FastAPI(
    title="Mzansi Law GPT API",
    description="State-of-the-Art South African Legal AI & Contract Compliance Auditor REST Server",
    version="2.0.0"
)

# Enable CORS for Next.js frontend (port 3000 or any)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    act_filter: Optional[str] = "All Acts"
    collection_name: Optional[str] = "mzansi_law_acts"
    force_local: Optional[bool] = False

class ChatResponseSource(BaseModel):
    act: str
    section: str
    content: str
    source_file: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatResponseSource]
    timestamp: str

class AuditFinding(BaseModel):
    domain: str
    status: str  # COMPLIANT, NON-COMPLIANT, RISK
    analysis: dict
    statutory_context_used: str

class AuditResponse(BaseModel):
    document_name: str
    contract_type: str
    overall_status: str
    violation_count: int
    findings: List[AuditFinding]
    report_url: Optional[str] = None
    timestamp: str

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "Mzansi-Law-GPT API Server",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/acts")
def get_available_acts():
    """Returns the list of core South African Acts loaded in the system."""
    acts_list = []
    for key, info in CORE_ACTS.items():
        acts_list.append({
            "key": key,
            "title": info["title"],
            "filename": info["filename"],
            "url": info["url"]
        })
    return {"total_acts": len(acts_list), "acts": acts_list}

@app.post("/api/chat", response_model=ChatResponse)
def chat_with_legal_consultant(req: ChatRequest):
    """Interactive multi-turn/single-turn chat endpoint with statutory source citations."""
    try:
        vector_store = get_qdrant_vector_store(collection_name=req.collection_name, force_local=req.force_local)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Qdrant Vector Store: {str(e)}")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is missing in .env file.")

    # Apply Act filter if specified
    search_query = req.query
    if req.act_filter and req.act_filter != "All Acts":
        search_query = f"{req.act_filter}: {req.query}"

    results = vector_store.similarity_search(search_query, k=4)
    sources = []
    context_blocks = []
    
    for doc in results:
        act_title = doc.metadata.get("act", "South African Legislation")
        section_num = doc.metadata.get("section", "N/A")
        src_file = doc.metadata.get("source", "N/A")
        
        # Filter strictly if act_filter is chosen
        if req.act_filter and req.act_filter != "All Acts" and req.act_filter.lower() not in act_title.lower():
            continue
            
        sources.append(ChatResponseSource(
            act=act_title,
            section=str(section_num),
            content=doc.page_content.strip(),
            source_file=src_file
        ))
        context_blocks.append(f"Source: {act_title} (Section {section_num})\nContent:\n{doc.page_content}")

    if not sources and results:
        # If filtering excluded all, fallback to all results
        for doc in results:
            act_title = doc.metadata.get("act", "South African Legislation")
            section_num = doc.metadata.get("section", "N/A")
            src_file = doc.metadata.get("source", "N/A")
            sources.append(ChatResponseSource(
                act=act_title,
                section=str(section_num),
                content=doc.page_content.strip(),
                source_file=src_file
            ))
            context_blocks.append(f"Source: {act_title} (Section {section_num})\nContent:\n{doc.page_content}")

    context_str = "\n\n---\n\n".join(context_blocks) if context_blocks else "No relevant statutory sections found in the current vector store."

    system_prompt = """
You are 'Mzansi Law GPT', a state-of-the-art South African AI Legal Advisor & Statutory Consultant.
Your task is to provide accurate, authoritative, structured, and helpful answers grounded STRICTLY in the provided South African legislation context.

Guidelines:
1. Always cite exact Acts and Section numbers when explaining rules or rights.
2. Structure your response with clean formatting (bullet points, bold headings, and clear step-by-step reasoning).
3. If the provided context does not cover the question fully, state clearly what is supported by the context and suggest verifying on SAFLII (http://www.saflii.org/) or consulting a South African labor/commercial attorney.
4. Maintain a professional, accessible, and empathetic South African tone ("Mzansi").
5. Conclude with a brief standard AI legal disclaimer.
"""

    user_prompt = f"""
--- RETRIEVED SOUTH AFRICAN LEGISLATION CONTEXT ---
{context_str}

--- USER QUESTION ---
{req.query}

Please provide a comprehensive, structured response grounded in the statutory excerpts above.
"""

    openai_client = OpenAI(api_key=openai_api_key)
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )

    answer = completion.choices[0].message.content.strip()
    return ChatResponse(
        answer=answer,
        sources=sources,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/audit", response_model=AuditResponse)
async def audit_contract_endpoint(
    file: UploadFile = File(...),
    contract_type: str = Form("auto"),
    force_local: bool = Form(False)
):
    """Endpoint to upload a contract file (.pdf, .docx, .txt) and perform automated statutory compliance auditing."""
    upload_dir = os.path.join("data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())[:8]
    file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        full_text, clauses = load_contract(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded document: {str(e)}")

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

    domains = []
    if contract_type == "employment":
        domains = [
            ("BCEA Working Hours & Overtime", "Ordinary hours of work (max 45h/week, 9h/day), overtime limits (max 10h/week, 3h/day) and mandatory overtime compensation (at least 1.5x regular wage or time off)."),
            ("BCEA Leave Policies", "Annual leave (minimum 21 consecutive days or 1 day for 17 worked), sick leave (6 weeks paid over 36-month cycle), maternity leave (4 months), and family responsibility leave (3 days)."),
            ("POPIA Employee Data Protection", "Lawful collection, processing, security safeguards, consent, and retention of employee personal information and records."),
            ("LRA Termination & Disciplinary Procedures", "Notice periods for termination, fair procedure, unfair dismissal protections, and dispute resolution via CCMA/Bargaining Council.")
        ]
    elif contract_type in ["lease", "consumer_terms"]:
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

    try:
        vector_store = get_qdrant_vector_store(force_local=force_local)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Vector store connection failure: {str(e)}")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing in .env")
    openai_client = OpenAI(api_key=openai_api_key)

    findings = []
    violation_count = 0
    for domain_name, desc in domains:
        res = audit_contract_domain(domain_name, desc, full_text, vector_store, openai_client)
        findings.append(AuditFinding(
            domain=res["domain"],
            status=res["status"],
            analysis=res["analysis"],
            statutory_context_used=res["statutory_context_used"]
        ))
        if res["status"] == "NON-COMPLIANT":
            violation_count += 1

    overall_status = "PASSED" if violation_count == 0 else "FAILED"
    
    # Save markdown report
    os.makedirs("audit_reports", exist_ok=True)
    report_filename = f"audit_{file_id}_{contract_type}.md"
    report_path = os.path.join("audit_reports", report_filename)
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write(f"# Mzansi Law GPT - Contract Compliance Audit Report\n\n")
        rf.write(f"- **Document Audited:** `{file.filename}`\n")
        rf.write(f"- **Contract Type:** `{contract_type.upper()}`\n")
        rf.write(f"- **Overall Findings:** **{violation_count} Critical Statutory Violation(s)**\n\n---\n\n")
        for fnd in findings:
            rf.write(f"## Domain: {fnd.domain} | Status: `{fnd.status}`\n\n")
            if isinstance(fnd.analysis, dict) and "error" not in fnd.analysis:
                rf.write(f"**Statutory Authority:** {fnd.analysis.get('statutory_authority', 'N/A')}\n\n")
                rf.write(f"**Contract Clause:** {fnd.analysis.get('contract_clause', 'N/A')}\n\n")
                rf.write(f"**Legal Analysis:** {fnd.analysis.get('legal_analysis', 'N/A')}\n\n")
                rf.write(f"**Citizen Explanation:** {fnd.analysis.get('citizen_explanation', 'N/A')}\n\n")
                rf.write(f"**Recommended Redline:** {fnd.analysis.get('recommended_redline', 'N/A')}\n\n")
            else:
                rf.write(f"{fnd.analysis}\n\n")
            rf.write("---\n\n")

    if os.path.exists(file_path):
        os.remove(file_path)

    return AuditResponse(
        document_name=file.filename,
        contract_type=contract_type.upper(),
        overall_status=overall_status,
        violation_count=violation_count,
        findings=findings,
        report_url=f"/audit_reports/{report_filename}",
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    print("Starting Mzansi Law GPT API Server on http://0.0.0.0:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
