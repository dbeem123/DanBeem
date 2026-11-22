/* Staffing suite menu: one list open at a time; click outside or press Escape to close. */
(function () {
  'use strict';
  const groups = [...document.querySelectorAll('.ltcop-suite-nav.suite-menu .suite-group')];
  if (!groups.length) return;
  const closeAll = (except) => groups.forEach((g) => { if (g !== except) g.open = false; });
  groups.forEach((g) => g.addEventListener('toggle', () => { if (g.open) closeAll(g); }));
  document.addEventListener('click', (e) => { if (!e.target.closest('.suite-group')) closeAll(); });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const open = groups.find((g) => g.open);
    if (open) { open.open = false; open.querySelector('summary').focus(); }
  });
})();
