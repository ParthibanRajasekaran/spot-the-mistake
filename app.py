from flask import Flask, render_template_string, jsonify
import random

rows, cols = 20, 20
decoys = 12
char_pool = list('?@#%&*"ABCDEFGHIJKLMNOPQRSTUVWXYZ')
rot_min, rot_max = 10, 35  # 10–35° rotation

app = Flask(__name__)

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Spot the Mistake</title>
  <style>
    /* Theme variables */
    :root { --bg: #000; --fg: #0f0; --btn-bg: #111; --btn-border: #0f0; }
    [data-theme="light"] { --bg: #fff; --fg: #000; --btn-bg: #eee; --btn-border: #000; }

    :root { --grid-size: min(80vmin,80vh); --cell-size: calc(var(--grid-size)/{{rows}}); }
    * { margin:0; padding:0; box-sizing:border-box; }
    body { background: var(--bg); color: var(--fg); font-family:'Courier New',monospace;
           display:flex; justify-content:center; transition:background .3s, color .3s; }
    #app { display:flex; flex-direction:column; align-items:center; padding:1rem; }
    header { display:flex; align-items:center; justify-content:center; width:100%; margin-bottom:1rem; }
    header h1 { font-size:2rem; letter-spacing:0.1em; }

    /* Theme toggle button now in header */
    .theme-btn { position:relative; margin-left:1rem;
                 width:3rem; height:1.5rem; background:var(--btn-bg);
                 border:1px solid var(--btn-border); border-radius:.75rem;
                 cursor:pointer; display:flex; align-items:center; padding:0 .25rem;
                 transition:background .3s, border-color .3s; }
    .theme-btn .icon { width:1rem; height:1rem; background:var(--fg);
                       border-radius:50%; transition:transform .3s, background .3s; }
    .theme-btn.pressed .icon { transform:translateX(1.5rem); }

    .board { display:flex; }
    .controls { display:flex; flex-direction:column; margin-right:1rem; }
    .controls button { background:var(--btn-bg); border:1px solid var(--btn-border);
                       color:var(--fg); margin:0.5rem 0; padding:0.5rem 1rem;
                       cursor:pointer; transition:background .2s; }
    .controls button:hover { background: var(--btn-border); color: var(--bg); }

    #grid { display:grid; grid-template-columns:repeat({{cols}},1fr);
             border:2px solid var(--fg); width:var(--grid-size); height:var(--grid-size); }
    .cell { display:flex; align-items:center; justify-content:center;
            font-size:0.8rem; cursor:pointer; transition:transform .2s, background .3s; }
    .rain .cell { animation:rain 1s linear infinite; }
    .highlight { background:blue; color:#000; }
    @keyframes rain { 0%{transform:translateY(-100%);opacity:0;}10%{opacity:1;}100%{transform:translateY(100%);opacity:0;} }

    #hint { margin-top:1rem; font-size:1rem; }
    #overlay {
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.85);
      transition: background .3s;
    }
    [data-theme="light"] #overlay { background: rgba(255,255,255,0.85); }

    #overlay canvas { position:absolute; width:100%; height:100%; }
    #overlay .msg { position:relative; color:var(--fg); font-size:1.5rem;
                    max-width:60%; line-height:1.6; white-space:pre-wrap;
                    padding:1rem; background:rgba(0,0,0,0.6);
                    border:1px solid var(--fg); opacity:0; transform:scale(0.8);
                    transition:opacity .5s, transform .5s; text-align:center; }
    [data-theme="light"] #overlay .msg { background:rgba(255,255,255,0.8); color:var(--fg); }
    #overlay .msg p { margin:0.5em 0; }
    #overlay .msg.visible { opacity:1; transform:scale(1); }
  </style>
