const authSection = document.getElementById('authSection');
const appSection = document.getElementById('appSection');
const userBadge = document.getElementById('userBadge');

const registerUsername = document.getElementById('registerUsername');
const registerPassword = document.getElementById('registerPassword');
const loginUsername = document.getElementById('loginUsername');
const loginPassword = document.getElementById('loginPassword');
const registerBtn = document.getElementById('registerBtn');
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');

const textInput = document.getElementById('textInput');
const voiceMode = document.getElementById('voiceMode');
const speakerAudio = document.getElementById('speakerAudio');
const generateBtn = document.getElementById('generateBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusMessage = document.getElementById('statusMessage');
const audioPlayer = document.getElementById('audioPlayer');
const historyList = document.getElementById('historyList');

let token = localStorage.getItem('authToken') || '';
let username = localStorage.getItem('username') || '';
let latestAudioUrl = '';

function setStatus(message, color = 'text-slate-300') {
  statusMessage.className = `mt-3 text-sm ${color}`;
  statusMessage.textContent = message;
}

function setAuthState(isLoggedIn) {
  authSection.classList.toggle('hidden', isLoggedIn);
  appSection.classList.toggle('hidden', !isLoggedIn);
  userBadge.classList.toggle('hidden', !isLoggedIn);
  userBadge.textContent = isLoggedIn ? `Logged in as @${username}` : '';
}

async function register() {
  const payload = {
    username: registerUsername.value.trim(),
    password: registerPassword.value,
  };

  const response = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Registration failed.');
  setStatus('Account created. Please login.', 'text-emerald-300');
}

async function login() {
  const payload = {
    username: loginUsername.value.trim(),
    password: loginPassword.value,
  };

  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Login failed.');

  token = data.token;
  username = data.username;
  localStorage.setItem('authToken', token);
  localStorage.setItem('username', username);

  setAuthState(true);
  await loadHistory();
  setStatus('Login successful.', 'text-emerald-300');
}

function logout() {
  token = '';
  username = '';
  localStorage.removeItem('authToken');
  localStorage.removeItem('username');
  setAuthState(false);
  historyList.innerHTML = '';
  setStatus('Logged out.', 'text-slate-300');
}

async function generateAudio() {
  const text = textInput.value.trim();
  if (!text) {
    setStatus('Please enter text first.', 'text-amber-300');
    return;
  }

  if (!token) {
    setStatus('Please login first.', 'text-amber-300');
    return;
  }

  const formData = new FormData();
  formData.append('text', text);

  if (voiceMode.value === 'clone') {
    const file = speakerAudio.files[0];
    if (!file) {
      setStatus('Choose a speaker sample for voice cloning.', 'text-amber-300');
      return;
    }
    formData.append('speaker_audio', file);
  }

  generateBtn.disabled = true;
  setStatus('Generating audio...', 'text-slate-300');

  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to generate audio.');
    }

    latestAudioUrl = data.audio_url;
    audioPlayer.src = latestAudioUrl;
    setStatus(`Generated successfully (${data.voice_mode}).`, 'text-emerald-300');
    await loadHistory();
  } catch (error) {
    setStatus(error.message, 'text-rose-300');
  } finally {
    generateBtn.disabled = false;
  }
}

async function loadHistory() {
  const response = await fetch('/history', {
    headers: { Authorization: `Bearer ${token}` },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to load history.');
  }

  if (!data.items.length) {
    historyList.innerHTML = '<p class="text-slate-400">No generated audio yet.</p>';
    return;
  }

  historyList.innerHTML = data.items
    .map(
      (item) => `
      <div class="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
        <p class="font-medium text-slate-200">${item.text}</p>
        <p class="mt-1 text-xs uppercase tracking-wide text-cyan-300">${item.voice_mode} • ${new Date(item.created_at).toLocaleString()}</p>
        <div class="mt-2 flex gap-2">
          <button class="rounded bg-cyan-500 px-3 py-1 text-xs font-semibold text-slate-950" onclick="playHistory('${item.audio_url}')">Play</button>
          <a class="rounded border border-cyan-400 px-3 py-1 text-xs font-semibold text-cyan-200" href="${item.audio_url}" download>Download</a>
        </div>
      </div>
    `,
    )
    .join('');
}

window.playHistory = (url) => {
  latestAudioUrl = url;
  audioPlayer.src = url;
  audioPlayer.play();
};

function downloadLatestAudio() {
  if (!latestAudioUrl) {
    setStatus('Generate or select audio first.', 'text-amber-300');
    return;
  }

  const link = document.createElement('a');
  link.href = latestAudioUrl;
  link.download = 'generated-voice.wav';
  document.body.appendChild(link);
  link.click();
  link.remove();
}

registerBtn.addEventListener('click', async () => {
  try {
    await register();
  } catch (error) {
    setStatus(error.message, 'text-rose-300');
  }
});

loginBtn.addEventListener('click', async () => {
  try {
    await login();
  } catch (error) {
    setStatus(error.message, 'text-rose-300');
  }
});

logoutBtn.addEventListener('click', logout);
generateBtn.addEventListener('click', generateAudio);
downloadBtn.addEventListener('click', downloadLatestAudio);

if (token && username) {
  setAuthState(true);
  loadHistory().catch((error) => setStatus(error.message, 'text-rose-300'));
} else {
  setAuthState(false);
}
