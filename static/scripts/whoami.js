import { fetchJSON } from './common.js';

function pickBestProvider(providers = []) {
  return providers.find((p) => p.ok && p.data) || null;
}

function appendCell(row, text, className = '') {
  const cell = document.createElement('td');
  cell.textContent = text;
  if (className) {
    cell.className = className;
  }
  row.appendChild(cell);
}

function fillProviderTable(providers = []) {
  const body = document.getElementById('providers-body');
  body.innerHTML = '';
  for (const p of providers) {
    const geo = p.data || {};
    const row = document.createElement('tr');
    appendCell(row, p.provider || '-');
    appendCell(row, p.ok ? 'OK' : 'Fail', p.ok ? 'success' : 'error');
    appendCell(row, geo.country || '-');
    appendCell(row, geo.city || '-');
    appendCell(row, geo.asn || '-');
    appendCell(row, geo.as_org || '-');
    body.appendChild(row);
  }
}

function fillMetaTable(headers = {}) {
  const body = document.getElementById('meta-body');
  body.innerHTML = '';
  const entries = Object.entries(headers);
  if (!entries.length) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 2;
    td.textContent = '无可用代理头（可能未经过 CDN/反向代理）';
    tr.appendChild(td);
    body.appendChild(tr);
    return;
  }

  for (const [key, value] of entries) {
    const tr = document.createElement('tr');
    appendCell(tr, key);
    appendCell(tr, value);
    body.appendChild(tr);
  }
}

async function loadData() {
  const [local, meta] = await Promise.all([
    fetchJSON('/api/local_ip'),
    fetchJSON('/api/request_meta'),
  ]);

  document.getElementById('ipv4').textContent = local.ipv4 || '-';
  document.getElementById('ipv6').textContent = local.ipv6 || '-';
  document.getElementById('client-ip').textContent = meta.client_ip || '-';

  const best = pickBestProvider(local.providers);
  if (best && best.data) {
    const g = best.data;
    document.getElementById('country').textContent = g.country || '-';
    document.getElementById('region-city').textContent = [g.region, g.city].filter(Boolean).join(' / ') || '-';
    document.getElementById('asn').textContent = g.asn || '-';
    document.getElementById('org').textContent = g.as_org || '-';
    document.getElementById('isp').textContent = g.isp || '-';
  }

  fillMetaTable(meta.headers || {});
  fillProviderTable(local.providers || []);
  document.getElementById('last-updated').textContent = `最后刷新：${new Date().toLocaleString()}`;
}

async function init() {
  const refreshBtn = document.getElementById('refresh-btn');
  refreshBtn.addEventListener('click', async () => {
    refreshBtn.disabled = true;
    refreshBtn.textContent = '刷新中...';
    try {
      await loadData();
    } catch (error) {
      console.error(error);
      document.body.insertAdjacentHTML('beforeend', `<p class="error">加载失败：${error.message}</p>`);
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = '刷新检测';
    }
  });

  await refreshBtn.click();
}

document.addEventListener('DOMContentLoaded', () => {
  init().catch((error) => {
    console.error(error);
    document.body.insertAdjacentHTML('beforeend', `<p class="error">初始化失败：${error.message}</p>`);
  });
});
