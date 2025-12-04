import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gtts import gTTS
from pipeline import run_pipeline
import numpy as np

# -----------------------------
# 1️⃣ Initialize Flask app
# -----------------------------
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# 2️⃣ In-memory vector DB for dummy embeddings
# -----------------------------
vectordb = []

def generate_embedding(text):
    """Dummy embedding (replace with real LLM embeddings later)"""
    return np.random.rand(512).tolist()

def save_to_vectordb(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    for line in lines:
        if line.strip():
            vectordb.append({"text": line, "embedding": generate_embedding(line)})

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

# -----------------------------
# 3️⃣ Routes
# -----------------------------
@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = file.filename
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # 1️⃣ Extract text
    output_path = os.path.join(UPLOAD_FOLDER, filename + ".out.txt")
    extracted_text = run_pipeline(save_path, output_path)

    # Save embeddings to vectordb
    save_to_vectordb(output_path)

    # 2️⃣ Generate audio
    audio_filename = filename + ".mp3"
    audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
    tts = gTTS(text=extracted_text, lang='en')
    tts.save(audio_path)

    return jsonify({
        "text": extracted_text,
        "audio_file": f"/uploads/{audio_filename}"
    })


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/query', methods=['POST'])
def query_document():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    query_emb = generate_embedding(query)

    # Find top 5 similar text chunks
    scores = [(item, cosine_similarity(query_emb, item["embedding"])) for item in vectordb]
    top_k = sorted(scores, key=lambda x: x[1], reverse=True)[:5]
    retrieved_text = "\n".join([t[0]["text"] for t in top_k])

    # Dummy LLM response
    answer = f"LLM response based on document:\n{retrieved_text}"
    return jsonify({"answer": answer})


@app.route('/health')
def health():
    return "ok"


# -----------------------------
# 4️⃣ Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
