# MediAssist AI

MediAssist AI is a full-stack medical education application with a retrieval-augmented generation (RAG) chatbot. Built for academic demonstrations, portfolio presentations, and local submissions, it answers questions using context retrieved from a medical PDF.

The backend extracts and chunks PDF text, generates embeddings locally, and stores them in a persistent Chroma database. For each question, it retrieves relevant passages and passes those passages as source context to the OpenAI Responses API. The interface displays educational answers with source snippets.

> **Medical safety:** This application is for educational use only. It is not a substitute for a licensed healthcare professional and must not be used for diagnosis, prescriptions, triage, or treatment decisions. For emergencies—including chest pain, breathing difficulty, signs of stroke, heavy bleeding, poisoning, loss of consciousness, or risk of self-harm—seek immediate professional or emergency help.

## Features

- Responsive Home, About, Services/Features, AI Medical Bot, and Contact pages
- Embedded chatbot with suggested prompts, loading states, source snippets, and safety warnings
- PDF ingestion with page metadata and overlapping text chunks
- Local embeddings and persistent vector storage
- Retrieval checks that reject questions without sufficient supporting context
- API endpoints for health checks, chat, indexing, index status, suggested prompts, and contact submissions

## Technology Stack

| Component | Technology |
| --- | --- |
| Frontend | React 19, Vite 8, Tailwind CSS 4, React Router, Framer Motion, Lucide React |
| Backend | Flask 3, Flask-CORS, python-dotenv |
| PDF extraction | pypdf |
| Embeddings | SentenceTransformers with `sentence-transformers/all-MiniLM-L6-v2` |
| Vector storage | Chroma, persisted in `backend/storage/chroma_db` |
| Answer generation | OpenAI Responses API; default model: `gpt-5.4-mini` |
| Configuration | Separate backend and frontend `.env` files |

## Architecture

```text
Medical PDF → pypdf → overlapping chunks → SentenceTransformers → Chroma

User question
  → React ChatWidget
  → POST /api/chat
  → Flask ChatbotService
  → SentenceTransformer query embedding
  → Chroma vector search
  → retrieval validation
  → retrieved PDF context + question → OpenAI Responses API
  → educational answer + source snippets + warning
  → React chat interface
```

### Repository Structure

```text
medical-ai-bot/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_loader.py
│   │   ├── text_splitter.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   ├── prompt_builder.py
│   │   ├── openai_client.py
│   │   └── chatbot_service.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat_routes.py
│   │   ├── index_routes.py
│   │   └── contact_routes.py
│   ├── data/
│   │   └── medical_book.pdf
│   ├── storage/
│   │   └── chroma_db/
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── .env.example
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/client.js
│       ├── assets/
│       ├── components/
│       ├── pages/
│       ├── router/AppRouter.jsx
│       └── styles/global.css
├── docs/
│   └── viva_guide.md
└── README.md
```

The PDF and Chroma directory are local runtime inputs and generated data; their inclusion in this layout does not imply they should be committed.

## Local Setup

### Prerequisites

- Python 3.10+
- Node.js 20.19+ recommended for Vite 8
- An OpenAI API key
- A medical PDF you are authorized to use

The commands below use PowerShell and start from the repository root (`medical-ai-bot`). Internet access is required to download the embedding model on its first run.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `backend/.env`. Place your medical PDF at `backend/data/medical_book.pdf`, replacing the sample if present, or update `MEDICAL_BOOK_PATH` in `backend/.env`.

Start the backend:

```powershell
python app.py
```

The local API is available at `http://localhost:5000`.

### Frontend

Open a second terminal at the repository root:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173), then build the PDF index before asking questions.

### Configuration

Create each `.env` file from its corresponding `.env.example`. Keep real credentials only in the local backend `.env`; never add them to the example files or frontend configuration.

Backend (`backend/.env`):

```env
OPENAI_API_KEY=
FLASK_ENV=development
FLASK_APP=app.py
VECTOR_STORE_DIR=storage/chroma_db
MEDICAL_BOOK_PATH=data/medical_book.pdf
OPENAI_MODEL=gpt-5.4-mini
OPENAI_CHAT_FALLBACK_MODEL=gpt-4.1-mini
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
MIN_RELEVANCE_SCORE=0.45
MIN_KEYWORD_COVERAGE=0.60
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
```

