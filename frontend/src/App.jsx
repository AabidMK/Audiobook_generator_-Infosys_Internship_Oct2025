import React, { useState } from "react";
import { FaUpload, FaRobot, FaHeadphones, FaPlayCircle } from "react-icons/fa";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("upload");
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [audioUrl, setAudioUrl] = useState(null);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // ==============================
  // 📘 Upload & Audio Generation
  // ==============================
  const handleUpload = async () => {
    if (!file) {
      setStatus("⚠️ Please select a file first.");
      return;
    }

    setStatus("⏳ Uploading & Processing...");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${backendUrl}/process_document`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const data = await response.json();
      setStatus("✅ Successfully processed!");
      setAudioUrl(`${backendUrl}${data.audio_url}`);
    } catch (error) {
      console.error("Upload error:", error);
      setStatus("❌ Failed to process file.");
    }
  };

  // ==============================
  // 💬 Chat Q&A
  // ==============================
  const handleChat = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setAnswer("");

    try {
      const res = await fetch(`${backendUrl}/chat_query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 3 }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setAnswer(data.answer || "No answer found.");
    } catch (err) {
      console.error(err);
      setAnswer("❌ Failed to get response from backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="root">
      <h1>
        <FaHeadphones className="icon" /> AI Audiobook & Q&A Assistant
      </h1>
      <p>Upload your document, generate an audiobook, or chat with it directly.</p>

      {/* === Navigation Tabs === */}
      <nav>
        <button
          className={tab === "upload" ? "active" : ""}
          onClick={() => setTab("upload")}
        >
          <FaUpload /> Audiobook Generator
        </button>
        <button
          className={tab === "chat" ? "active" : ""}
          onClick={() => setTab("chat")}
        >
          <FaRobot /> Chat / Q&A
        </button>
      </nav>

      {/* === Upload Tab === */}
      {tab === "upload" && (
        <main className="upload-section">
          <h2>
            <FaUpload className="icon" /> Upload Your Document
          </h2>
          <input
            type="file"
            accept=".pdf,.txt,.docx"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button className="upload-btn" onClick={handleUpload}>
            Upload & Process
          </button>
          <p className="status">{status}</p>

          {audioUrl && (
            <div className="audio-section">
              <h3>
                <FaPlayCircle className="icon" /> Generated Audio
              </h3>
              <audio controls src={audioUrl} />
            </div>
          )}
        </main>
      )}

      {/* === Chat Tab === */}
      {tab === "chat" && (
        <div className="chat-section">
          <h2>
            <FaRobot className="icon" /> Ask About Your Document
          </h2>

          <div className="chat-input-area">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your uploaded document..."
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
            ) : answer ? (
              <p className="answer-text">{answer}</p>
            ) : (
              <p>No response yet.</p>
            )}
          </div>
        </div>
      )}

      <footer>
        Backend: <code>{backendUrl}</code>
      </footer>
    </div>
  );
}
