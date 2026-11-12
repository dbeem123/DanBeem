(function () {
  const patterns = [
    /\b(?:\d{1,2}[/-]){1,2}\d{2,4}\b/,
    /\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,?\s+\d{4})?\b/i,
    /\b(?:room|rm\.?|suite|unit)\s*#?\s*[a-z0-9-]+\b/i,
    /\b(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]?\d{4}\b/,
    /\b(?:resident|patient|case|member)?\s*(?:id|number|no\.?|#)\s*[:#-]?\s*[a-z0-9-]{4,}\b/i,
    /\b[A-Z][a-z]{1,30}\s+[A-Z][a-z]{1,30}\b/
  ];
  function looksSensitive(value) { return patterns.some(pattern => pattern.test(value)); }
  function init() {
    const warning = document.getElementById('sensitive-input-warning');
    if (!warning) return;
    document.querySelectorAll('textarea, input[type="text"]')
      .forEach(input => input.addEventListener('input', () => {
        warning.hidden = !looksSensitive(input.value);
        warning.textContent = warning.hidden ? '' : 'Privacy reminder: this may look like a name, date, room, phone, or ID. Use synthetic or invented facts only. This check cannot catch everything.';
      }));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
