(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const NS = 'http://www.w3.org/2000/svg';

  // Footer word lights up when it scrolls into view.
  const word = document.querySelector('.footer-word');
  if (word && 'IntersectionObserver' in window) {
    new IntersectionObserver((entries, obs) => {
      if (entries.some(e => e.isIntersecting)) { word.classList.add('lit'); obs.disconnect(); }
    }, { threshold: .4 }).observe(word);
  }

  const board = document.querySelector('[data-board]');
  if (!board) return;
  const svg = board.querySelector('.cables');
  const source = board.querySelector('[data-source]');
  const monitor = board.querySelector('.monitor');
  const img = monitor.querySelector('.monitor-img');
  const title = monitor.querySelector('.monitor-title');
  const desc = monitor.querySelector('.monitor-desc');
  const link = monitor.querySelector('.monitor-link');
  const jacks = [...board.querySelectorAll('.jack-btn')];

  // Preload monitor images so switching is instant.
  jacks.forEach(j => { const i = new Image(); i.src = j.dataset.img; });

  const cables = jacks.map((jack, i) => {
    const color = jack.dataset.color;
    jack.style.setProperty('--c', color);
    const g = document.createElementNS(NS, 'g');
    const sheath = document.createElementNS(NS, 'path');
    sheath.setAttribute('class', 'sheath');
    const wire = document.createElementNS(NS, 'path');
    wire.setAttribute('stroke', color);
    const pulse = document.createElementNS(NS, 'circle');
    pulse.setAttribute('class', 'pulse');
    pulse.setAttribute('r', '4');
    pulse.setAttribute('fill', '#fff');
    pulse.style.color = color;
    g.append(sheath, wire, pulse);
    svg.append(g);
    return { jack, g, sheath, wire, pulse, phase: i * 0.9, t: (i * 0.17) % 1 };
  });

  let active = 0;
  let geom = null;
  const center = (el, box) => {
    const r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2 - box.left, y: r.top + r.height / 2 - box.top };
  };
  const measure = () => {
    const box = board.getBoundingClientRect();
    const vertical = window.matchMedia('(max-width: 860px)').matches;
    geom = {
      vertical,
      s: center(source, box),
      ends: cables.map(c => center(c.jack.querySelector('.jack'), box)),
    };
    svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
  };

  const pathFor = (s, e, vertical, sway) => {
    if (vertical) {
      const dy = e.y - s.y;
      return `M${s.x},${s.y} C${s.x + sway},${s.y + dy * .55} ${e.x - sway * .6},${e.y - dy * .65} ${e.x},${e.y}`;
    }
    const dx = e.x - s.x;
    const sag = 60 + Math.abs(e.y - s.y) * .25;
    return `M${s.x},${s.y} C${s.x + dx * .35},${s.y + sag + sway} ${e.x - dx * .45},${e.y + sag * .6 - sway} ${e.x},${e.y}`;
  };

  const draw = (time) => {
    if (!geom) measure();
    cables.forEach((c, i) => {
      const on = i === active;
      const sway = reduce ? 0 : Math.sin(time / 1300 + c.phase) * (on ? 6 : 12);
      const d = pathFor(geom.s, geom.ends[i], geom.vertical, sway);
      c.sheath.setAttribute('d', d);
      c.wire.setAttribute('d', d);
      c.sheath.setAttribute('stroke-width', on ? 11 : 8);
      c.wire.setAttribute('stroke-width', on ? 6 : 4);
      c.g.style.opacity = on ? 1 : .38;
      if (reduce) { c.pulse.style.display = 'none'; return; }
      c.t = (c.t + (on ? .011 : .003)) % 1;
      const len = c.wire.getTotalLength();
      const p = c.wire.getPointAtLength(c.t * len);
      c.pulse.setAttribute('cx', p.x);
      c.pulse.setAttribute('cy', p.y);
      c.pulse.setAttribute('r', on ? 5 : 3);
    });
  };

  let swapTimer;
  const activate = (i) => {
    if (i === active && title.textContent === jacks[i].dataset.title) return;
    active = i;
    const j = jacks[i];
    jacks.forEach((x, k) => x.classList.toggle('is-active', k === i));
    monitor.style.setProperty('--accent', j.dataset.color);
    monitor.classList.add('switching');
    clearTimeout(swapTimer);
    swapTimer = setTimeout(() => {
      img.src = j.dataset.img;
      title.textContent = j.dataset.title;
      desc.textContent = j.dataset.desc;
      link.href = j.getAttribute('href');
      link.textContent = j.dataset.cta;
      monitor.classList.remove('switching');
    }, reduce ? 0 : 160);
    cables[i].t = 0;
    if (reduce) draw(0);
  };

  let userTouched = false;
  jacks.forEach((j, i) => {
    j.addEventListener('pointerenter', () => { userTouched = true; activate(i); });
    j.addEventListener('focus', () => { userTouched = true; activate(i); });
  });
  activate(0);

  // Attract mode: cycle through the lines until someone touches the board.
  let visible = false;
  if (!reduce) {
    setInterval(() => { if (visible && !userTouched && !document.hidden) activate((active + 1) % jacks.length); }, 4200);
  }

  let raf = 0;
  const loop = (t) => { draw(t); raf = requestAnimationFrame(loop); };
  const start = () => { if (!raf && !reduce) raf = requestAnimationFrame(loop); };
  const stop = () => { cancelAnimationFrame(raf); raf = 0; };
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; visible ? start() : stop(); }).observe(board);
  } else { visible = true; start(); }

  const remeasure = () => { measure(); draw(performance.now()); };
  window.addEventListener('resize', remeasure);
  if (document.fonts) document.fonts.ready.then(remeasure);
  window.addEventListener('load', remeasure);
  remeasure();
})();

// Hero art leans toward the pointer.
(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const art = document.querySelector('[data-tilt]');
  const frame = art && art.querySelector('.hero-frame');
  if (!frame) return;
  art.addEventListener('pointermove', (e) => {
    const r = art.getBoundingClientRect();
    frame.style.setProperty('--ry', `${((e.clientX - r.left) / r.width - .5) * 10}deg`);
    frame.style.setProperty('--rx', `${-((e.clientY - r.top) / r.height - .5) * 7}deg`);
  });
  art.addEventListener('pointerleave', () => { frame.style.removeProperty('--ry'); frame.style.removeProperty('--rx'); });
})();
