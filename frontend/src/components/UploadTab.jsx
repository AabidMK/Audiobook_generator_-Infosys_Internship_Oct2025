import React, { useState } from "react";

export default function UploadTab({ setAudioUrl, audioUrl }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");

  const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

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

  return (
    <div className="p-6 text-center">
      <h2 className="text-2xl font-semibold mb-4">Upload Document</h2>

      <input
        type="file"
        accept=".pdf,.txt,.docx"
        onChange={(e) => setFile(e.target.files[0])}
        className="block mx-auto mb-4 border p-2 rounded"
      />

      <button
        onClick={handleUpload}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Upload & Process
      </button>

      <p className="mt-4 text-gray-600">{status}</p>

      {audioUrl && (
        <div className="mt-6">
          <h3 className="font-semibold mb-2">🎧 Generated Audio:</h3>
          <audio controls src={audioUrl} style={{ marginTop: "1rem" }} />
        </div>
      )}
    </div>
  );
}
