/* Same-origin private result viewer contract. No tokens or public URLs. */
(function () {
  'use strict';
  const ID = /^[A-Za-z0-9][A-Za-z0-9._~-]{0,127}$/;
  const root = document.querySelector('[data-result-viewer]');
  const kind = root && root.dataset.resultViewer;
  const status = document.querySelector('[data-status]');
  const setStatus = (text, bad) => { status.textContent = text; status.className = 'status' + (bad ? ' error' : ''); };
  const safeId = new URLSearchParams(location.search).get('id') || '';
  const api = (suffix) => `/v1/results/${encodeURIComponent(safeId)}/${suffix}`;
  const isProtectedRelative = (value) => {
    try { const u = new URL(value, location.origin); return u.origin === location.origin && u.protocol === location.protocol && u.pathname.startsWith('/v1/results/'); }
    catch (_) { return false; }
  };
  const showMeta = (meta) => {
    document.querySelector('[data-result-id]').textContent = meta.result_id;
    document.querySelector('[data-mime]').textContent = meta.mime;
    document.querySelector('[data-size]').textContent = `${meta.size} bytes`;
  };
  async function load() {
    if (!root || !ID.test(safeId)) { setStatus('This result link is invalid.', true); return; }
    try {
      const response = await fetch(api('metadata'), { credentials: 'same-origin', cache: 'no-store', headers: { Accept: 'application/json' } });
      if (!response.ok) { const messages = {401:'Sign-in is required.',403:'You do not have access to this result.',404:'Result not found.',410:'This result is expired or revoked.'}; throw new Error(messages[response.status] || `Unable to load result (${response.status}).`); }
      const meta = await response.json();
      if (meta.result_id !== safeId || typeof meta.mime !== 'string') throw new Error('The result metadata is invalid.');
      const media = api('media'), download = api('download');
      if (!isProtectedRelative(media) || !isProtectedRelative(download)) throw new Error('Protected media URL validation failed.');
      showMeta(meta);
      const node = document.querySelector('[data-media]'); node.src = media; node.hidden = false;
      document.querySelector('[data-download]').href = download;
      setStatus('Protected result loaded.');
      node.addEventListener('error', () => setStatus('Protected media is unavailable.', true), { once: true });
    } catch (error) { setStatus(error.message || 'Unable to load result.', true); }
  }
  load();
})();
