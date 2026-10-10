/**
 * 1073 // LOGER DARKNET BBS FRONTEND JAVASCRIPT
 */

let allServices = [];
let autoScroll = true;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
  initBBS();
  loadData();
  connectSSE();
});

function initBBS() {
  // 1. CRT Scanlines Toggle
  const crtBtn = document.getElementById('crt-toggle');
  const scanlines = document.querySelector('.scanlines');
  crtBtn.addEventListener('click', () => {
    scanlines.classList.toggle('disabled');
    const isOn = !scanlines.classList.contains('disabled');
    crtBtn.textContent = `[CRT: ${isOn ? 'ON' : 'OFF'}]`;
  });

  // 2. Reset Button
  document.getElementById('reset-all-btn').addEventListener('click', async () => {
    if (!confirm('Reset all custom endpoints and flush darknet buffer to factory defaults?')) return;
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      if (res.ok) {
        await loadData();
      }
    } catch (e) {
      console.error(e);
    }
  });

  // 3. Post New Target Form
  document.getElementById('new-service-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('in-name').value.trim(),
      address: document.getElementById('in-addr').value.trim(),
      port: document.getElementById('in-port').value.trim() || null,
      category: document.getElementById('in-cat').value.trim() || 'User Daemon',
      description: document.getElementById('in-desc').value.trim()
    };
    try {
      const res = await fetch('/api/services', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        document.getElementById('new-service-form').reset();
        await fetchServices();
      } else {
        alert('[x] Failed to register endpoint');
      }
    } catch (err) {
      console.error(err);
    }
  });

  // 4. Board Filter Tabs
  document.querySelectorAll('.filter-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.filter-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      currentFilter = item.dataset.filter;
      renderThreads();
    });
  });

  // 5. Wire Controls
  const scrollBtn = document.getElementById('toggle-scroll');
  scrollBtn.addEventListener('click', () => {
    autoScroll = !autoScroll;
    scrollBtn.textContent = `[Scroll: ${autoScroll ? 'ON' : 'OFF'}]`;
    scrollBtn.style.color = autoScroll ? 'var(--green-matrix)' : 'var(--text-muted)';
  });

  document.getElementById('clear-wire').addEventListener('click', () => {
    document.getElementById('wire-container').innerHTML = '';
  });

  document.getElementById('wire-search').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('.wire-line').forEach(line => {
      const text = line.textContent.toLowerCase();
      line.style.display = text.includes(q) ? 'flex' : 'none';
    });
  });
}

async function loadData() {
  await Promise.all([fetchStats(), fetchServices(), fetchLogs()]);
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('stat-load').textContent = data.cpu_load || '0.24';
    document.getElementById('stat-ram').textContent = `${data.mem_pct}`;
    document.getElementById('stat-uptime').textContent = data.uptime || '15d 10h';
  } catch (err) {
    console.error(err);
  }
}

async function fetchServices() {
  try {
    const res = await fetch('/api/services');
    if (!res.ok) return;
    const data = await res.json();
    allServices = data.services || [];
    renderThreads();
  } catch (err) {
    console.error(err);
  }
}

function renderThreads() {
  const container = document.getElementById('threads-container');
  container.innerHTML = '';

  const filtered = allServices.filter(s => {
    if (currentFilter === 'healthy') return s.status === 'healthy';
    if (currentFilter === 'custom') return s.type === 'custom';
    return true;
  });

  document.getElementById('threads-count').textContent = filtered.length;
  document.getElementById('stat-total').textContent = allServices.length;

  filtered.forEach(s => {
    const thread = document.createElement('div');
    thread.className = 'thread-post';

    const pNo = s.post_no || 1073000;
    const stBadge = `badge-${s.status || 'offline'}`;
    const openLink = s.port ? `<a href="http://${window.location.hostname}:${s.port}" target="_blank" class="action-link">[>>Open Port :${s.port}]</a>` : '';
    const delLink = s.type === 'custom' ? `<button class="action-delete" onclick="deleteService('${s.id}')">[>>Delete Target]</button>` : '';

    thread.innerHTML = `
      <div class="thread-header">
        <span class="thread-title">${escapeHtml(s.name)}</span>
        <span class="thread-postno">No. ${pNo}</span>
        <span class="thread-badge ${stBadge}">${s.status.toUpperCase()}</span>
      </div>
      <div class="thread-body">
        <p class="greentext">>target: ${escapeHtml(s.address)}</p>
        <p class="greentext">>type: ${s.type} | category: ${escapeHtml(s.category)} | ping: ${s.latency_ms || 0.1}ms</p>
        <p class="greentext">>daemon: ${escapeHtml(s.description || 'Active background process')}</p>
      </div>
      <div class="thread-actions">
        ${openLink}
        <a href="#wire" class="action-link" onclick="filterWire('${escapeJs(s.name)}')">[>>Filter Logs]</a>
        ${delLink}
      </div>
    `;

    container.appendChild(thread);
  });
}

function filterWire(name) {
  const searchInput = document.getElementById('wire-search');
  searchInput.value = name;
  searchInput.dispatchEvent(new Event('input'));
}

async function deleteService(id) {
  if (!confirm(`Delete endpoint ${id}?`)) return;
  try {
    const res = await fetch(`/api/services/${id}`, { method: 'DELETE' });
    if (res.ok) {
      await fetchServices();
    }
  } catch (err) {
    console.error(err);
  }
}

async function fetchLogs() {
  try {
    const res = await fetch('/api/logs?limit=35');
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById('wire-container');
    container.innerHTML = '';
    (data.logs || []).forEach(appendWireLine);
    if (autoScroll) container.scrollTop = container.scrollHeight;
  } catch (err) {
    console.error(err);
  }
}

function appendWireLine(log) {
  const container = document.getElementById('wire-container');
  const line = document.createElement('div');
  line.className = 'wire-line';

  const lvlClass = `lvl-${log.level || 'INFO'}`;
  const ts = log.timestamp ? log.timestamp.split(' ')[1] : '00:00:00';
  const pNo = log.post_no ? `>>${log.post_no}` : '>>1073';

  line.innerHTML = `
    <span class="wire-postno">${pNo}</span>
    <span class="wire-ts">[${ts}]</span>
    <span class="wire-lvl ${lvlClass}">[${log.level || 'INFO'}]</span>
    <span class="wire-srv">[${escapeHtml(log.service_name || '')}]</span>
    <span class="wire-msg">> ${escapeHtml(log.message || '')}</span>
  `;

  container.appendChild(line);

  // Buffer cap 250 elements
  if (container.children.length > 250) {
    container.removeChild(container.children[0]);
  }

  if (autoScroll) {
    container.scrollTop = container.scrollHeight;
  }
}

function connectSSE() {
  try {
    const sse = new EventSource('/api/stream');
    sse.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.stats) {
          document.getElementById('stat-load').textContent = data.stats.cpu_load;
          document.getElementById('stat-ram').textContent = `${data.stats.mem_pct}`;
          document.getElementById('wire-tick').textContent = `tick: ${data.stats.timestamp.split(' ')[1]}`;
        }
        if (data.latest_logs && data.latest_logs.length > 0) {
          data.latest_logs.forEach(appendWireLine);
        }
      } catch (err) {
        console.error(err);
      }
    };
  } catch (e) {
    console.warn('SSE fallback to polling');
    setInterval(fetchStats, 3000);
    setInterval(fetchLogs, 3000);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[m]);
}

function escapeJs(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'");
}
