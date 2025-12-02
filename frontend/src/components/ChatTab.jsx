import React, { useState } from "react";
import "../App.css";

export default function ChatTab({ setLastAnswer, lastAnswer }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const handleChat = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setLastAnswer("");

    try {
      const res = await fetch(`${backendUrl}/chat_query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 3 }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      // Only keep paragraph answer
      setLastAnswer(data.answer || "No answer found.");
    } catch (err) {
      console.error(err);
      setLastAnswer("❌ Failed to get response from backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-section">
      <h2>Chat / Q&amp;A</h2>

      <div className="chat-input-area">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your document..."
        />
        <button onClick={handleChat} disabled={loading}>
          {loading ? "Processing..." : "Ask"}
        </button>
      </div>

      <div className="chat-response">
        {loading ? (
          <div className="typing-dots">
            <span></span><span></span><span></span>
          </div>
        ) : lastAnswer ? (
          <p className="answer-text">{lastAnswer}</p>
        ) : (
          <p>No response yet.</p>
        )}
      </div>
    </div>
  );
}
