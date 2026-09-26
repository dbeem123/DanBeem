/* Presentation only: navigation, dossier anchors, and print disclosure state. */
(function () {
  'use strict';
  const nav = document.querySelector('.ltcop-suite-nav');
  if (nav) {
    const links = nav.querySelector('.wrap');
    const toggle = document.createElement('button');
    links.id = 'staffing-navigation-links';
    toggle.type = 'button';
    toggle.className = 'staffing-nav-toggle';
    toggle.textContent = 'Staffing tools menu';
    toggle.setAttribute('aria-controls', links.id);
    toggle.setAttribute('aria-expanded', 'false');
    nav.prepend(toggle);
    nav.classList.add('is-enhanced');
    const setOpen = (open) => {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
    };
    toggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-open')));
    nav.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  function revealTarget(hash, focus) {
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (_) { return; }
    const target = id && document.getElementById(id);
    if (!target) return;
    let ancestor = target.closest('details');
    while (ancestor) {
      ancestor.open = true;
      ancestor = ancestor.parentElement.closest('details');
    }
    if (focus) {
      if (!target.matches('summary, a, button, input, select, textarea, [tabindex]')) {
        target.setAttribute('tabindex', '-1');
      }
      target.focus({ preventScroll: true });
    }
  }
  document.querySelectorAll('.dossier-guide a[href^="#"]').forEach((link) => {
    link.addEventListener('click', () => revealTarget(link.hash, true));
  });
  window.addEventListener('hashchange', () => revealTarget(window.location.hash, true));
  revealTarget(window.location.hash, false);

  // Expand only for printing, then restore the reader's original section choices.
  let printState = null;
  window.addEventListener('beforeprint', () => {
    if (printState) return;
    printState = Array.from(document.querySelectorAll('main details'), (element) => [element, element.open]);
    printState.forEach(([element]) => { element.open = true; });
  });
  window.addEventListener('afterprint', () => {
    if (!printState) return;
    printState.forEach(([element, open]) => { element.open = open; });
    printState = null;
  });
})();
