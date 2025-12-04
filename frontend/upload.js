document.getElementById('uploadBtn').addEventListener('click', async () => {
  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files.length) { alert("Select a file"); return; }
  const file = fileInput.files[0];
  const fd = new FormData();
  fd.append('file', file);
  document.getElementById('status').innerText = "Uploading...";

  try {
    const resp = await fetch('http://127.0.0.1:5000/process', { method: 'POST', body: fd });
    if (!resp.ok) throw new Error('Processing failed');

    const data = await resp.json();
    document.getElementById('extractedText').value = data.text;

    // Play audio
    const audioPlayer = document.getElementById('audioPlayer');
    audioPlayer.src = 'http://127.0.0.1:5000' + data.audio_file;
    audioPlayer.load();
    audioPlayer.play();

    document.getElementById('status').innerText = "Done! Text extracted and audio generated.";

  } catch (e) {
    document.getElementById('status').innerText = "Error: " + e.message;
  }
});

// Chat Query
document.getElementById('chatBtn').addEventListener('click', async () => {
  const query = document.getElementById('chatInput').value;
  const responseDiv = document.getElementById('chatResponse');
  if (!query) return alert("Enter a question");

  responseDiv.innerHTML = "Querying...";

  try {
    const resp = await fetch('http://127.0.0.1:5000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    if (!resp.ok) throw new Error("Query failed");

    const data = await resp.json();
    responseDiv.innerHTML = data.answer;

  } catch (e) {
    responseDiv.innerHTML = "Error: " + e.message;
  }
});
