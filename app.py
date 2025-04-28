from flask import Flask, render_template_string, jsonify, url_for
import random

# ───── CONFIG ────────────────────────────────────────────────────────────────
rows, cols      = 15, 15
char_pool       = list('?@#%&*"ABCDEFGHIJKLMNOPQRSTUVWXYZ')
rot_min, rot_max = 10, 35  # degrees

app = Flask(__name__)

# ───── TEMPLATE ───────────────────────────────────────────────────────────────
TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Spot the Glitch</title>

  <!-- Matrix-y font -->
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">

  <style>
    /* ─── Full-screen GIF bg + tint ─────────────────────────────────────────── */
    body {
      margin:0;
      background: url("{{ url_for('static', filename='bg_dark.gif') }}") center/cover no-repeat;
      transition: background-image .5s ease;
    }
    body[data-theme="light"] {
      background: url("{{ url_for('static', filename='bg_light.gif') }}") center/cover no-repeat;
    }
    body::before {
      content:""; position:fixed; inset:0;
      background: rgba(0,0,0,0.6);
      z-index:0; transition: background .5s;
    }
    body[data-theme="light"]::before {
      background: rgba(255,255,255,0.6);
    }
    #app, #overlay { position:relative; z-index:1; }

    /* ─── Theme variables ─────────────────────────────────────────────────── */
    :root {
      --bg: #000; --fg: #0f0;
      --btn-bg: #111; --btn-border: #0f0;
    }
    [data-theme="light"] {
      --bg: #fff; --fg: #000;
      --btn-bg: #eee; --btn-border: #000;
    }

    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      color: var(--fg);
      font-family:'Courier New',monospace;
      display:flex; flex-direction:column; align-items:center;
      transition: color .3s;
    }

    /* ─── Header + Toggle ─────────────────────────────────────────────────── */
    header {
      display:flex; align-items:center; margin:1rem 0;
    }
    header h1 {
      font-size:2.5rem; letter-spacing:.1em;
    }
    .theme-btn {
      width:56px; height:32px; padding:4px;
      background:var(--btn-bg); border:2px solid var(--btn-border);
      border-radius:16px; position:relative; cursor:pointer;
      transition:background .3s,border-color .3s;
      margin-left:1rem;
    }
    .theme-btn .icon {
      width:20px; height:20px; border-radius:50%;
      background:var(--fg); position:absolute; top:4px; left:4px;
      transition:left .3s ease;
    }
    .theme-btn.pressed .icon {
      left: calc(100% - 4px - 20px);
    }

    /* ─── Devices & Labels ─────────────────────────────────────────────────── */
    .devices {
      display:flex; align-items:flex-start; gap:2rem;
    }
    .device-wrapper {
      display:flex; flex-direction:column; align-items:center;
    }
    .device-label {
      font-weight:bold; margin-bottom:.5rem;
    }
    .device {
      --w:320px; --h:calc(var(--w)*(844/390));
      width:var(--w); height:var(--h);
      border:6px solid var(--btn-border);
      border-radius:2rem; background:#111;
      position:relative; overflow:hidden;
    }
    .device.ipad {
      --w:400px; --h:calc(var(--w)*(1024/768));
      border-radius:1rem;
    }
    .device::before {
      content:""; position:absolute; top:8px; left:50%;
      width:40px; height:6px; background:#444;
      border-radius:3px; transform:translateX(-50%);
    }
    [data-theme="light"] .device {
      background:var(--bg)!important;
      border-color:var(--fg)!important;
    }
    [data-theme="light"] .device::before {
      background:#888!important;
    }

    /* ─── Vertical Controls (modern button-64) ─────────────────────────────── */
    .controls-vertical {
      display:flex; flex-direction:column; gap:1rem;
      margin-top:2rem;
    }

    /* hide the old plain buttons if any */
    .controls-vertical button:not(.button-64) {
      display: none;
    }

    /* ─── button-64 base & theme vars ──────────────────────────────────────── */
    :root {
      --btn-grad-dark:  linear-gradient(144deg, #0f0, #0c0 50%, #060);
      --btn-grad-light: linear-gradient(144deg, #fff, #ddd 50%, #fff);
      --btn-shadow-dark: rgba(0,255,0,0.2) 0 15px 30px -5px;
      --btn-shadow-light: rgba(0,0,0,0.2) 0 15px 30px -5px;
    }
    body:not([data-theme="light"]) .button-64 {
      background-image: var(--btn-grad-dark);
      box-shadow: var(--btn-shadow-dark);
      color: #0f0;
    }
    body[data-theme="light"] .button-64 {
      background-image: var(--btn-grad-light);
      box-shadow: var(--btn-shadow-light);
      color: #000;
    }

    /* ─── button-64 core styling ───────────────────────────────────────────── */
    .button-64 {
      font-family: 'Orbitron', sans-serif;
      display: flex; align-items:center; justify-content:center;
      border: none; border-radius:8px; cursor:pointer;
      overflow:hidden; position:relative; min-width:140px;
      padding:0; transition:all .3s ease;
    }
    .button-64 .text {
      display:block; width:100%; padding:16px 24px;
      background-color: rgba(0,0,0,0.8); border-radius:6px;
      transition:background .3s ease; font-size:1rem; line-height:1;
    }
    body[data-theme="light"] .button-64 .text {
      background-color: #fff;
    }
    body[data-theme="light"] .button-64:hover .text {
      background-color: #000;
      color: #fff;
    }
    .button-64:hover .text {
      background: none;
    }
    .button-64:focus {
      outline: none;
    }
    @media (min-width:768px) {
      .button-64 .text {
        font-size:1.25rem; padding:20px 28px;
      }
    }

    /* ─── Grid & Cells ───────────────────────────────────────────────────── */
    .grid {
      position:absolute; top:20px; left:0;
      width:100%; height:calc(100% - 20px);
      display:grid;
      grid-template-columns:repeat({{cols}},1fr);
      grid-template-rows:   repeat({{rows}},1fr);
    }
    .cell {
      display:flex; align-items:center; justify-content:center;
      color:var(--fg);
      font-size:calc(var(--w)/{{cols}}*0.8);
      transition:transform .2s, background .3s;
      cursor:pointer;
    }
    .rain .cell { animation:rain 1s linear infinite; }
    .highlight { background:blue!important; color:black!important; }
    @keyframes rain {
      0%   { transform:translateY(-100%); opacity:0; }
      10%  { opacity:1; }
      100% { transform:translateY(100%); opacity:0; }
    }

    /* ─── Overlay + Matrix Rain ───────────────────────────────────────────── */
    #overlay {
      display:none; position:fixed; inset:0;
      background:rgba(0,0,0,0.85);
      align-items:center; justify-content:center;
      flex-direction:column; z-index:2;
    }
    [data-theme="light"] #overlay {
      background:rgba(255,255,255,0.85);
    }
    #matCanvas {
      position:absolute; inset:0;
    }
    #msg {
      position:relative; z-index:3;
      background:rgba(0,0,0,0.7);
      color:var(--fg);
      padding:2rem; border:2px solid var(--fg);
      border-radius:.5rem; max-width:60%;
      font-size:1.25rem; line-height:1.4;
      opacity:0; transform:scale(0.8);
      transition:opacity .5s, transform .5s;
      text-align:center; margin-top:1rem;
    }
    [data-theme="light"] #msg {
      background:rgba(255,255,255,0.9);
    }
    #msg.visible {
      opacity:1; transform:scale(1);
    }
    #msg p {
      margin-bottom: 1rem;
    }
  </style>
