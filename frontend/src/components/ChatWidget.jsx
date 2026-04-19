import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";

import { getSuggestedPrompts, sendChatMessage } from "../api/client.js";
import ChatMessage from "./ChatMessage.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";
import SuggestedPrompts from "./SuggestedPrompts.jsx";

const initialMessages = [
  {
    id: "welcome",
    role: "assistant",
    content:
      "Ask a medical topic from the indexed book. I will retrieve relevant chunks first and keep the answer educational.",
    sources: [],
    warning: ""
  }
];

function makeMessage(role, content, extras = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
    ...extras
  };
}

function createSessionId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function ChatWidget({ onSourcesChange, compact = false }) {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sharedLocation, setSharedLocation] = useState(null);
  const listRef = useRef(null);
  const requestIdRef = useRef(0);
  const sessionIdRef = useRef(createSessionId());

  useEffect(() => {
    getSuggestedPrompts()
      .then((data) => setPrompts(data.prompts || []))
      .catch(() => setPrompts(["What is acne?", "What causes fever?", "What is anemia?"]));
  }, []);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(value = input) {
    const question = value.trim();
    if (!question || loading) return;

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    setInput("");
    setError("");
    setLoading(true);
    setMessages((current) => [...current, makeMessage("user", question)]);

    try {
      const data = await sendChatMessage(
        question,
        sessionIdRef.current,
        sharedLocation ? { location: sharedLocation } : undefined
      );
      const assistantMessage = makeMessage("assistant", data.answer, {
        sources: data.sources || [],
        warning: data.warning || "",
        triage: {
          needLevel: data.need_level,
          needLabel: data.need_label,
          careGuidance: data.care_guidance || null,
          suggestNearbyCare: Boolean(data.suggest_nearby_care),
          triageReason: data.triage_reason || null
        }
      });

      if (requestId !== requestIdRef.current) return;

      setMessages((current) => [...current, assistantMessage]);
      onSourcesChange?.(data.sources || []);
    } catch (err) {
      const fallback = "I could not reach the medical assistant service. Check the backend, API key, and vector index status.";

      if (requestId !== requestIdRef.current) return;

      setError(err.message || fallback);
      setMessages((current) => [...current, makeMessage("assistant", fallback)]);
      onSourcesChange?.([]);
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }

  return (
    <div className={`chat-panel ${compact ? "min-h-[560px]" : "min-h-[680px]"}`}>
      <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
        <div>
          <p className="flex items-center gap-2 text-sm font-bold text-cyan-700">
            <Sparkles size={17} /> Retrieval-based medical assistant
          </p>
          <h2 className="mt-1 text-2xl font-black text-slate-950">Ask MediAssist AI</h2>
        </div>
        <span className="rounded-lg bg-teal-50 px-3 py-1 text-xs font-bold text-teal-800">
          RAG mode
        </span>
      </div>

      <div ref={listRef} className="flex-1 space-y-4 overflow-y-auto p-5">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            sharedLocation={sharedLocation}
            onLocationResolved={setSharedLocation}
          />
        ))}
        {loading && (
          <div className="chat-bubble chat-bubble-bot">
            <LoadingSpinner />
          </div>
        )}
      </div>

      <div className="border-t border-slate-200 p-5">
        <SuggestedPrompts prompts={prompts} onSelect={handleSend} />
        {error && <p className="mt-3 text-sm font-semibold text-rose-700">{error}</p>}
        <form
          className="mt-4 flex flex-col gap-3 md:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            handleSend();
          }}
        >
          <input
            className="input"
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask: What is anemia?"
            aria-label="Medical question"
          />
          <button className="btn-primary shrink-0" type="submit" disabled={loading}>
            <Send size={18} />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
