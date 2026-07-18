# 🏛️🇿🇦 Mzansi-Law-GPT

Mzansi-Law-GPT is a state-of-the-art South African Legal AI Assistant and automated Contract Compliance Auditor. Built for the modern legal professional and everyday citizens, it leverages Large Language Models (LLMs) and a robust Retrieval-Augmented Generation (RAG) architecture to provide authoritative, statutory-grounded legal guidance and automated contract reviews.

## ✨ Key Features

- **🗣️ AI Legal Consultant (Chat)**: Engage in a rich, interactive chat interface to ask complex legal questions. Every answer is grounded in actual South African statutes with exact Act and Section citations provided via source drawers.
- **📄 Contract Auditor**: Upload employment contracts, lease agreements, or consumer terms and conditions (`.pdf`, `.docx`, `.txt`). The AI will automatically scan the document against South African laws (BCEA, POPIA, CPA, etc.) and flag illegal, non-compliant, or risky clauses, generating a detailed Markdown report.
- **📚 Rich Legislation Library**: Pre-loaded with 17 Core South African Statutes, Regulations, and Landmark Case Law judgments—including the Constitution, POPIA, Labour Relations Act, Basic Conditions of Employment Act, Companies Act, and CCMA rules.
- **☁️ Cloud Vector Storage**: Uses Qdrant Vector Store to seamlessly chunk, embed, and retrieve dense legal texts for ultra-fast and accurate semantic search.
- **💎 Premium Glassmorphic UI**: A visually stunning Next.js interactive dashboard featuring modern transitions, dark-mode aesthetics, and intuitive navigation.

## 🛠️ Technology Stack

- **Frontend**: [Next.js 16](https://nextjs.org/) (React), TailwindCSS, Framer Motion, Lucide Icons.
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python) for robust, async REST API handling.
- **AI & RAG**: [LangChain](https://python.langchain.com/), OpenAI API (`gpt-4o-mini`), HuggingFace Embeddings (`all-MiniLM-L6-v2`).
- **Vector Database**: [Qdrant](https://qdrant.tech/) Cloud (sa-east-1) for scalable similarity search.
- **Data Pipeline**: Custom web scraper hitting [SAFLII](http://www.saflii.org/) to download, clean, and chunk raw legislation.

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- Qdrant Cloud Account (Free Tier)
- OpenAI API Key

### 1. Backend Setup (FastAPI & Vector DB)
Navigate to the root directory and set up your Python environment:
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key
```

### 2. Data Ingestion (Populating the Vector Store)
Download the 17 core acts and landmark case laws from SAFLII, then embed them into Qdrant:
```bash
# Download all core statutes to data/raw_acts
python download_core_acts.py --all

# Embed the files into your Qdrant Vector DB
python data_ingestion.py --dir data/raw_acts
```

### 3. Start the Backend Server
```bash
python api_server.py
```
*The FastAPI server will start on `http://localhost:8000`.*

### 4. Frontend Setup (Next.js Dashboard)
Open a new terminal window and navigate to the dashboard directory:
```bash
cd dashboard
npm install
npm run dev
```
*The web app will be available at `http://localhost:3000`.*

## 📂 Project Structure

```text
Mzansi-Law-GPT/
├── api_server.py            # FastAPI backend server
├── contract_review.py       # Contract auditing logic and RAG chain
├── data_ingestion.py        # Pipeline to chunk and upload texts to Qdrant
├── download_core_acts.py    # SAFLII web scraper and fallback structured texts
├── data/                    # Storage for raw legal texts and file uploads
├── audit_reports/           # Generated markdown audit reports
├── dashboard/               # Next.js frontend application
│   ├── src/app/             # Next.js pages and routing
│   └── src/components/      # UI Components (ChatConsultant, ContractAuditor, etc.)
└── requirements.txt         # Python dependencies
```

## ⚖️ Disclaimer
*Mzansi-Law-GPT is an educational/open-source AI tool and does not constitute formal legal advice. Always consult a qualified South African attorney for legal matters.*