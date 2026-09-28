(() => {
  const page = document.querySelector('.danbeem-page');
  if (!page) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(pointer: fine)');
  const progress = document.querySelector('.danbeem-scroll-progress span');
  const revealItems = [...document.querySelectorAll('[data-reveal]')];
  const cards = [...document.querySelectorAll('.danbeem-card')];

  revealItems[0]?.classList.add('is-visible');
  if ('IntersectionObserver' in window && !reducedMotion.matches) {
    const observer = new IntersectionObserver((entries, instance) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        instance.unobserve(entry.target);
      });
    }, { threshold: 0.14 });
    revealItems.slice(1).forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add('is-visible'));
  }

  const updateProgress = () => {
    if (!progress) return;
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    const percent = scrollable > 0 ? Math.min(100, Math.max(0, (window.scrollY / scrollable) * 100)) : 0;
    progress.style.width = `${percent}%`;
  };
  updateProgress();
  window.addEventListener('scroll', updateProgress, { passive: true });
  window.addEventListener('resize', updateProgress, { passive: true });

  if (finePointer.matches && !reducedMotion.matches) {
    page.addEventListener('pointermove', (event) => {
      const x = (event.clientX / window.innerWidth - 0.5) * 8;
      const y = (event.clientY / window.innerHeight - 0.5) * 5;
      page.style.setProperty('--hero-x', `${x.toFixed(2)}px`);
      page.style.setProperty('--hero-y', `${y.toFixed(2)}px`);
    });
    page.addEventListener('pointerleave', () => {
      page.style.setProperty('--hero-x', '0px');
      page.style.setProperty('--hero-y', '0px');
    });

    cards.forEach((card) => {
      card.addEventListener('pointermove', (event) => {
        const rect = card.getBoundingClientRect();
        card.style.setProperty('--spot-x', `${event.clientX - rect.left}px`);
        card.style.setProperty('--spot-y', `${event.clientY - rect.top}px`);
        card.classList.add('is-spotlit');
      });
      card.addEventListener('pointerleave', () => card.classList.remove('is-spotlit'));
    });
  }
})();
