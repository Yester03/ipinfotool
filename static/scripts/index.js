// index.js
// Logic for the Local IP Lookup page.

import { fetchJSON, loadStaticJSON } from './common.js';

/**
 * Render the results from the /api/local_ip endpoint.
 */
async function loadLocalIPInfo() {
  try {
    const data = await fetchJSON('/api/local_ip');
    // Set IP addresses
    document.getElementById('ipv4').textContent = data.ipv4 || 'N/A';
    document.getElementById('ipv6').textContent = data.ipv6 || 'N/A';
    // Populate provider table
    const tbody = document.getElementById('providers-body');
    tbody.innerHTML = '';
    for (const res of data.providers) {
      const tr = document.createElement('tr');
      const status = res.ok ? 'OK' : 'Fail';
      const statusClass = res.ok ? 'success' : 'error';
      const geo = res.data || {};
      tr.innerHTML = `
        <td>${res.provider}</td>
        <td class="${statusClass}">${status}</td>
        <td>${geo.country || '-'}</td>
        <td>${geo.region || '-'}</td>
        <td>${geo.city || '-'}</td>
        <td>${geo.asn || '-'}</td>
        <td>${geo.as_org || '-'}</td>
        <td>${geo.isp || '-'}</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    console.error('Failed to fetch local IP info:', err);
    document.getElementById('ip-info').textContent = 'Failed to load IP information.';
  }
}

/**
 * Run connectivity tests against configured sites.
 */
async function runConnectivityTests() {
  const sites = await loadStaticJSON('/static/sites.json');
  const tbody = document.getElementById('ping-body');
  tbody.innerHTML = '';
  // For each site, start the test but don't block the others.  Use Promise.all
  const tests = sites.map(async (site) => {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${site}</td><td>Testing…</td><td></td>`;
    tbody.appendChild(row);
    const statusCell = row.children[1];
    const rttCell = row.children[2];
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const start = performance.now();
    try {
      // Use no-cors mode so that we don't violate CORS policies.  We cannot read
      // response details but we can measure completion time.
      await fetch(site, { mode: 'no-cors', signal: controller.signal });
      const duration = Math.round(performance.now() - start);
      statusCell.textContent = 'OK';
      statusCell.className = 'success';
      rttCell.textContent = `${duration}`;
    } catch (err) {
      if (err.name === 'AbortError') {
        statusCell.textContent = 'Timeout';
      } else {
        statusCell.textContent = 'Error';
      }
      statusCell.className = 'error';
      rttCell.textContent = '-';
    } finally {
      clearTimeout(timeoutId);
    }
  });
  await Promise.all(tests);
}

/**
 * Toggle visibility of an element by id based on a checkbox.
 */
function setupToggle(checkboxId, elementId) {
  const cb = document.getElementById(checkboxId);
  const el = document.getElementById(elementId);
  cb.addEventListener('change', () => {
    if (cb.checked) {
      el.classList.add('hidden');
    } else {
      el.classList.remove('hidden');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadLocalIPInfo();
  runConnectivityTests();
  setupToggle('toggle-ip', 'ip-info');
  setupToggle('toggle-geo', 'geo-info');
});
