/**
 * loger (1073) Web Interface
 */

let allServices = [];
let autoScroll = true;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
  initUI();
  loadData();
  connectSSE();
});

function initUI() {
  // Reset Button
  document.getElementById('reset-all-btn').addEventListener('click', async () => {
    if (!confirm('Сбросить добавленные адреса к дефолтным?')) return;
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      if (res.ok) {
        await loadData();
      }
    } catch (e) {
      console.error(e);
    }
  });

  // Add Form
  document.getElementById('new-service-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('in-name').value.trim(),
      address: document.getElementById('in-addr').value.trim(),
      port: document.getElementById('in-port').value.trim() || null,
      category: document.getElementById('in-cat').value.trim() || 'Сервис',
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
        alert('Ошибка при сохранении адреса');
      }
    } catch (err) {
      console.error(err);
    }
  });

  // Filter Tabs
  document.querySelectorAll('.filter-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.filter-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      currentFilter = item.dataset.filter;
      renderThreads();
    });
  });

  // Wire Controls
  const scrollBtn = document.getElementById('toggle-scroll');
  scrollBtn.addEventListener('click', () => {
    autoScroll = !autoScroll;
    scrollBtn.textContent = `[Автопрокрутка: ${autoScroll ? 'ВКЛ' : 'ВЫКЛ'}]`;
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
    document.getElementById('stat-load').textContent = data.cpu_load || '0.20';
    document.getElementById('stat-ram').textContent = `${data.mem_pct}`;
    document.getElementById('stat-uptime').textContent = data.uptime || '--';
    document.getElementById('pinned-date').textContent = data.timestamp || '';
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

    const pNo = s.post_no || 1073;
    const stBadge = `badge-${s.status || 'offline'}`;
    const host = window.location.hostname || '127.0.0.1';
    const openLink = s.port ? `<a href="http://${host}:${s.port}" target="_blank" class="action-link">[Открыть :${s.port}]</a>` : '';
    const delLink = s.type === 'custom' ? `<button class="action-delete" onclick="deleteService('${s.id}')">[Удалить]</button>` : '';

    thread.innerHTML = `
      <div class="thread-header">
        <span class="thread-title">${escapeHtml(s.name)}</span>
        <span class="thread-postno">#${pNo}</span>
        <span class="thread-badge ${stBadge}">${s.status.toUpperCase()}</span>
      </div>
      <div class="thread-body">
        <p class="greentext">>адрес: ${escapeHtml(s.address)}</p>
        <p class="greentext">>тип: ${s.type} | пинг: ${s.latency_ms || 0.1}ms</p>
        <p class="greentext">>инфо: ${escapeHtml(s.description || 'Работает')}</p>
      </div>
      <div class="thread-actions">
        ${openLink}
        <a href="#wire" class="action-link" onclick="filterWire('${escapeJs(s.name)}')">[Логи]</a>
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
  if (!confirm(`Удалить ${id}?`)) return;
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
  const pNo = log.post_no ? `#${log.post_no}` : '';

  line.innerHTML = `
    <span class="wire-postno">${pNo}</span>
    <span class="wire-ts">[${ts}]</span>
    <span class="wire-lvl ${lvlClass}">[${log.level || 'INFO'}]</span>
    <span class="wire-srv">[${escapeHtml(log.service_name || '')}]</span>
    <span class="wire-msg">> ${escapeHtml(log.message || '')}</span>
  `;

  container.appendChild(line);

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