The current architecture uses local Chroma storage. Pinecone is listed as a future option; its configuration entries can remain empty for the local setup.

Frontend (`frontend/.env`):

```env
VITE_API_BASE_URL=http://localhost:5000
```

## PDF Indexing and Chat

On the AI Medical Bot page, select **Rebuild PDF Index**, or run:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/index/rebuild
```

The backend loads the PDF specified by `MEDICAL_BOOK_PATH`, extracts text page by page with `pypdf`, splits it into overlapping chunks, and generates SentenceTransformer embeddings. Chroma stores the vectors, text, and metadata. The indexing response includes the number of indexed chunks.

Check the index status:

```powershell
Invoke-RestMethod -Uri http://localhost:5000/api/index/status
```

For chat, the frontend sends `POST /api/chat` with a JSON body:

```json
{ "message": "What is hypertension?" }
```

The backend validates the question, embeds it, and retrieves matching chunks from Chroma. Before answer generation, strict RAG checks evaluate vector similarity and keyword coverage. Questions that are out of domain, too vague, meta-only, or lack direct support for their key medical terms are refused with no visible sources.

When context is insufficient, the chatbot returns:

```text
I do not have enough relevant medical-book context to answer that confidently.
```

When the checks pass, retrieved chunks are formatted into a grounded prompt. The backend uses the OpenAI Python SDK (`OpenAI` and `client.responses.create(...)`) with a safety-focused system prompt to generate a concise educational answer. It returns the answer, source snippets, and a warning for the frontend to display.

## API Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check API health |
| `POST` | `/api/chat` | Submit a question |
| `POST` | `/api/index/rebuild` | Rebuild the PDF index |
| `GET` | `/api/index/status` | Check index status |
| `GET` | `/api/suggested-prompts` | Retrieve suggested questions |
| `POST` | `/api/contact` | Submit the contact form |

## Repository Hygiene and Security

- **Never commit real API keys or secrets**, including in source code, documentation, screenshots, or logs.
- Create `backend/.env` and `frontend/.env` from their respective `.env.example` files. Keep `.env.example` files credential-free; do not replace their placeholders with real credentials.
- Ensure `.env` files are ignored by Git before adding credentials. Frontend configuration is exposed to the browser, so keep the OpenAI API key in the backend only.
- If a key is accidentally exposed, revoke or rotate it immediately. Remove it from tracked files and repository history as appropriate; deleting it from the latest commit alone does not invalidate the exposed key.
- Do not commit generated Chroma data unless intentionally required and reviewed for sensitive content. It contains source text and metadata as well as embeddings and can be rebuilt from the PDF.
- Do not commit private medical PDFs, patient information, or copyrighted medical PDFs without explicit redistribution rights. Keep source documents local unless they are suitable and authorized for public distribution.
- Exclude local environments, installed dependencies, and generated build files from version control.

Recommended root `.gitignore` entries:

```gitignore
# Local configuration and secrets
.env
.env.*
!.env.example

# Generated vector data and local source PDFs
/backend/storage/chroma_db/
/backend/data/*.pdf

# Dependencies and generated files
.venv/
__pycache__/
*.py[cod]
node_modules/
/frontend/dist/
```

Ignore any custom PDF or vector-store paths as well. Git ignore rules do not stop tracking files already committed; remove those files from tracking separately while retaining any needed local copies.

## Limitations

- Answer quality depends on the source PDF's quality and coverage.
- Scanned PDFs may extract poorly without OCR, which is not currently included.
- The embedding model requires an internet connection for its initial download.
- Retrieval checks assess supporting context; the system does not independently validate medical correctness.
- The application is intended for academic and local educational use, not clinical decision-making or emergency care.

## Planned Improvements

- Admin uploads and support for multiple PDFs
- OCR for scanned documents
- Citation scoring, answer evaluation, and a model evaluation test set
- Pinecone or another managed vector store
- Chat history, user accounts, and streaming answers
- Docker deployment
- Clinical review workflow before any real-world use
