# MediAssist AI Viva Guide

## 1. What is RAG?

RAG means Retrieval-Augmented Generation. Instead of asking the model to answer from memory, the system first retrieves relevant context from a knowledge source and then asks the LLM to generate an answer using that context.

## 2. Why are embeddings used?

Embeddings convert text into numerical vectors that capture semantic meaning. This lets the system find book chunks related to a user question even when the exact words are different.

## 3. How does the vector store work?

Chroma stores each PDF chunk with its embedding and metadata such as source file, page number, and chunk index. During chat, the question is embedded and compared against stored vectors to retrieve the most similar chunks.

## 4. Why is OpenAI used?

OpenAI is used for answer generation after retrieval. The backend sends the retrieved medical-book context and user question to the OpenAI Responses API so the final answer is readable, concise, and safety-aware.

## 5. How is this different from a static chatbot?

A static chatbot usually returns predefined answers or general model responses. MediAssist AI retrieves live context from the indexed PDF, returns source snippets, and refuses when the book context is insufficient.

## 6. Why is this a dynamic website?

The React frontend calls live Flask APIs for chat, index status, index rebuild, suggested prompts, and contact form submission. The chatbot state, loading state, source snippets, and index status update dynamically.

## 7. Explain the architecture.

The frontend is React + Vite. The backend is Flask with separated route and service layers. The ingestion pipeline loads the PDF, chunks text, creates embeddings, and stores them in Chroma. The chat route retrieves context and calls OpenAI for answer generation.

## 8. What are the main limitations?

The system depends on the PDF quality and coverage. It is not a medical device, does not replace doctors, and cannot handle emergencies. Scanned PDFs need OCR support. Model output should still be reviewed in serious contexts.

## 9. What ethical considerations are included?

The UI and backend include disclaimers, avoid diagnosis or prescriptions, warn users about emergencies, and require the assistant to say when retrieved context is insufficient. Real healthcare decisions require licensed professionals.

## 10. What future improvements would you add?

I would add admin PDF upload, multiple-book indexing, OCR for scanned documents, streaming responses, automated retrieval evaluation, stronger citation formatting, user authentication, and Docker deployment.
