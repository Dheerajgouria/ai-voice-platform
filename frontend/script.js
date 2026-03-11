const textInput = document.getElementById('textInput');
const generateBtn = document.getElementById('generateBtn');
const statusMessage = document.getElementById('statusMessage');
const audioContainer = document.getElementById('audioContainer');
const audioPlayer = document.getElementById('audioPlayer');

async function generateAudio() {
  const text = textInput.value.trim();

  if (!text) {
    statusMessage.textContent = 'Please enter some text first.';
    statusMessage.className = 'mt-4 min-h-6 text-sm text-amber-300';
    return;
  }

  generateBtn.disabled = true;
  statusMessage.textContent = 'Generating audio...';
  statusMessage.className = 'mt-4 min-h-6 text-sm text-slate-300';

  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to generate audio.');
    }

    audioPlayer.src = data.audio_url;
    audioContainer.classList.remove('hidden');
    statusMessage.textContent = 'Audio generated successfully!';
    statusMessage.className = 'mt-4 min-h-6 text-sm text-emerald-300';
  } catch (error) {
    statusMessage.textContent = error.message;
    statusMessage.className = 'mt-4 min-h-6 text-sm text-rose-300';
  } finally {
    generateBtn.disabled = false;
  }
}

generateBtn.addEventListener('click', generateAudio);
