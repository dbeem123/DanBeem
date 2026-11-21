(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Starfield: slow twinkle plus the odd shooting star. Paused when the tab is hidden.
  const canvas = document.querySelector('.stars');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let stars = [], w = 0, h = 0, dpr = 1, shoot = null, raf = 0;
    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.round(w * h / 5200);
      stars = Array.from({ length: n }, () => ({
        x: Math.random() * w, y: Math.random() * h, r: Math.random() * 1.3 + .2,
        p: Math.random() * Math.PI * 2, s: Math.random() * .8 + .2,
        gold: Math.random() < .12,
      }));
    };
    const frame = (t) => {
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        const a = reduce ? .7 : .35 + .65 * (0.5 + 0.5 * Math.sin(t / 1000 * s.s + s.p));
        ctx.fillStyle = s.gold ? `rgba(244,198,91,${a})` : `rgba(220,235,245,${a * .85})`;
        ctx.beginPath(); ctx.arc(s.x, s.y + (reduce ? 0 : (window.scrollY * s.r * .05) % h), s.r, 0, 6.283); ctx.fill();
      }
      if (!reduce) {
        if (!shoot && Math.random() < .004) shoot = { x: Math.random() * w * .7, y: Math.random() * h * .4, l: 0 };
        if (shoot) {
          shoot.l += 14;
          const g = ctx.createLinearGradient(shoot.x, shoot.y, shoot.x + shoot.l, shoot.y + shoot.l * .45);
          g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(255,240,200,.9)');
          ctx.strokeStyle = g; ctx.lineWidth = 1.6;
          ctx.beginPath(); ctx.moveTo(shoot.x, shoot.y); ctx.lineTo(shoot.x + shoot.l, shoot.y + shoot.l * .45); ctx.stroke();
          if (shoot.l > 260) shoot = null;
        }
        raf = requestAnimationFrame(frame);
      }
    };
    resize();
    window.addEventListener('resize', () => { resize(); if (reduce) frame(0); });
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { cancelAnimationFrame(raf); raf = 0; } else if (!reduce && !raf) raf = requestAnimationFrame(frame);
    });
    frame(0);
  }

  // Hero parallax: the operator drifts toward the pointer.
  const stage = document.querySelector('[data-parallax]');
  if (stage && !reduce) {
    window.addEventListener('pointermove', (e) => {
      const x = (e.clientX / window.innerWidth - .5) * 18;
      const y = (e.clientY / window.innerHeight - .5) * 12;
      stage.style.setProperty('--px', `${x.toFixed(1)}px`);
      stage.style.setProperty('--py', `${y.toFixed(1)}px`);
    }, { passive: true });
  }

  // Sub-page art tilts toward the pointer.
  document.querySelectorAll('.sub-art').forEach((art) => {
    if (reduce) return;
    art.addEventListener('pointermove', (e) => {
      const r = art.getBoundingClientRect();
      art.style.setProperty('--ry', `${((e.clientX - r.left) / r.width - .5) * 12}deg`);
      art.style.setProperty('--rx', `${-((e.clientY - r.top) / r.height - .5) * 8}deg`);
    });
    art.addEventListener('pointerleave', () => { art.style.removeProperty('--ry'); art.style.removeProperty('--rx'); });
  });

  // Crew dial: tabs with arrow-key support.
  const crew = document.querySelector('[data-crew]');
  if (crew) {
    const tabs = [...crew.querySelectorAll('.station')];
    const panel = crew.querySelector('.panel');
    const img = panel.querySelector('.panel-img');
    const title = panel.querySelector('.panel-title');
    const text = panel.querySelector('.panel-text');
    const link = panel.querySelector('.panel-link');
    const ring = crew.querySelector('.dial');
    tabs.forEach((t) => { const i = new Image(); i.src = t.dataset.img; });
    let timer;
    const select = (i, focus) => {
      const t = tabs[i];
      tabs.forEach((x, k) => { x.setAttribute('aria-selected', String(k === i)); x.tabIndex = k === i ? 0 : -1; });
      if (focus) t.focus();
      ring.style.setProperty('--sweep', `${parseFloat(t.style.getPropertyValue('--a')) - 20}deg`);
      panel.classList.add('switching');
      clearTimeout(timer);
      timer = setTimeout(() => {
        img.src = t.dataset.img; img.alt = t.dataset.alt;
        title.textContent = t.dataset.title; text.textContent = t.dataset.text;
        link.href = t.dataset.href; link.textContent = t.dataset.cta;
        panel.classList.remove('switching');
      }, reduce ? 0 : 220);
    };
    tabs.forEach((t, i) => {
      t.tabIndex = i === 0 ? 0 : -1;
      t.addEventListener('click', () => select(i));
      t.addEventListener('keydown', (e) => {
        const n = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
        if (n) { e.preventDefault(); select((i + n + tabs.length) % tabs.length, true); }
        if (e.key === 'Home') { e.preventDefault(); select(0, true); }
        if (e.key === 'End') { e.preventDefault(); select(tabs.length - 1, true); }
      });
    });
    ring.style.setProperty('--sweep', '-110deg');
  }

  // Request -> Deliver track: a comet runs down the line and lights each step.
  document.querySelectorAll('[data-track]').forEach((track) => {
    const items = [...track.children];
    if (reduce || !('IntersectionObserver' in window)) { items.forEach(li => li.classList.add('lit')); return; }
    let interval;
    const cycle = () => {
      items.forEach(li => li.classList.remove('lit'));
      items.forEach((li, k) => setTimeout(() => li.classList.add('lit'), 500 + k * 1150));
    };
    new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { track.classList.add('run'); cycle(); interval = setInterval(cycle, 5200); }
      else { track.classList.remove('run'); clearInterval(interval); }
    }, { threshold: .4 }).observe(track);
  });
})();

// Golden embers rise around the operator.
(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const c = document.querySelector('.embers');
  if (!c) return;
  const ctx = c.getContext('2d');
  let w, h, parts = [], raf = 0, on = true;
  const size = () => { const d = Math.min(devicePixelRatio || 1, 2); w = c.clientWidth; h = c.clientHeight; c.width = w * d; c.height = h * d; ctx.setTransform(d, 0, 0, d, 0, 0); };
  const spawn = () => ({ x: w * (.25 + Math.random() * .5), y: h * (.75 + Math.random() * .3), vx: (Math.random() - .5) * .35, vy: -(.35 + Math.random() * .9), r: Math.random() * 2 + .6, life: 0, max: 160 + Math.random() * 160, hue: Math.random() < .2 ? 'rgba(95,211,230,' : 'rgba(255,214,120,' });
  size(); addEventListener('resize', size);
  for (let i = 0; i < 40; i++) { const p = spawn(); p.life = Math.random() * p.max; parts.push(p); }
  const tick = () => {
    ctx.clearRect(0, 0, w, h);
    for (const p of parts) {
      p.life++; p.x += p.vx + Math.sin((p.life + p.r * 50) / 30) * .25; p.y += p.vy;
      const a = Math.sin(Math.PI * p.life / p.max);
      ctx.fillStyle = p.hue + (a * .9).toFixed(2) + ')';
      ctx.shadowColor = p.hue + '1)'; ctx.shadowBlur = 8;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill();
      if (p.life >= p.max) Object.assign(p, spawn());
    }
    raf = on ? requestAnimationFrame(tick) : 0;
  };
  new IntersectionObserver(([e]) => { on = e.isIntersecting; if (on && !raf) raf = requestAnimationFrame(tick); }).observe(c);
})();
