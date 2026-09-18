/* DanBot result viewer. Never put secrets or media URLs in SMS or client configuration. */
(() => {
  'use strict';
  const kind = document.body.dataset.resultType;
  const status = document.getElementById('status');
  const result = document.getElementById('result');
  const media = document.getElementById('result-media');
  const title = document.getElementById('result-title');
  const description = document.getElementById('result-description');
  const created = document.getElementById('result-created');
  const download = document.getElementById('download');
  const share = document.getElementById('share');
  const retry = document.getElementById('retry');
  const feedback = document.getElementById('feedback');
  const id = new URLSearchParams(location.search).get('id') || '';
  const allowedMime = kind === 'image'
    ? new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/avif'])
    : new Set(['audio/mpeg', 'audio/mp4', 'audio/wav', 'audio/x-wav', 'audio/ogg', 'audio/webm', 'audio/flac']);

  function showStatus(heading, message, isError = false) {
    result.hidden = true;
    status.hidden = false;
    status.classList.toggle('error', isError);
    status.querySelector('h2').textContent = heading;
    status.querySelector('p').textContent = message;
  }

  function sameOriginUrl(value) {
    if (typeof value !== 'string' || !value || value.startsWith('//')) return null;
    try {
      const url = new URL(value, location.origin);
      if (url.origin !== location.origin || !['https:', 'http:'].includes(url.protocol) || url.username || url.password) return null;
      if (location.protocol === 'https:' && url.protocol !== 'https:') return null;
      return url.href;
    } catch { return null; }
  }

  function render(item) {
    if (!item || item.id !== id || item.type !== kind) throw new Error('Result identity did not match the request.');
    if (item.status === 'queued' || item.status === 'processing') {
      showStatus('Still creating your ' + (kind === 'image' ? 'image' : 'song'), 'This result is not ready yet. You can check again in a little while.');
      retry.hidden = false;
      return;
    }
    if (item.status === 'failed') {
      showStatus('Creation did not finish', 'DanBot could not complete this request. Please check your original message for an update.', true);
      return;
    }
    if (item.status !== 'complete' || !item.media || !allowedMime.has(item.media.mime_type)) throw new Error('Result metadata is incomplete or the file type is unsupported.');
    const fileUrl = sameOriginUrl(item.media.url);
    if (!fileUrl) throw new Error('The result file is not available through the protected media service.');
    const element = document.createElement(kind === 'image' ? 'img' : 'audio');
    element.src = fileUrl;
    if (kind === 'image') {
      element.alt = (typeof item.title === 'string' && item.title ? item.title : 'Generated image').slice(0, 180);
      element.decoding = 'async';
    } else {
      element.controls = true;
      element.preload = 'none';
      element.setAttribute('aria-label', 'Play generated song');
    }
    element.addEventListener('error', () => {
      showStatus('File unavailable', 'The protected result file could not be loaded. Please try again or contact DanBot.', true);
    });
    media.replaceChildren(element);
    title.textContent = (typeof item.title === 'string' && item.title.trim() ? item.title : 'Your ' + kind).slice(0, 180);
    description.textContent = (typeof item.description === 'string' ? item.description : '').slice(0, 1200);
    description.hidden = !description.textContent;
    const date = typeof item.created_at === 'string' ? new Date(item.created_at) : null;
    if (date && !Number.isNaN(date.getTime())) {
      created.dateTime = date.toISOString();
      created.textContent = 'Created ' + date.toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'short'});
      created.hidden = false;
    }
    const downloadUrl = sameOriginUrl(item.media.download_url);
    download.hidden = !downloadUrl;
    if (downloadUrl) download.href = downloadUrl;
    const shareUrl = item.sharing && item.sharing.enabled === true ? sameOriginUrl(item.sharing.url) : null;
    share.hidden = !shareUrl;
    share.onclick = shareUrl ? async () => {
      try {
        await navigator.clipboard.writeText(shareUrl);
        feedback.textContent = 'Share link copied. Only share with someone you intend to give access to.';
      } catch { feedback.textContent = 'Copy is unavailable in this browser.'; }
    } : null;
    status.hidden = true;
    result.hidden = false;
  }

  retry.addEventListener('click', () => location.reload());
  async function load() {
    if (!/^[A-Za-z0-9_-]{16,128}$/.test(id)) {
      showStatus('No result selected', 'Open the unique result link DanBot sent you. Do not enter a phone number or personal information here.', true);
      return;
    }
    showStatus('Loading your result', 'Checking access and retrieving your ' + kind + '…');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      // Requires a same-origin authenticated API and protected media endpoint.
      // GitHub Pages alone cannot implement these endpoints: see results/README.md.
      const response = await fetch('/api/results/' + encodeURIComponent(id), {
        method: 'GET', credentials: 'same-origin', cache: 'no-store', redirect: 'error',
        headers: {Accept: 'application/json'}, signal: controller.signal
      });
      if (response.status === 401) { showStatus('Sign in required', 'Sign in to your authorized DanBot account and reopen this link.', true); return; }
      if (response.status === 403) { showStatus('Access not granted', 'This result is not available to your account.', true); return; }
      if (response.status === 404 || response.status === 410) { showStatus('Result not found', 'This link is invalid, expired, or the result is no longer available.', true); return; }
      if (!response.ok || !(response.headers.get('content-type') || '').toLowerCase().includes('application/json')) throw new Error('The result service is not connected.');
      render(await response.json());
    } catch (error) {
      showStatus('Result service unavailable', 'This page is ready, but the protected DanBot result service is not connected or is temporarily unavailable. No media has been published.', true);
      retry.hidden = false;
    } finally { clearTimeout(timeout); }
  }
  load();
})();