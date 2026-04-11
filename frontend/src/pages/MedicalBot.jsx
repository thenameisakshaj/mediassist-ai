import { useEffect, useState } from "react";
import { BookMarked, Database, RefreshCcw } from "lucide-react";

import { getIndexStatus, rebuildIndex } from "../api/client.js";
import ChatWidget from "../components/ChatWidget.jsx";
import DisclaimerBanner from "../components/DisclaimerBanner.jsx";
import Footer from "../components/Footer.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";

export default function MedicalBot() {
  const [sources, setSources] = useState([]);
  const [status, setStatus] = useState(null);
  const [indexing, setIndexing] = useState(false);
  const [statusError, setStatusError] = useState("");

  async function refreshStatus() {
    try {
      const data = await getIndexStatus();
      setStatus(data);
      setStatusError("");
    } catch (err) {
      setStatusError(err.message);
    }
  }

  async function handleRebuildIndex() {
    setIndexing(true);
    setStatusError("");
    try {
      await rebuildIndex();
      await refreshStatus();
    } catch (err) {
      setStatusError(err.message);
    } finally {
      setIndexing(false);
    }
  }

  useEffect(() => {
    refreshStatus();
  }, []);

  return (
    <>
      <section className="page-hero bg-slate-50">
        <div className="section-inner grid gap-8 lg:grid-cols-[1fr_0.8fr] lg:items-end">
          <div>
            <span className="eyebrow">AI Medical Bot</span>
            <h1>Book-grounded medical Q&A with visible source snippets.</h1>
            <p>
              Ask concise medical-learning questions. The backend validates the message,
              retrieves matching PDF chunks, sends context to OpenAI, and returns a safe answer.
            </p>
          </div>
          <DisclaimerBanner compact />
        </div>
      </section>

      <section className="section bg-white">
        <div className="section-inner grid gap-8 lg:grid-cols-[1.25fr_0.75fr]">
          <ChatWidget onSourcesChange={setSources} />

          <aside className="space-y-5">
            <div className="card">
              <div className="mb-4 flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-bold text-cyan-700">Indexing status</p>
                  <h2>Medical book vector store</h2>
                </div>
                <Database className="text-cyan-700" size={28} />
              </div>
              {status ? (
                <div className="grid gap-3 text-sm text-slate-700">
                  <p><strong>Indexed:</strong> {status.indexed ? "Yes" : "No"}</p>
                  <p><strong>Vector store:</strong> {status.vector_store}</p>
                  <p><strong>Document:</strong> {status.document_name}</p>
                  <p><strong>Chunks:</strong> {status.chunks_indexed ?? 0}</p>
                </div>
              ) : (
                <LoadingSpinner />
              )}
              {statusError && <p className="mt-4 text-sm font-semibold text-rose-700">{statusError}</p>}
              <button className="btn-primary mt-5 w-full justify-center" onClick={handleRebuildIndex} disabled={indexing}>
                <RefreshCcw size={18} />
                {indexing ? "Rebuilding index..." : "Rebuild PDF Index"}
              </button>
            </div>

            <div className="card">
              <p className="text-sm font-bold text-cyan-700">Retrieved source/context snippet panel</p>
              <h2 className="mt-1">Latest retrieved context</h2>
              <div className="mt-5 space-y-4">
                {sources.length > 0 ? (
                  sources.map((source) => (
                    <div className="source-snippet" key={`${source.label}-${source.chunk_index}`}>
                      <div className="mb-2 flex items-center gap-2 text-xs font-bold text-cyan-800">
                        <BookMarked size={14} />
                        {source.label} - page {source.page || "unknown"}
                      </div>
                      <p>{source.snippet}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm leading-6 text-slate-600">
                    Ask a question after indexing the PDF. Retrieved source snippets will appear here.
                  </p>
                )}
              </div>
            </div>

            <div className="card">
              <p className="text-sm font-bold text-cyan-700">How answers are generated</p>
              <ol className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
                <li>1. The frontend sends your question to <strong>/api/chat</strong>.</li>
                <li>2. The backend embeds the question and queries Chroma.</li>
                <li>3. Retrieved chunks are inserted into a safety-aware prompt.</li>
                <li>4. OpenAI generates a concise answer grounded in that context.</li>
              </ol>
              <p className="mt-5 text-sm font-semibold text-slate-700">
                Answers are educational, not professional medical advice.
              </p>
            </div>
          </aside>
        </div>
      </section>

      <Footer />
    </>
  );
}
