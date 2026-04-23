(function () {
  const DEFAULT_PATHS = ['../data/nors_case_level_guidance.json', 'data/nors_case_level_guidance.json'];
  const BATCH5_PATHS = ['../data/nors_knowledge_base_batch5.json', 'data/nors_knowledge_base_batch5.json'];
  const BATCH6_PATHS = ['../data/nors_knowledge_base_batch6.json', 'data/nors_knowledge_base_batch6.json'];
  const BATCH7_PATHS = ['../data/nors_knowledge_base_batch7.json', 'data/nors_knowledge_base_batch7.json'];
  const BATCH8_PATHS = ['../data/nors_knowledge_base_batch8.json', 'data/nors_knowledge_base_batch8.json'];
  const BATCH9_PATHS = ['../data/nors_knowledge_base_batch9.json', 'data/nors_knowledge_base_batch9.json'];
  let guidanceById = {};

  async function loadFirstJson(paths) {
    const errors = [];
    for (const path of paths) {
      try {
        const response = await fetch(path);
        if (!response.ok) {
          errors.push(`${path} returned HTTP ${response.status}`);
          continue;
        }
        return response.json();
      } catch (err) {
        errors.push(`${path}: ${err.message}`);
      }
    }
    throw new Error(errors.join('; '));
  }

  function mergeGuidanceItems(items) {
    items.forEach(item => {
      if (item?.id) guidanceById[item.id] = item;
    });
  }

  function normalizeTooltipRow(row) {
    return {
      id: row.id || row.tooltip_id,
      label: row.term || row.label || row.tooltip_type?.replace(/_/g, ' ') || row.id || row.tooltip_id,
      short_help: row.short_help || row.tooltip_text || '',
      details: row.details || row.authority || '',
      source: 'NORS knowledge base Batch 5'
    };
  }

  async function loadGuidance() {
    try {
      const payload = await loadFirstJson(DEFAULT_PATHS);
      mergeGuidanceItems(payload.items || []);
    } catch (err) {
      console.warn('[nors-help] Case-level guidance could not be loaded:', err.message);
    }

    try {
      const payload = await loadFirstJson(BATCH5_PATHS);
      mergeGuidanceItems((payload.tooltip_rows || []).map(normalizeTooltipRow));
    } catch (err) {
      console.warn('[nors-help] Batch 5 tooltip guidance could not be loaded:', err.message);
    }

    try {
      const payload = await loadFirstJson(BATCH6_PATHS);
      mergeGuidanceItems((payload.tooltip_rows || []).map(row => ({
        ...normalizeTooltipRow(row),
        source: 'NORS knowledge base Batch 6'
      })));
    } catch (err) {
      console.warn('[nors-help] Batch 6 tooltip guidance could not be loaded:', err.message);
    }

    try {
      const payload = await loadFirstJson(BATCH7_PATHS);
      mergeGuidanceItems((payload.tooltip_rows || []).map(row => ({
        ...normalizeTooltipRow(row),
        source: 'NORS knowledge base Batch 7'
      })));
    } catch (err) {
      console.warn('[nors-help] Batch 7 tooltip guidance could not be loaded:', err.message);
    }

    try {
      const payload = await loadFirstJson(BATCH8_PATHS);
      mergeGuidanceItems((payload.tooltip_rows || []).map(row => ({
        ...normalizeTooltipRow(row),
        source: 'NORS knowledge base Batch 8'
      })));
    } catch (err) {
      console.warn('[nors-help] Batch 8 tooltip guidance could not be loaded:', err.message);
    }

    try {
      const payload = await loadFirstJson(BATCH9_PATHS);
      mergeGuidanceItems((payload.tooltip_rows || []).map(row => ({
        ...normalizeTooltipRow(row),
        source: 'NORS knowledge base Batch 9'
      })));
    } catch (err) {
      console.warn('[nors-help] Batch 9 tooltip guidance could not be loaded:', err.message);
    }
  }

  function closeOtherHelpButtons(currentButton) {
    document.querySelectorAll('.help-button[aria-expanded="true"]').forEach(button => {
      if (button !== currentButton) button.setAttribute('aria-expanded', 'false');
    });
  }

  function createHelpButton(item) {
    const button = document.createElement('button');
    const popoverId = `help-popover-${item.id}`;
    button.type = 'button';
    button.className = 'help-button';
    button.setAttribute('aria-label', `${item.label} help`);
    button.setAttribute('aria-describedby', popoverId);
    button.setAttribute('aria-expanded', 'false');
    button.textContent = '?';

    const popover = document.createElement('span');
    popover.id = popoverId;
    popover.className = 'help-popover';
    popover.setAttribute('role', 'tooltip');
    popover.innerHTML = `
      <strong>${escapeHtml(item.label)}</strong>
      <span>${escapeHtml(item.short_help || item.details || '')}</span>
      ${item.details ? `<span>${escapeHtml(item.details)}</span>` : ''}
      <span class="help-source">${escapeHtml(item.source || 'NORS guidance')}</span>
    `;

    button.appendChild(popover);
    button.addEventListener('click', event => {
      event.preventDefault();
      const isOpen = button.getAttribute('aria-expanded') === 'true';
      closeOtherHelpButtons(button);
      button.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
    });

    return button;
  }

  function renderHelpAnchors() {
    document.querySelectorAll('[data-help-id]').forEach(anchor => {
      if (anchor.dataset.helpRendered === 'true') return;
      const item = guidanceById[anchor.dataset.helpId];
      if (!item) return;

      anchor.classList.add('help-anchor');
      anchor.appendChild(createHelpButton(item));
      anchor.dataset.helpRendered = 'true';
    });
  }

  function renderInlineGuidance() {
    document.querySelectorAll('[data-help-inline]').forEach(target => {
      if (target.dataset.helpRendered === 'true') return;
      const item = guidanceById[target.dataset.helpInline];
      if (!item) return;

      target.classList.add('help-inline');
      target.innerHTML = `
        <strong>${escapeHtml(item.label)}:</strong>
        ${escapeHtml(item.short_help || '')}
        ${item.details ? `<span>${escapeHtml(item.details)}</span>` : ''}
      `;
      target.dataset.helpRendered = 'true';
    });
  }

  function escapeHtml(value) {
    return String(value || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  document.addEventListener('click', event => {
    if (!event.target.closest('.help-button')) {
      closeOtherHelpButtons(null);
    }
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeOtherHelpButtons(null);
  });

  document.addEventListener('DOMContentLoaded', async () => {
    await loadGuidance();
    renderHelpAnchors();
    renderInlineGuidance();
  });
})();
