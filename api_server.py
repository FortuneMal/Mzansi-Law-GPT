import os
import json
import shutil
import time
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# Import internal modules
from download_core_acts import CORE_ACTS
from contract_review import load_contract, get_qdrant_vector_store, audit_contract_domain
from rag_core import (
    CHAT_MODEL,
    ChatMessage,
    ChatRequest,
    ChatResponseSource,
    VectorStoreConnectionError,
    generate_answer,
    get_openai_client,
    retrieve_sources,
    stream_answer,
)
from query_log import log_rag_event, logging_enabled

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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChatMessage, ChatRequest and ChatResponseSource live in rag_core so the eval harness shares them.

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

@app.on_event("startup")
def warm_up_clients():
    """Connect to Qdrant and OpenAI at boot so the first chat request doesn't pay the setup cost."""
    try:
        get_openai_client()
        # Must match the call in rag_core.retrieve_sources exactly, or lru_cache treats it as a different key
        default_req = ChatRequest(query="")
        get_qdrant_vector_store(collection_name=default_req.collection_name, force_local=default_req.force_local)
    except Exception as e:
        print(f"[WARN] Warm-up failed (will retry on first request): {e}")

def build_chat_context(req: ChatRequest):
    """Retrieves statutory sources via rag_core and maps vector store failures to HTTP 500.
    Returns (sources, context_str, messages_payload)."""
    try:
        return retrieve_sources(req)
    except VectorStoreConnectionError as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Qdrant Vector Store: {str(e)}")

def _get_openai_client_or_500() -> OpenAI:
    try:
        return get_openai_client()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

def _error_text(e: Exception) -> str:
    detail = getattr(e, "detail", None)
    return f"{type(e).__name__}: {detail if detail is not None else e}"

def _log_chat(endpoint: str, req: ChatRequest, sources, answer, started: float, error: Optional[str]) -> None:
    """Builds the query-log event for a chat request. No-op unless MZANSI_LOG_QUERIES=1; never raises."""
    if not logging_enabled():
        return
    try:
        log_rag_event({
            "timestamp": datetime.now().astimezone().isoformat(),
            "endpoint": endpoint,
            "query": req.query,
            "act_filter": req.act_filter,
            "collection": req.collection_name,
            "sources": [{"act": s.act, "section": s.section} for s in sources],
            "answer": answer,
            "model": CHAT_MODEL,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "error": error,
        })
    except Exception:
        pass

@app.post("/api/chat", response_model=ChatResponse)
def chat_with_legal_consultant(req: ChatRequest):
    """Interactive multi-turn/single-turn chat endpoint with statutory source citations."""
    started = time.perf_counter()
    sources, answer, error = [], None, None
    try:
        openai_client = _get_openai_client_or_500()
        sources, _context, messages_payload = build_chat_context(req)
        answer = generate_answer(messages_payload, openai_client)
    except Exception as e:
        error = _error_text(e)
        raise
    finally:
        _log_chat("/api/chat", req, sources, answer, started, error)

    return ChatResponse(
        answer=answer,
        sources=sources,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/chat/stream")
def chat_with_legal_consultant_stream(req: ChatRequest):
    """Streaming chat endpoint. Emits newline-delimited JSON events:
    {"type": "sources", ...}, then {"type": "delta", "content": ...} per token, then {"type": "done"} or {"type": "error"}.
    """
    started = time.perf_counter()
    try:
        openai_client = _get_openai_client_or_500()
        sources, _context, messages_payload = build_chat_context(req)
    except Exception as e:
        _log_chat("/api/chat/stream", req, [], None, started, _error_text(e))
        raise

    def event_stream():
        parts = []
        error = None
        completed = False
        try:
            yield json.dumps({
                "type": "sources",
                "sources": [s.model_dump() for s in sources],
                "timestamp": datetime.now().isoformat()
            }) + "\n"
            try:
                for delta in stream_answer(messages_payload, openai_client):
                    parts.append(delta)
                    yield json.dumps({"type": "delta", "content": delta}) + "\n"
                completed = True
                yield json.dumps({"type": "done"}) + "\n"
            except Exception as e:
                error = str(e)
                yield json.dumps({"type": "error", "detail": str(e)}) + "\n"
        finally:
            # Logged exactly once: after "done", after "error", or when the client disconnects mid-stream
            if not completed and error is None:
                error = "stream closed by client before completion"
            _log_chat("/api/chat/stream", req, sources, "".join(parts), started, error)

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        # Stop proxies (e.g. Render) from buffering the stream
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
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

    try:
        openai_client = get_openai_client()
    except RuntimeError as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

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
