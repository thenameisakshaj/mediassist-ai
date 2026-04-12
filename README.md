# MediAssist AI

MediAssist AI is a full-stack academic medical website with an embedded retrieval-based AI chatbot. It is designed for a viva, portfolio demo, and local academic submission.

The chatbot is not a generic assistant. It loads a medical PDF, splits the text into chunks, creates embeddings, stores them in a local Chroma vector store, retrieves relevant chunks for a user question, and sends only that retrieved context to OpenAI for a concise educational answer.

## Final Tech Stack

- Frontend: React 19, Vite 8, Tailwind CSS 4, React Router, Framer Motion, Lucide React
- Backend: Flask 3, Flask-CORS, Python dotenv
- PDF processing: pypdf
- Embeddings: SentenceTransformers with `sentence-transformers/all-MiniLM-L6-v2`
- Vector store: Chroma persisted locally in `backend/storage/chroma_db`
- LLM: OpenAI Responses API with `gpt-5.4-mini` by default
- Configuration: `.env` files for backend and frontend

OpenAI API usage follows the official Python SDK pattern from the OpenAI API docs: `from openai import OpenAI` and `client.responses.create(...)`.

## Full Folder Structure

```text
medical-ai-bot/
|-- backend/
|   |-- app.py
|   |-- config.py
|   |-- requirements.txt
|   |-- .env.example
|   |-- services/
|   |   |-- __init__.py
|   |   |-- pdf_loader.py
|   |   |-- text_splitter.py
|   |   |-- embeddings.py
|   |   |-- vector_store.py
|   |   |-- retriever.py
|   |   |-- prompt_builder.py
|   |   |-- openai_client.py
|   |   `-- chatbot_service.py
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- chat_routes.py
|   |   |-- index_routes.py
|   |   `-- contact_routes.py
|   |-- data/
|   |   `-- medical_book.pdf
|   |-- storage/
|   |   `-- chroma_db/
|   `-- utils/
|       |-- __init__.py
|       |-- logger.py
|       `-- helpers.py
|-- frontend/
|   |-- package.json
|   |-- vite.config.js
|   |-- index.html
|   |-- .env.example
|   `-- src/
|       |-- main.jsx
|       |-- App.jsx
|       |-- api/client.js
|       |-- assets/
|       |-- components/
|       |-- pages/
|       |-- router/AppRouter.jsx
|       `-- styles/global.css
|-- docs/
|   `-- viva_guide.md
`-- README.md
```

## Features

- Modern responsive medical-tech website
- Home, About, Services/Features, AI Medical Bot, and Contact pages
- Embedded chatbot with suggested prompts and loading states
- Flask API with health, chat, indexing, status, suggestions, and contact routes
- PDF ingestion with page metadata
- Chunking with overlap for better retrieval continuity
- Local embedding generation for indexing
- Persistent Chroma vector store
- OpenAI answer generation with a safety-focused system prompt
- Source snippet display for retrieved context
- Medical disclaimer and emergency-care warning

## Architecture

```text
User question
  -> React ChatWidget
  -> POST /api/chat
  -> Flask ChatbotService
  -> SentenceTransformer query embedding
  -> Chroma vector search
  -> retrieved PDF chunks
  -> OpenAI Responses API
  -> concise educational answer + sources
  -> React renders answer and snippets
```

## Backend API

- `GET /api/health`
- `POST /api/chat`
- `POST /api/index/rebuild`
- `GET /api/index/status`
- `GET /api/suggested-prompts`
- `POST /api/contact`

## Environment Variables

Backend: create `backend/.env` from `backend/.env.example`.

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

Frontend: create `frontend/.env` from `frontend/.env.example`.

```env
VITE_API_BASE_URL=http://localhost:5000
```

Never commit real API keys.

## Setup Steps

Requirements:

- Python 3.10+
- Node.js 20.19+ recommended for Vite 8
- An OpenAI API key

Backend setup:

```powershell
cd medical-ai-bot\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and add `OPENAI_API_KEY`.

Replace the sample `backend/data/medical_book.pdf` with your real medical book PDF, keeping the same filename or updating `MEDICAL_BOOK_PATH`.

Start backend:

```powershell
python app.py
```

Frontend setup:

```powershell
cd medical-ai-bot\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open:

```text
http://localhost:5173
```

## Indexing Workflow

Use the AI Medical Bot page and click "Rebuild PDF Index", or call:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/index/rebuild
```

The backend will:

1. Load the PDF from `MEDICAL_BOOK_PATH`
2. Extract text page by page with `pypdf`
3. Split text into overlapping chunks
4. Create embeddings with SentenceTransformers
5. Store vectors, text, and metadata in Chroma
6. Return the number of indexed chunks

Check status:

```powershell
Invoke-RestMethod -Uri http://localhost:5000/api/index/status
```

## Chatbot Workflow

1. The user enters a medical question in the React chat UI.
2. The frontend sends `POST /api/chat` with `{ "message": "..." }`.
3. The backend validates the question.
4. The retriever embeds the question and searches Chroma.
5. Retrieved chunks are formatted into a grounded prompt.
6. OpenAI generates a concise educational answer.
7. The backend returns answer, source snippets, and warning.
8. The frontend renders the answer and retrieved context.

If the context is insufficient, the chatbot returns:

```text
I do not have enough relevant medical-book context to answer that confidently.
```

Strict RAG refusal mode runs before answer generation. The backend checks both vector similarity and keyword coverage against the retrieved chunks. If the question is out-of-domain, too vague, meta-only, or the key medical terms are not directly supported by the retrieved book context, the chatbot refuses and returns no visible sources.

## Screenshots

Add screenshots after running the app:

- `docs/screenshots/home.png`
- `docs/screenshots/bot.png`
- `docs/screenshots/index-status.png`

## Limitations

- Educational use only
- Not a substitute for doctors or licensed healthcare professionals
- Should not be used for emergencies
- Depends on the quality and coverage of the source PDF
- PDF extraction may be weak for scanned books unless OCR is added
- Local embedding model download requires internet on first run
- The system does not validate medical correctness beyond retrieved context

## Ethical Note

MediAssist AI must not be used for diagnosis, prescriptions, triage, or treatment decisions. Medical questions involving severe symptoms, chest pain, breathing difficulty, stroke signs, heavy bleeding, poisoning, loss of consciousness, or self-harm require immediate professional or emergency help.

## Future Scope

- Admin upload flow for multiple PDFs
- OCR support for scanned books
- Citation scoring and answer evaluation
- Pinecone or managed vector store option
- Chat history and user accounts
- Streaming answers
- Model evaluation test set
- Docker deployment
- Clinical review workflow before real-world use