</head>

<body data-theme="">
  <div id="app">
    <header>
      <h1>Spot the Glitch</h1>
      <button id="themeToggle" class="theme-btn" aria-pressed="false">
        <span class="icon"></span>
      </button>
    </header>

    <div class="devices">
      <div class="device-wrapper">
        <div class="device-label">iPad</div>
        <div class="device ipad">
          <div class="grid" id="grid-ipad"></div>
        </div>
      </div>

      <div class="device-wrapper">
        <div class="device-label">iPhone 14 Pro</div>
        <div class="device phone">
          <div class="grid" id="grid-iphone"></div>
        </div>
      </div>

      <div class="controls-vertical">
        <!-- modern button-64 markup -->
        <button id="btnGen" class="button-64" role="button">
          <span class="text">Generate</span>
        </button>
        <button id="btnAns" class="button-64" role="button">
          <span class="text">Answer</span>
        </button>
      </div>
    </div>
  </div>

  <div id="overlay">
    <canvas id="matCanvas"></canvas>
    <button id="themeToggleOverlay" class="theme-btn" aria-pressed="false">
      <span class="icon"></span>
    </button>
    <div id="msg">
      <p>If uncovering one tiny glitch feels impossible, imagine the headache of manually validating every device, OS and browser combination then re-executing your entire suite after every single fix. That’s a monumental drag on every release.</p>
      <p>We have slashed 3 days of grueling manual QA down to under 10 minutes of automation.</p>
      <p>Ready to stop sweating about compatibility and start shipping flawless, lightning-fast deliverables? Chat with our team today @ Big Picture</p>
    </div>
  </div>

  <script>
  document.addEventListener('DOMContentLoaded', () => {
    const char_pool = {{ char_pool|tojson }};
    const rows = {{rows}}, cols = {{cols}};
    let current = null;

    // theme helpers
    function isLight() {
      return document.body.dataset.theme === 'light';
    }
    function applyTheme(light) {
      document.body.dataset.theme = light ? 'light' : '';
      ['themeToggle','themeToggleOverlay'].forEach(id => {
        const btn = document.getElementById(id);
        btn.classList.toggle('pressed', light);
        btn.setAttribute('aria-pressed', light);
      });
    }

    // wire up toggles
    ['themeToggle','themeToggleOverlay'].forEach(id => {
      document.getElementById(id).addEventListener('click', () => {
        const light = !isLight();
        localStorage.setItem('theme', light ? 'light' : '');
        applyTheme(light);
      });
    });

    // init
    applyTheme(localStorage.getItem('theme') === 'light');
    document.getElementById('btnGen').click();

    // fetch pattern
    async function fetchPattern() {
      const res = await fetch('/generate');
      return current = await res.json();
    }

    // draw + glitch
    async function generateGrid() {
      const info = await fetchPattern();
      info.glitchDevice = Math.random() < 0.5 ? 'ipad' : 'iphone';

      ['ipad','iphone'].forEach(dev => {
        const grid = document.getElementById('grid-'+dev);
        grid.innerHTML = '';
        info.pattern.forEach((row, r) =>
          row.forEach((ch, c) => {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.textContent = ch;
            if (dev===info.glitchDevice && r===info.target[0] && c===info.target[1]) {
              cell.style.transform = `rotate(${info.angle.toFixed(1)}deg)`;
            }
            grid.appendChild(cell);
          })
        );
      });

      document.getElementById('overlay').style.display = 'none';
      document.getElementById('msg').classList.remove('visible');
      document.getElementById('btnAns').disabled = false;
    }
    document.getElementById('btnGen').addEventListener('click', generateGrid);

    // answer
    document.getElementById('btnAns').addEventListener('click', () => {
      if (!current) return;
      const dev = current.glitchDevice;
      const cells = document.getElementById('grid-'+dev).children;
      Array.from(cells).forEach(c => c.classList.remove('highlight'));
      const idx = current.target[0]*cols + current.target[1];
      cells[idx].classList.add('highlight');
    });

    // click-to-overlay
    ['ipad','iphone'].forEach(dev => {
      document.getElementById('grid-'+dev).addEventListener('click', e => {
        if (!e.target.classList.contains('cell') || !current) return;
        if (dev !== current.glitchDevice) return;
        const idx = [...e.target.parentNode.children].indexOf(e.target);
        if (idx === current.target[0]*cols + current.target[1]) {
          showOverlay();
        }
      });
    });

    // MATRIX RAIN
    const canvas = document.getElementById('matCanvas'),
          ctx    = canvas.getContext('2d');
    let drops = [], colCount = 0, fontSize = 16;

    function initMatrix() {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
      colCount = Math.floor(canvas.width / fontSize);
      drops    = Array(colCount).fill(0);
    }
    function drawMatrix() {
      const fade = isLight() ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
      ctx.fillStyle = fade; ctx.fillRect(0,0,canvas.width,canvas.height);
      const fg = getComputedStyle(document.documentElement).getPropertyValue('--fg').trim();
      ctx.fillStyle = fg; ctx.font = fontSize + 'px monospace';
      for (let i=0; i<colCount; i++) {
        const txt = char_pool[Math.floor(Math.random()*char_pool.length)];
        const x = i*fontSize, y = drops[i]*fontSize;
        ctx.fillText(txt, x, y);
        drops[i] += 8;
        if (y > canvas.height && Math.random() > .975) drops[i] = 0;
      }
      requestAnimationFrame(drawMatrix);
    }
    function showOverlay() {
      document.getElementById('overlay').style.display = 'flex';
      initMatrix(); drawMatrix();
      setTimeout(() => document.getElementById('msg').classList.add('visible'), 600);
    }
    window.addEventListener('resize', initMatrix);

  });
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(
        TEMPLATE,
        rows=rows,
        cols=cols,
        char_pool=char_pool
    )

@app.route('/generate')
def generate():
    # build 15×15 grid
    pattern = [
      [random.choice(char_pool) for _ in range(cols)]
      for _ in range(rows)
    ]
    # center-bias weights
    weights = [
      1/(((r-(rows-1)/2)**2 + (c-(cols-1)/2)**2)+1)
      for r in range(rows) for c in range(cols)
    ]
    idx = random.choices(range(rows*cols), weights)[0]
    tr, tc = divmod(idx, cols)
    # pick a big enough rotation
    while True:
      angle = random.uniform(-rot_max, rot_max)
      if abs(angle) >= rot_min: break

    return jsonify({
      'pattern': pattern,
      'target':  [tr, tc],
      'char':    pattern[tr][tc],
      'angle':   angle
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)