/* =========================================================
   Первый экран главной: интерактивная «карта изолиний»
   ---------------------------------------------------------
   Линии равного уровня (как на геологических картах месторождений) по полю
   шума Перлина медленно текут; курсор «притягивает» поле — вокруг него линии
   сгущаются в кольца и подсвечиваются; клик / касание пускает волну.

   Экономия: ~30 кадров/с, анимация стоит, пока первый экран не виден или вкладка
   скрыта; при «уменьшении движения» (prefers-reduced-motion) — один статичный кадр.
   Подключается только на главной (templates/index.html).
   ========================================================= */
(() => {
  const hero = document.getElementById("hero");
  const canvas = document.getElementById("hero-canvas");
  if (!hero || !canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------- шум Перлина (3D, improved noise) ---------- */
  const perm = new Uint8Array(512);
  {
    const p = Array.from({ length: 256 }, (_, i) => i);
    let seed = 20100; // постоянный рисунок при каждой загрузке
    for (let i = 255; i > 0; i -= 1) {
      seed = (seed * 16807) % 2147483647;
      const j = seed % (i + 1);
      [p[i], p[j]] = [p[j], p[i]];
    }
    for (let i = 0; i < 512; i += 1) perm[i] = p[i & 255];
  }
  const fade = (t) => t * t * t * (t * (t * 6 - 15) + 10);
  const lerp = (a, b, t) => a + t * (b - a);
  function grad(hash, x, y, z) {
    const h = hash & 15;
    const u = h < 8 ? x : y;
    const v = h < 4 ? y : h === 12 || h === 14 ? x : z;
    return ((h & 1) ? -u : u) + ((h & 2) ? -v : v);
  }
  function noise(x, y, z) {
    const X = Math.floor(x) & 255, Y = Math.floor(y) & 255, Z = Math.floor(z) & 255;
    x -= Math.floor(x); y -= Math.floor(y); z -= Math.floor(z);
    const u = fade(x), v = fade(y), w = fade(z);
    const A = perm[X] + Y, AA = perm[A] + Z, AB = perm[A + 1] + Z;
    const B = perm[X + 1] + Y, BA = perm[B] + Z, BB = perm[B + 1] + Z;
    return lerp(
      lerp(lerp(grad(perm[AA], x, y, z), grad(perm[BA], x - 1, y, z), u),
           lerp(grad(perm[AB], x, y - 1, z), grad(perm[BB], x - 1, y - 1, z), u), v),
      lerp(lerp(grad(perm[AA + 1], x, y, z - 1), grad(perm[BA + 1], x - 1, y, z - 1), u),
           lerp(grad(perm[AB + 1], x, y - 1, z - 1), grad(perm[BB + 1], x - 1, y - 1, z - 1), u), v),
      w,
    );
  }

  /* ---------- поле и уровни ---------- */
  const LEVEL_MIN = -0.8;
  const LEVEL_STEP = 0.075;
  const LEVEL_COUNT = 30;
  const GOLD_EVERY = 5; // каждая пятая линия — золотая, как «главные» изолинии на карте

  let width = 0, height = 0, cell = 10, cols = 0, rows = 0, field = new Float32Array(0);
  const pointer = { x: 0, y: 0, tx: 0, ty: 0, strength: 0, active: false };
  const ripples = [];
  let time = 0;

  function resize() {
    const rect = hero.getBoundingClientRect();
    width = Math.max(1, rect.width);
    height = Math.max(1, rect.height);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cell = width < 640 ? 14 : 10;
    cols = Math.ceil(width / cell) + 1;
    rows = Math.ceil(height / cell) + 1;
    field = new Float32Array(cols * rows);
    if (!pointer.active) {
      pointer.x = pointer.tx = width * 0.72;
      pointer.y = pointer.ty = height * 0.5;
    }
  }

  function sample(t) {
    const radius = Math.min(width, height) * 0.22;
    const r2 = radius * radius;
    const z1 = t * 0.045, z2 = t * 0.07 + 7.3;
    for (let j = 0; j < rows; j += 1) {
      const y = j * cell;
      for (let i = 0; i < cols; i += 1) {
        const x = i * cell;
        let v = noise(x * 0.0017, y * 0.0017, z1) * 0.95 + noise(x * 0.0045 + 31.7, y * 0.0045, z2) * 0.22;
        const dx = x - pointer.x, dy = y - pointer.y;
        const d2 = dx * dx + dy * dy;
        if (pointer.strength > 0.001) v += pointer.strength * 0.85 * Math.exp(-d2 / r2);
        for (const r of ripples) {
          const age = t - r.t0;
          const ring = Math.sqrt((x - r.x) ** 2 + (y - r.y) ** 2) - age * 260;
          v += r.amp * Math.exp(-(ring * ring) / 1600) * Math.exp(-age * 1.1);
        }
        field[j * cols + i] = v;
      }
    }
  }

  // Точка пересечения изолинии с ребром клетки (линейная интерполяция).
  const cross = (level, a, b) => (b === a ? 0.5 : (level - a) / (b - a));

  function draw(t) {
    sample(t);
    ctx.clearRect(0, 0, width, height);
    const paths = Array.from({ length: LEVEL_COUNT }, () => new Path2D());

    for (let j = 0; j < rows - 1; j += 1) {
      for (let i = 0; i < cols - 1; i += 1) {
        const a = field[j * cols + i];           // верх-лево
        const b = field[j * cols + i + 1];       // верх-право
        const c = field[(j + 1) * cols + i + 1]; // низ-право
        const d = field[(j + 1) * cols + i];     // низ-лево
        const lo = Math.min(a, b, c, d), hi = Math.max(a, b, c, d);
        const first = Math.max(0, Math.ceil((lo - LEVEL_MIN) / LEVEL_STEP));
        const last = Math.min(LEVEL_COUNT - 1, Math.floor((hi - LEVEL_MIN) / LEVEL_STEP));
        if (first > last) continue;
        const x0 = i * cell, y0 = j * cell;
        for (let li = first; li <= last; li += 1) {
          const L = LEVEL_MIN + li * LEVEL_STEP;
          const idx = (a > L ? 8 : 0) | (b > L ? 4 : 0) | (c > L ? 2 : 0) | (d > L ? 1 : 0);
          if (idx === 0 || idx === 15) continue;
          const top = [x0 + cell * cross(L, a, b), y0];
          const right = [x0 + cell, y0 + cell * cross(L, b, c)];
          const bottom = [x0 + cell * cross(L, d, c), y0 + cell];
          const left = [x0, y0 + cell * cross(L, a, d)];
          const path = paths[li];
          const seg = (p, q) => { path.moveTo(p[0], p[1]); path.lineTo(q[0], q[1]); };
          switch (idx) {
            case 1: case 14: seg(left, bottom); break;
            case 2: case 13: seg(bottom, right); break;
            case 3: case 12: seg(left, right); break;
            case 4: case 11: seg(top, right); break;
            case 6: case 9: seg(top, bottom); break;
            case 7: case 8: seg(left, top); break;
            case 5: seg(top, right); seg(left, bottom); break;   // седловые клетки
            case 10: seg(left, top); seg(bottom, right); break;
            default: break;
          }
        }
      }
    }

    ctx.lineCap = "round";
    for (let li = 0; li < LEVEL_COUNT; li += 1) {
      const gold = li % GOLD_EVERY === 0;
      ctx.strokeStyle = gold ? "rgba(184, 146, 75, 0.55)" : "rgba(237, 239, 242, 0.11)";
      ctx.lineWidth = gold ? 1.3 : 1;
      ctx.stroke(paths[li]);
    }

    // Подсветка линий у курсора: рисуем только поверх уже нарисованных линий.
    if (pointer.strength > 0.01) {
      const glow = ctx.createRadialGradient(pointer.x, pointer.y, 0, pointer.x, pointer.y, Math.min(width, height) * 0.28);
      glow.addColorStop(0, `rgba(0, 173, 239, ${0.75 * pointer.strength})`);
      glow.addColorStop(1, "rgba(0, 173, 239, 0)");
      ctx.globalCompositeOperation = "source-atop";
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, width, height);
      ctx.globalCompositeOperation = "source-over";
    }
  }

  /* ---------- анимация ---------- */
  let running = false, visible = true, last = 0, frame = 0;

  function tick(now) {
    if (!running) return;
    frame = requestAnimationFrame(tick);
    if (now - last < 33) return; // ~30 кадров/с
    const dt = Math.min(0.1, (now - last) / 1000 || 0.033);
    last = now;
    time += dt;
    pointer.x += (pointer.tx - pointer.x) * 0.1;
    pointer.y += (pointer.ty - pointer.y) * 0.1;
    pointer.strength += ((pointer.active ? 1 : 0.35) - pointer.strength) * 0.05;
    while (ripples.length && time - ripples[0].t0 > 3.5) ripples.shift();
    draw(time);
  }

  function update() {
    const shouldRun = visible && !document.hidden && !reducedMotion.matches;
    if (shouldRun && !running) {
      running = true;
      last = 0;
      frame = requestAnimationFrame(tick);
    } else if (!shouldRun && running) {
      running = false;
      cancelAnimationFrame(frame);
    }
    if (reducedMotion.matches) {
      pointer.strength = 0.35;
      draw(12);
    }
  }

  /* ---------- взаимодействие ---------- */
  function localPoint(event) {
    const rect = hero.getBoundingClientRect();
    return [event.clientX - rect.left, event.clientY - rect.top];
  }
  hero.addEventListener("pointermove", (event) => {
    [pointer.tx, pointer.ty] = localPoint(event);
    pointer.active = true;
  }, { passive: true });
  hero.addEventListener("pointerleave", () => { pointer.active = false; }, { passive: true });
  hero.addEventListener("pointerdown", (event) => {
    if (event.target.closest("a, button")) return;
    const [x, y] = localPoint(event);
    [pointer.tx, pointer.ty] = [x, y];
    pointer.active = true;
    ripples.push({ x, y, t0: time, amp: 0.45 });
    if (ripples.length > 4) ripples.shift();
  }, { passive: true });

  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    update();
  }).observe(hero);
  document.addEventListener("visibilitychange", update);
  reducedMotion.addEventListener("change", update);
  new ResizeObserver(() => {
    resize();
    if (!running) draw(reducedMotion.matches ? 12 : time);
  }).observe(hero);

  resize();
  draw(0);
  hero.classList.add("hero--animated");
  update();
})();
