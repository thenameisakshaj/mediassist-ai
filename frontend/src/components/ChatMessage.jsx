import { BookMarked } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";

import TriagePanel from "./TriagePanel.jsx";

const markdownPlugins = [remarkGfm, remarkBreaks];

function MessageBody({ content, isUser }) {
  if (isUser) {
    return <p className="whitespace-pre-line">{content}</p>;
  }

  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={markdownPlugins}
        skipHtml
        components={{
          a: ({ ...props }) => <a {...props} target="_blank" rel="noreferrer" />
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default function ChatMessage({ message, sharedLocation, onLocationResolved }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`chat-bubble ${isUser ? "chat-bubble-user" : "chat-bubble-bot"}`}>
        <MessageBody content={message.content} isUser={isUser} />
        {!isUser && (
          <TriagePanel
            triage={message.triage}
            sharedLocation={sharedLocation}
            onLocationResolved={onLocationResolved}
          />
        )}
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
