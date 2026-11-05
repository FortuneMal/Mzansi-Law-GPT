"""Shared retrieval and generation code for the legal chat.

The FastAPI chat endpoints (api_server.py) and the evaluation harness
(evals/run_evals.py) both call these functions, so an evaluation run exercises
exactly the same retrieval, prompt construction and generation as production.

The logic below was moved verbatim from api_server.build_chat_context and the
chat endpoints. Behaviour, prompts and models are intentionally unchanged.
"""
import os
from functools import lru_cache
from typing import Iterator, List, Optional, Tuple

from openai import OpenAI
from pydantic import BaseModel

from contract_review import get_qdrant_vector_store

CHAT_MODEL = "gpt-4o-mini"
CHAT_TEMPERATURE = 0.2
RETRIEVAL_K = 4
DEFAULT_COLLECTION = "mzansi_law_acts_v2"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[ChatMessage]] = []
    act_filter: Optional[str] = "All Acts"
    collection_name: Optional[str] = DEFAULT_COLLECTION
    force_local: Optional[bool] = False


class ChatResponseSource(BaseModel):
    act: str
    section: str
    content: str
    source_file: str


class VectorStoreConnectionError(RuntimeError):
    """Raised when the Qdrant vector store cannot be opened. str() is the original error message."""


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Shared OpenAI client so HTTP connections are reused across requests."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is missing in .env file.")
    return OpenAI(api_key=openai_api_key, timeout=60, max_retries=1)


SYSTEM_PROMPT = """
You are 'Mzansi Law GPT', a state-of-the-art South African AI Legal Advisor & Statutory Consultant.
Your task is to provide accurate, authoritative, structured, and helpful answers grounded STRICTLY in the provided South African legislation context.

Guidelines:
1. Always cite exact Acts and Section numbers when explaining rules or rights.
2. Structure your response with clean formatting (bullet points, bold headings, and clear step-by-step reasoning).
3. If the provided context does not cover the question fully, state clearly what is supported by the context and suggest verifying on SAFLII (http://www.saflii.org/) or consulting a South African labor/commercial attorney.
4. Maintain a professional, accessible, and empathetic South African tone ("Mzansi").
5. Conclude with a brief standard AI legal disclaimer.
"""


def retrieve_sources(req: ChatRequest) -> Tuple[List[ChatResponseSource], str, list]:
    """Retrieves statutory sources and builds the OpenAI messages payload for a chat request.

    Returns (sources, context_str, messages_payload). Raises VectorStoreConnectionError if the
    vector store cannot be opened; any error from the similarity search itself propagates unchanged.
    """
    try:
        vector_store = get_qdrant_vector_store(collection_name=req.collection_name, force_local=req.force_local)
    except Exception as e:
        raise VectorStoreConnectionError(str(e)) from e

    # Apply Act filter if specified
    search_query = req.query
    if req.act_filter and req.act_filter != "All Acts":
        search_query = f"{req.act_filter}: {req.query}"

    results = vector_store.similarity_search(search_query, k=RETRIEVAL_K)
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

    user_prompt = f"""
--- RETRIEVED SOUTH AFRICAN LEGISLATION CONTEXT ---
{context_str}

--- USER QUESTION ---
{req.query}

Please provide a comprehensive, structured response grounded in the statutory excerpts above.
"""

    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Append conversation history
    for msg in req.history:
        messages_payload.append({"role": msg.role, "content": msg.content})

    messages_payload.append({"role": "user", "content": user_prompt})
    return sources, context_str, messages_payload


def generate_answer(messages_payload: list, client: Optional[OpenAI] = None) -> str:
    """Generates the full (non-streaming) answer for a messages payload built by retrieve_sources."""
    openai_client = client or get_openai_client()
    completion = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages_payload,
        temperature=CHAT_TEMPERATURE
    )
    return completion.choices[0].message.content.strip()


def stream_answer(messages_payload: list, client: Optional[OpenAI] = None) -> Iterator[str]:
    """Yields answer text deltas for a messages payload built by retrieve_sources."""
    openai_client = client or get_openai_client()
    stream = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages_payload,
        temperature=CHAT_TEMPERATURE,
        stream=True
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
