const textInput = document.getElementById('textInput');
const voiceSelect = document.getElementById('voiceSelect');
const generateBtn = document.getElementById('generateBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusMessage = document.getElementById('statusMessage');
const audioPlayer = document.getElementById('audioPlayer');

let latestAudioUrl = '';

async function generateAudio() {
  const text = textInput.value.trim();
  const selectedVoice = voiceSelect.value;

  if (!text) {
    statusMessage.textContent = 'Please enter some text first.';
    statusMessage.className = 'mt-5 min-h-6 text-sm text-amber-300';
    return;
  }

  generateBtn.disabled = true;
  statusMessage.textContent = `Generating audio using "${selectedVoice}" voice...`;
  statusMessage.className = 'mt-5 min-h-6 text-sm text-slate-300';

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

    latestAudioUrl = data.audio_url;
    audioPlayer.src = latestAudioUrl;
    statusMessage.textContent = 'Audio generated successfully!';
    statusMessage.className = 'mt-5 min-h-6 text-sm text-emerald-300';
  } catch (error) {
    statusMessage.textContent = error.message;
    statusMessage.className = 'mt-5 min-h-6 text-sm text-rose-300';
  } finally {
    generateBtn.disabled = false;
  }
}

function downloadAudio() {
  if (!latestAudioUrl) {
    statusMessage.textContent = 'Generate audio first, then download it.';
    statusMessage.className = 'mt-5 min-h-6 text-sm text-amber-300';
    return;
  }

  const link = document.createElement('a');
  link.href = latestAudioUrl;
  link.download = 'generated-voice.wav';
  document.body.appendChild(link);
  link.click();
  link.remove();
}

generateBtn.addEventListener('click', generateAudio);
downloadBtn.addEventListener('click', downloadAudio);
