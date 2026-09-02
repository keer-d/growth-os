/* ============================================================
   GOOGLE-BRIGHT LAYER — motion, ported from Career OS
     HalftoneReveal -> full-page colour print, dots swell under the cursor
     ClickSpark     -> Google-coloured burst wherever you click
     PillNav        -> the sliding pill borrows the active item's colour
   ============================================================ */
(function () {
  var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var COARSE = window.matchMedia && window.matchMedia('(pointer:coarse)').matches;
  var PALETTE = ['#4285f4', '#ea4335', '#f9ab00', '#34a853', '#9334e6', '#e52592', '#12b5cb'];

  /* ---- PillNav: the indicator tracks the active button and borrows its --hue ---- */
  (function () {
    var nav = document.querySelector('.primary-nav');
    var ind = document.getElementById('nav-indicator');
    if (!nav || !ind) return;

    var WATCH = { attributes: true, subtree: true, attributeFilter: ['class'] };
    var mo = null;

    /* place() writes to the indicator, which lives inside the observed subtree.
       Disconnecting first drops the records those writes queue, so the observer
       can never re-trigger itself into a loop. */
    function place() {
      if (mo) mo.disconnect();
      var on = nav.querySelector('button.active');
      if (!on) {
        ind.classList.remove('ready');
      } else {
        var hue = getComputedStyle(on).getPropertyValue('--hue').trim();
        if (hue) ind.style.setProperty('--nav-hue', hue);
        ind.style.width = on.offsetWidth + 'px';
        ind.style.height = on.offsetHeight + 'px';
        ind.style.transform = 'translate(' + on.offsetLeft + 'px,' + on.offsetTop + 'px)';
        ind.classList.add('ready');
      }
      if (mo) mo.observe(nav, WATCH);
    }

    place();
    nav.addEventListener('click', function () { setTimeout(place, 0); });
    window.addEventListener('resize', place);
    /* app.js swaps .active when the route changes */
    mo = new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        if (records[i].target !== ind) { place(); return; }
      }
    });
    mo.observe(nav, WATCH);
  })();

  /* ---- HalftoneReveal: the background is a slow colour halftone print, and the
         dots swell into solid colour around the cursor. Five blobs drift on
         prime-ish periods (97s-179s) so the field never visibly loops. ---- */
  (function () {
    var cv = document.createElement('canvas');
    cv.className = 'halftone';
    cv.setAttribute('aria-hidden', 'true');
    document.body.appendChild(cv);
    var ctx = cv.getContext('2d');
    if (!ctx) return;

    var GAP = 24, BUCKETS = 18, REACH = 250, IDLE = 6000;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = 0, h = 0, cols = 0, rows = 0, maxR = 0, sprites = null, hash = null;
    var mx = -9999, my = -9999, mAim = 0, mCur = 0, mStamp = 0;
    var t0 = null, raf = null, last = 0;

    /* col = index into PALETTE; red is left out — as a background wash it reads
       as an alert rather than a mood */
    var BLOBS = [
      { col: 0, cx: .20, cy: .24, ax: .16, ay: .13, px: 97, py: 131, ph: 0.0, r: .66, amp: .92 },
      { col: 4, cx: .78, cy: .18, ax: .14, ay: .15, px: 113, py: 149, ph: 1.7, r: .60, amp: .86 },
      { col: 5, cx: .86, cy: .72, ax: .15, ay: .12, px: 167, py: 127, ph: 3.1, r: .64, amp: .90 },
      { col: 2, cx: .44, cy: .88, ax: .18, ay: .11, px: 139, py: 101, ph: 4.4, r: .58, amp: .82 },
      { col: 3, cx: .12, cy: .70, ax: .12, ay: .16, px: 151, py: 179, ph: 5.6, r: .62, amp: .88 }
    ];

    /* radius and alpha both ride one level, so every (colour, level) pair is a
       pre-rendered sprite and the hot loop never builds a path or flips alpha */
    function buildSprites() {
      maxR = GAP * 0.62;
      sprites = PALETTE.map(function (col) {
        var arr = [];
        for (var b = 0; b < BUCKETS; b++) {
          var L = (b + 0.5) / BUCKETS;
          /* a power curve keeps the resting print fine-grained; only near the
             cursor do dots grow past the gap and merge into solid colour */
          var r = maxR * (0.055 + 0.945 * Math.pow(L, 1.55));
          var sc = document.createElement('canvas');
          var side = Math.ceil((r * 2 + 2) * dpr);
          sc.width = side; sc.height = side;
          var c2 = sc.getContext('2d');
          c2.scale(dpr, dpr);
          c2.globalAlpha = 0.05 + 0.42 * L;
          c2.fillStyle = col;
          c2.beginPath(); c2.arc(side / dpr / 2, side / dpr / 2, r, 0, 6.2832); c2.fill();
          arr.push({ cv: sc, w: side / dpr, half: side / dpr / 2 });
        }
        return arr;
      });
    }

    function layout() {
      w = window.innerWidth; h = window.innerHeight;
      cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
      cv.style.width = w + 'px'; cv.style.height = h + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cols = Math.ceil(w / GAP) + 1; rows = Math.ceil(h / GAP) + 1;
      hash = new Float32Array(cols * rows);
      for (var i = 0; i < hash.length; i++) { var n = Math.sin(i * 12.9898) * 43758.5453; hash[i] = n - Math.floor(n); }
      buildSprites();
      if (REDUCED) paint(0);
    }

    function paint(t) {
      ctx.clearRect(0, 0, w, h);
      var n = BLOBS.length, bx = [], by = [], br = [], base = Math.min(w, h);
      for (var k = 0; k < n; k++) {
        var B = BLOBS[k];
        bx[k] = (B.cx + B.ax * Math.sin(6.2832 * t / B.px + B.ph)) * w;
        by[k] = (B.cy + B.ay * Math.cos(6.2832 * t / B.py + B.ph)) * h;
        br[k] = B.r * base;
      }
      for (var ry = 0; ry < rows; ry++) {
        var y = ry * GAP;
        for (var cx2 = 0; cx2 < cols; cx2++) {
          var x = cx2 * GAP, sum = 0, best = 0, bestW = 0;
          for (var k2 = 0; k2 < n; k2++) {
            var dx = x - bx[k2], dy = y - by[k2];
            var d = Math.sqrt(dx * dx + dy * dy) / br[k2];
            if (d >= 1) continue;
            var g = 1 - d; g = g * g * BLOBS[k2].amp;
            sum += g;
            if (g > bestW) { bestW = g; best = k2; }
          }
          /* a per-dot jitter dithers the colour boundaries instead of seaming them */
          var amb = sum * 0.55; if (amb > 1) amb = 1;
          var L = 0.05 + amb * 0.34 * (0.78 + hash[ry * cols + cx2] * 0.44);
          if (mCur > 0.01) {
            var mdx = x - mx, mdy = y - my, md = Math.sqrt(mdx * mdx + mdy * mdy);
            if (md < REACH) { var f = 1 - md / REACH; L += f * f * 0.82 * mCur; }
          }
          if (L > 1) L = 1;
          var bk = (L * BUCKETS) | 0; if (bk >= BUCKETS) bk = BUCKETS - 1;
          var sp = sprites[BLOBS[best].col][bk];
          ctx.drawImage(sp.cv, x - sp.half, y - sp.half, sp.w, sp.w);
        }
      }
    }

    function frame(ts) {
      raf = null;
      if (ts - last < 28) { raf = requestAnimationFrame(frame); return; }
      last = ts;
      if (t0 === null) t0 = ts;
      if (mAim > 0 && ts - mStamp > IDLE) mAim = 0;   /* the reveal breathes back out when you stop */
      mCur += (mAim - mCur) * 0.07;
      paint((ts - t0) / 1000);
      raf = requestAnimationFrame(frame);
    }

    if (!COARSE && !REDUCED) {
      window.addEventListener('pointermove', function (e) {
        if (e.pointerType === 'touch') return;
        mx = e.clientX; my = e.clientY; mAim = 1;
        mStamp = (typeof e.timeStamp === 'number' && e.timeStamp > 0) ? e.timeStamp : performance.now();
      }, { passive: true });
      document.addEventListener('mouseleave', function () { mAim = 0; });
    }
    window.addEventListener('resize', layout);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { if (raf) { cancelAnimationFrame(raf); raf = null; } }
      else if (!REDUCED && !raf) { t0 = null; raf = requestAnimationFrame(frame); }
    });

    layout();
    if (!REDUCED) raf = requestAnimationFrame(frame);
  })();

  /* ---- ClickSpark: every click leaves a little Google confetti ---- */
  (function () {
    if (REDUCED) return;
    var cv = document.createElement('canvas');
    cv.className = 'spark-canvas';
    cv.setAttribute('aria-hidden', 'true');
    document.body.appendChild(cv);
    var ctx = cv.getContext('2d');
    if (!ctx) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var sparks = [], raf = null;

    function size() {
      cv.width = window.innerWidth * dpr;
      cv.height = window.innerHeight * dpr;
      cv.style.width = window.innerWidth + 'px';
      cv.style.height = window.innerHeight + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    size();
    window.addEventListener('resize', size);

    function tick() {
      raf = null;
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      var live = 0;
      for (var i = 0; i < sparks.length; i++) {
        var s = sparks[i];
        s.t += 0.055;
        if (s.t >= 1) continue;
        live++;
        var e = 1 - Math.pow(1 - s.t, 3);        // ease-out
        var d0 = 7 + e * s.reach;
        var d1 = d0 + 7 * (1 - s.t);
        ctx.globalAlpha = 1 - s.t;
        ctx.strokeStyle = s.col;
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(s.x + Math.cos(s.a) * d0, s.y + Math.sin(s.a) * d0);
        ctx.lineTo(s.x + Math.cos(s.a) * d1, s.y + Math.sin(s.a) * d1);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      if (live) raf = requestAnimationFrame(tick);
      else sparks.length = 0;
    }

    document.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      var n = 8;
      for (var i = 0; i < n; i++) {
        sparks.push({
          x: e.clientX, y: e.clientY,
          a: (Math.PI * 2 / n) * i + Math.random() * 0.3,
          col: PALETTE[i % PALETTE.length],
          reach: 20 + Math.random() * 12,
          t: 0
        });
      }
      if (sparks.length > 200) sparks.splice(0, sparks.length - 200);
      if (!raf) raf = requestAnimationFrame(tick);
    }, { passive: true });
  })();
})();
