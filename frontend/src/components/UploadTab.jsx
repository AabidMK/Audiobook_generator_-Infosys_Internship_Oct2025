import React, { useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";

const API_BASE = "http://localhost:8000";

export default function UploadTab() {
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileUpload = async () => {
    if (!file) {
      toast.error("Please select a file first!");
      return;
    }

    setLoading(true);
    setUploadProgress(0);
    setAudioUrl("");
    setText("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await axios.post(`${API_BASE}/extract`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) {
            const percent = Math.round((e.loaded * 100) / e.total);
            setUploadProgress(percent);
          }
        },
      });

      setText(res.data.extracted_text || "");
      toast.success("Text extracted and saved to memory!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to extract text from file.");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAudio = async () => {
    if (!text.trim()) {
      toast.error("No text available. Extract text first.");
      return;
    }

    setLoading(true);
    setAudioUrl("");

    try {
      const res = await axios.post(
        `${API_BASE}/generate-audio`,
        {
          text,
          // You can customize voice & rate if needed:
          // voice: "en-US-JennyNeural",
          // rate: 180,
        },
        { responseType: "blob" }
      );

      const url = URL.createObjectURL(new Blob([res.data]));
      setAudioUrl(url);
      toast.success("Audio generated successfully!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to generate audio.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* File chooser */}
      <div>
        <label className="block text-sm font-semibold mb-2">
          Upload your document
        </label>
        <input
          type="file"
          accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-gray-800 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 p-2"
        />
        <p className="text-xs text-gray-500 mt-1">
          Supported: PDF, DOCX, TXT, images with text (if your backend supports OCR).
        </p>
      </div>

      {/* Upload progress */}
      {loading && (
        <div className="space-y-2">
          <p className="text-sm text-gray-700">
            {uploadProgress > 0 && uploadProgress < 100
              ? `Uploading... ${uploadProgress}%`
              : "Processing..."}
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleFileUpload}
          disabled={loading || !file}
          className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Processing..." : "Extract Text"}
        </button>

        <button
          onClick={handleGenerateAudio}
          disabled={loading || !text}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Working..." : "Generate Audio 🎧"}
        </button>
      </div>

      {/* Extracted text */}
      {text && (
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-gray-800 text-sm">
              Extracted Text
            </h2>
            <span className="text-xs text-gray-500">
              {text.split(/\s+/).length} words
            </span>
          </div>
          <textarea
            className="w-full border rounded-lg p-3 text-sm bg-gray-50 text-gray-800 h-40 resize-y"
            value={text}
            readOnly
          />
        </div>
      )}

      {/* Audio player */}
      {audioUrl && (
        <div className="space-y-2">
          <h2 className="font-semibold text-gray-800 text-sm">Preview Audio</h2>
          <audio
            controls
            className="w-full rounded-lg border border-gray-300 bg-gray-50"
          >
            <source src={audioUrl} type="audio/mp3" />
            Your browser does not support the audio element.
          </audio>
        </div>
      )}
    </div>
  );
}
