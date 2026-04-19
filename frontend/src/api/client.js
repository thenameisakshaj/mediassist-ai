const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || data.message || "Request failed");
  }

  return data;
}

export function getSuggestedPrompts() {
  return request("/api/suggested-prompts");
}

export function sendChatMessage(message, sessionId, extraPayload = {}) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
      ...(extraPayload || {})
    })
  });
}

export function getIndexStatus() {
  return request("/api/index/status");
}

export function rebuildIndex() {
  return request("/api/index/rebuild", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function submitContactForm(payload) {
  return request("/api/contact", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
