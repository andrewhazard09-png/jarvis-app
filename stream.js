async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMessage('user', text);

  const typing = document.getElementById('typing');
  const messages = document.getElementById('messages');
  messages.appendChild(typing);
  typing.classList.add('active');
  messages.scrollTop = messages.scrollHeight;

  const start = Date.now();
  const model = document.getElementById('model-select').value;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message: text, model })
    });

    typing.classList.remove('active');

    const div = document.createElement('div');
    div.className = 'msg assistant';
    div.innerHTML = '<div class="msg-label">// JARVIS</div><div class="msg-bubble" id="streaming-bubble"></div>';
    messages.appendChild(div);

    const bubble = document.getElementById('streaming-bubble');
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let full = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      full += decoder.decode(value);
      bubble.textContent = full;
      bubble.id = '';
      messages.scrollTop = messages.scrollHeight;
    }

    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    document.getElementById('resp-time').textContent = elapsed;
    msgCount++;
    document.getElementById('msg-count').textContent = msgCount;

  } catch(e) {
    typing.classList.remove('active');
    addMessage('system', '⚠ CONNECTION ERROR — CHECK OLLAMA STATUS');
  }
}
