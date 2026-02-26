// common.js
// Helper functions shared across pages.

/**
 * Perform a fetch and parse the JSON response with basic error handling.
 * @param {string} url
 * @param {Object} [opts]
 * @returns {Promise<any>}
 */
export async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return await res.json();
}

/**
 * Create a DOM element from an HTML string.
 * @param {string} html
 * @returns {Element}
 */
export function createElement(html) {
  const template = document.createElement('template');
  template.innerHTML = html.trim();
  return template.content.firstChild;
}

/**
 * Load a JSON file relative to the `static` directory.
 * @param {string} path
 * @returns {Promise<any>}
 */
export async function loadStaticJSON(path) {
  return fetchJSON(path);
}
