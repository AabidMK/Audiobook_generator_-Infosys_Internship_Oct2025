// src/api.js
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);

  const resp = await fetch(`${API_BASE}/process_document`, {
    method: "POST",
    body: form,
  });

  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(`Upload failed: ${resp.status} ${txt}`);
  }
  return resp.json();
}

export async function downloadAudio(audioUrl) {
  // returns blob
  const url = `${API_BASE}${audioUrl}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("Audio not found");
  return resp.blob();
}

export async function chatQuery(query, top_k = 3) {
  const resp = await fetch(`${API_BASE}/chat_query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k }),
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(`Chat failed: ${resp.status} ${txt}`);
  }
  return resp.json();
}
