import { BookMarked } from "lucide-react";

export default function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`chat-bubble ${isUser ? "chat-bubble-user" : "chat-bubble-bot"}`}>
        <p className="whitespace-pre-line">{message.content}</p>
        {!isUser && message.sources?.length > 0 && (
          <div className="mt-4 space-y-3 border-t border-slate-200 pt-3">
            {message.sources.map((source) => (
              <div key={`${source.label}-${source.chunk_index}`} className="source-snippet">
                <div className="mb-1 flex items-center gap-2 text-xs font-bold text-cyan-800">
                  <BookMarked size={14} />
                  {source.label} - page {source.page || "unknown"} - similarity {source.similarity}
                </div>
                <p>{source.snippet}</p>
              </div>
            ))}
          </div>
        )}
        {!isUser && message.warning && (
          <p className="mt-3 text-xs font-semibold text-slate-500">{message.warning}</p>
        )}
      </div>
    </div>
  );
}