</head>
<body>
  <div id="app">
    <header>
      <h1>Spot the Mistake</h1>
      <button id="themeToggle" class="theme-btn" aria-pressed="false"><span class="icon"></span></button>
    </header>
    <div class="board">
      <div class="controls">
        <button id="btnGen">Generate</button>
        <button id="btnAns">Answer</button>
      </div>
      <div id="grid"></div>
    </div>
    <div id="hint"></div>
  </div>
  <div id="overlay">
    <button id="themeToggleOverlay" class="theme-btn" aria-pressed="false"><span class="icon"></span></button>
    <canvas id="matCanvas"></canvas>
    <div class="msg" id="msg">
      <p>Just as this tiny glitch was tough to spot, validating compatibility across 20+ configurations every release can be monumental.</p>
      
      <p>We cut 3 days of manual testing down to under 10 minutes of automated checks.</p>
      
      <p>Curious? Talk to our team at Big Picture and see how we delivered flawless, lightning-fast launches!</p>
    </div>
  </div>
  <script>
    const char_pool = {{ char_pool|tojson }};
    const rows = {{rows}}, cols = {{cols}};
    let current = null;

    function applyTheme(isLight) {
      if (isLight) document.documentElement.setAttribute('data-theme','light');
      else document.documentElement.removeAttribute('data-theme');
      ['themeToggle','themeToggleOverlay'].forEach(id => {
        const btn = document.getElementById(id);
        btn.classList.toggle('pressed', isLight);
        btn.setAttribute('aria-pressed', isLight);
      });
    }
    window.addEventListener('load', () => {
      const saved = localStorage.getItem('theme') === 'light';
      applyTheme(saved);
      updateGridSize(); initMatrix(); document.getElementById('btnGen').click();
    });
    ['themeToggle','themeToggleOverlay'].forEach(id => {
      document.getElementById(id).addEventListener('click', () => {
        const isLight = !document.documentElement.hasAttribute('data-theme');
        applyTheme(isLight);
        if (isLight) localStorage.setItem('theme','light');
        else localStorage.removeItem('theme');
      });
    });
    async function fetchPattern() { const res = await fetch('/generate'); current = await res.json(); return current; }
    function render(info) {
      const grid = document.getElementById('grid'); grid.innerHTML = '';
      document.getElementById('hint').textContent = '';
      document.getElementById('overlay').style.display = 'none';
      document.getElementById('msg').classList.remove('visible');
      const cellSize = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--cell-size'));
      info.pattern.forEach((row,r) => row.forEach((ch,c) => {
        const cell = document.createElement('div'); cell.className='cell'; cell.textContent=ch;
        const d = info.decoys.find(x=>x.r===r&&x.c===c);
        if(d) cell.style.transform=`translateY(${d.off*cellSize}px)`;
        if(r===info.target[0]&&c===info.target[1]) cell.style.transform=`rotate(${info.angle.toFixed(1)}deg)`;
        grid.appendChild(cell);
      }));
    }
    const canvas = document.getElementById('matCanvas'), ctx = canvas.getContext('2d');
    let drops=[], colCount=0, fontSize=16, anim;
    function initMatrix(){ canvas.width=window.innerWidth; canvas.height=window.innerHeight; colCount=Math.floor(canvas.width/fontSize); drops=Array(colCount).fill(0); }
    function drawMatrix(){
      const theme = document.documentElement.hasAttribute('data-theme') ? 'light' : 'dark';
      const trail = theme==='light'? 'rgba(255,255,255,0.1)': 'rgba(0,0,0,0.1)';
      ctx.fillStyle = trail; ctx.fillRect(0,0,canvas.width,canvas.height);
      const fg = getComputedStyle(document.documentElement).getPropertyValue('--fg').trim();
      ctx.fillStyle = fg; ctx.font = fontSize+'px monospace';
      for(let i=0;i<colCount;i++){ const txt=char_pool[Math.floor(Math.random()*char_pool.length)]; const x=i*fontSize,y=drops[i]*fontSize; ctx.fillText(txt,x,y); drops[i]+=8; if(y>canvas.height&&Math.random()>.975)drops[i]=0; }
      anim = requestAnimationFrame(drawMatrix);
    }
    function startMatrix(){ initMatrix(); drawMatrix(); }
    function typeMessage(){ const el=document.getElementById('msg'); el.classList.add('visible'); const text=el.textContent; el.textContent=''; let i=0; (function tick(){ if(i<text.length){el.textContent+=text[i++]; setTimeout(tick,40);} })(); }

    document.getElementById('btnGen').onclick=async()=>{const info=await fetchPattern();render(info);document.getElementById('grid').classList.add('rain');setTimeout(()=>document.getElementById('grid').classList.remove('rain'),1000);};
    document.getElementById('btnAns').onclick=()=>{if(!current)return;Array.from(document.getElementById('grid').children).forEach(c=>c.classList.remove('highlight'));const idx=current.target[0]*cols+current.target[1];document.getElementById('grid').children[idx].classList.add('highlight');document.getElementById('hint').textContent=`Rotated '${current.char}' at (row ${current.target[0]+1}, col ${current.target[1]+1}) by ${current.angle.toFixed(1)}°.`;};
    document.getElementById('grid').onclick=e=>{if(!e.target.classList.contains('cell')||!current)return;const idx=[...document.getElementById('grid').children].indexOf(e.target);const r=Math.floor(idx/cols),c=idx%cols;if(r===current.target[0]&&c===current.target[1]){document.getElementById('overlay').style.display='flex';startMatrix();setTimeout(typeMessage,800);}};
    window.onresize=()=>{updateGridSize();initMatrix();};
    function updateGridSize(){const size=Math.min(window.innerWidth*0.8,window.innerHeight*0.8);document.documentElement.style.setProperty('--grid-size',size+'px');}
  </script>
</body>
</html>
'''

@app.route('/')
def index(): return render_template_string(TEMPLATE, rows=rows, cols=cols, char_pool=char_pool)

@app.route('/generate')
def generate():
    pattern=[[random.choice(char_pool) for _ in range(cols)] for _ in range(rows)]
    weights=[1/(((r-(rows-1)/2)**2+(c-(cols-1)/2)**2)+1) for r in range(rows) for c in range(cols)]
    idx=random.choices(range(rows*cols),weights)[0]
    tr,tc=divmod(idx,cols)
    while True:
        angle=random.uniform(-rot_max,rot_max)
        if abs(angle)>=rot_min: break
    glitch={'type':'rotate','angle':angle}
    others=[(r,c) for r in range(rows) for c in range(cols) if (r,c)!=(tr,tc)]
    decs=[{'r':r,'c':c,'off':random.uniform(-0.05,0.05)} for r,c in random.sample(others,decoys)]
    info={'pattern':pattern,'target':[tr,tc],'char':pattern[tr][tc],'decoys':decs,**glitch}
    return jsonify(info)

if __name__=='__main__': app.run(debug=True,port=5000)