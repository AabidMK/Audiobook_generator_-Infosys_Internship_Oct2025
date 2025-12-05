/* eslint-disable no-unused-vars */
import React, { useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";

const API_BASE = "http://localhost:8000";

export default function ChatTab() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!query.trim()) {
      toast.error("Please type a question.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setSources([]);

    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        query,
        top_k: 5,
      });

      setAnswer(res.data.answer || "No answer returned.");
      setSources(res.data.sources || []);
      toast.success("Answer retrieved!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to get answer from backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Question Input */}
      <div>
        <label className="block text-sm font-semibold mb-2">
          Ask a question about your uploaded document
        </label>
        <textarea
          rows={3}
          className="w-full border rounded-lg p-3 text-sm bg-gray-50 text-gray-800"
          placeholder="e.g., Summarize the main idea of this document..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {/* Ask Button */}
      <button
        onClick={handleAsk}
        disabled={loading || !query.trim()}
        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Thinking..." : "Ask 💬"}
      </button>

      {/* Answer Section */}
      {answer && (
        <div className="bg-gray-100 p-4 rounded-lg border-l-4 border-indigo-600 shadow-sm">
          <h3 className="font-semibold mb-1 text-gray-800 text-sm">💡 Answer</h3>
          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
            {answer}
          </p>
        </div>
      )}

      {/* Sources Section */}
      {sources.length > 0 && (
        <div className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300">
          <h4 className="font-semibold text-gray-800 text-sm mb-2">
            📚 Sources (top matches)
          </h4>
          <ul className="space-y-2 text-xs text-gray-700">
            {sources.map((s, idx) => (
              <li
                key={idx}
                className="border-b border-gray-200 pb-2 last:border-none"
              >
                <div className="font-semibold">
                  {s.source || "Unknown file"}{" "}
                  <span className="text-gray-500">
                    (score: {s.score?.toFixed ? s.score.toFixed(3) : s.score})
                  </span>
                </div>
                <div className="mt-1 line-clamp-3">{s.text}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
