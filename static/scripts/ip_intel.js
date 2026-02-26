// ip_intel.js
// Logic for the IP Intelligence page.

import { fetchJSON } from './common.js';

/**
 * Fetch IP intelligence from the backend, with caching in sessionStorage.
 * @param {string} ip
 * @returns {Promise<any>}
 */
async function fetchIPIntel(ip) {
  const cacheKey = `ip-intel:${ip || 'self'}`;
  const cache = sessionStorage.getItem(cacheKey);
  if (cache) {
    try {
      const { timestamp, data } = JSON.parse(cache);
      // Use cache if within 6 hours
      if (Date.now() - timestamp < 6 * 60 * 60 * 1000) {
        return data;
      }
    } catch {
      // ignore parse errors and fall through
    }
  }
  // Make request (use GET for convenience)
  const url = ip ? `/api/ip_intel?ip=${encodeURIComponent(ip)}` : '/api/ip_intel';
  const data = await fetchJSON(url);
  sessionStorage.setItem(cacheKey, JSON.stringify({ timestamp: Date.now(), data }));
  return data;
}

/**
 * Render results into the table.
 * @param {any} data
 */
function renderResults(data) {
  const table = document.getElementById('intel-table');
  const tbody = document.getElementById('intel-body');
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
  table.style.display = 'table';
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('lookup-form');
  const input = document.getElementById('ip-input');
  const errorDiv = document.getElementById('intel-error');
  form.addEventListener('submit', async (evt) => {
    evt.preventDefault();
    errorDiv.textContent = '';
    const ip = input.value.trim();
    try {
      const data = await fetchIPIntel(ip);
      renderResults(data);
    } catch (err) {
      console.error('Lookup failed:', err);
      errorDiv.textContent = 'Failed to fetch IP intelligence: ' + err.message;
    }
  });
  // Auto‑lookup own IP on page load
  form.dispatchEvent(new Event('submit'));
});
