let sessionId = null;

async function api(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return await res.json();
}

async function apiGet(path) {
  const res = await fetch(path);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return await res.text();
}

function $(id) { return document.getElementById(id); }

function show(id, v) {
  $(id).style.display = v ? '' : 'none';
}

function renderQuestions(questions) {
  const container = $('questions');
  container.innerHTML = '';
  questions.forEach(q => {
    const wrap = document.createElement('div');
    wrap.className = 'q';
    const label = document.createElement('label');
    label.textContent = q.question + (q.required ? '（必填）' : '（可选）');
    label.className = 'q-label';

    let input;
    if (q.input_type === 'select') {
      input = document.createElement('select');
      (q.options || []).forEach(opt => {
        const o = document.createElement('option');
        o.value = opt;
        o.textContent = opt;
        input.appendChild(o);
      });
    } else {
      input = document.createElement('input');
      input.type = (q.input_type === 'number') ? 'number' : 'text';
      if (q.input_type === 'list') {
        input.placeholder = '用逗号分隔，例如：A,B,C';
      }
    }
    input.dataset.key = q.key;
    input.className = 'q-input';

    wrap.appendChild(label);
    wrap.appendChild(input);
    container.appendChild(wrap);
  });
}

function collectAnswers(questions) {
  const answers = {};
  questions.forEach(q => {
    const el = document.querySelector(`[data-key="${q.key}"]`);
    if (!el) return;
    let v = el.value;
    if (q.input_type === 'number') {
      v = (v === '' ? null : Number(v));
    }
    if (q.input_type === 'list') {
      v = v.split(',').map(s => s.trim()).filter(Boolean);
    }
    answers[q.key] = v;
  });
  return answers;
}

function downloadText(filename, text) {
  const blob = new Blob([text], { type: 'application/octet-stream' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function runWorkflow(payload) {
  const data = await api('/api/workflow/run', payload);
  $('logsPreview').textContent = JSON.stringify(data.logs_preview || [], null, 2);
  show('logsCard', true);

  if (data.status === 'need_user_input') {
    show('questionsCard', true);
    show('resultCard', false);
    $('reqPreview').textContent = JSON.stringify(data.teaching_request || {}, null, 2);
    renderQuestions(data.questions || []);
    window.__lastQuestions = data.questions || [];
    return;
  }

  if (data.status === 'ok') {
    show('questionsCard', false);
    show('resultCard', true);
    $('stylePreview').textContent = JSON.stringify(data.style_config || {}, null, 2);
    $('samplesPreview').textContent = JSON.stringify(data.style_samples || [], null, 2);
    $('outlinePreview').textContent = JSON.stringify(data.outline || {}, null, 2);

    window.__lastOutline = data.outline;
    return;
  }

  alert(data.message || '发生错误');
}

async function init() {
  const s = await api('/api/session', {});
  sessionId = s.session_id;
  $('sessionInfo').textContent = `Session: ${sessionId}`;
}

$('btnRun').addEventListener('click', async () => {
  const userText = $('userText').value;
  if (!userText.trim()) {
    alert('请先输入需求');
    return;
  }
  await runWorkflow({ session_id: sessionId, user_text: userText, auto_fill_defaults: $('autoFill').checked });
});

$('btnSubmitAnswers').addEventListener('click', async () => {
  const qs = window.__lastQuestions || [];
  const answers = collectAnswers(qs);
  await runWorkflow({ session_id: sessionId, answers, auto_fill_defaults: false });
});

$('btnUseDefaults').addEventListener('click', async () => {
  await runWorkflow({ session_id: sessionId, auto_fill_defaults: true });
});

$('btnDownloadOutline').addEventListener('click', () => {
  const outline = window.__lastOutline;
  if (!outline) { alert('还没有大纲'); return; }
  downloadText('outline.json', JSON.stringify(outline, null, 2));
});

$('btnDownloadLogs').addEventListener('click', async () => {
  const text = await apiGet(`/api/logs/${sessionId}`);
  downloadText(`${sessionId}.jsonl`, text);
});

init().catch(err => {
  console.error(err);
  alert('初始化失败：' + err.message);
});
