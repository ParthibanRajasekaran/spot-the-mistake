from flask import Flask, render_template_string, jsonify
import random

# --- CONFIGURATION ---
rows, cols = 20, 20
decoys = 12
char_pool = list('?@#%&*"ABCDEFGHIJKLMNOPQRSTUVWXYZ')
# remove offset, only rotation
rot_min, rot_max = 10, 25     # 10–25° rotation

app = Flask(__name__)

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Spot the Mistake</title>
  <style>
    :root { --grid-size: min(80vmin,80vh); --cell-size: calc(var(--grid-size)/{{rows}}); }
    * { margin:0; padding:0; box-sizing:border-box; }
    body { background:#000; color:#0f0; font-family:'Courier New', monospace; display:flex; justify-content:center; }
    #app { display:flex; flex-direction:column; align-items:center; padding:1rem; }
    header h1 { font-size:2rem; letter-spacing:0.1em; margin-bottom:1rem; }
    .board { display:flex; }
    .controls { display:flex; flex-direction:column; margin-right:1rem; }
    .controls button { margin:0.5rem 0; padding:0.5rem 1rem; background:#111; border:1px solid #0f0;
                       color:#0f0; cursor:pointer; transition:background .2s; }
    .controls button:hover { background:#222; }
    #gridContainer { position:relative; }
    #grid { display:grid; grid-template-columns:repeat({{cols}},1fr);
             border:2px solid #0f0; width:var(--grid-size); height:var(--grid-size); }
    .cell { border:1px dashed rgba(0,255,0,0.2); display:flex; align-items:center;
            justify-content:center; font-size:0.8rem; cursor:pointer; transition:transform .2s, background .3s; }
    .rain .cell { animation:rain 1s linear infinite; }
    .highlight { background: blue; color:#000; }
    @keyframes rain { 0%{transform:translateY(-100%);opacity:0;}10%{opacity:1;}100%{transform:translateY(100%);opacity:0;} }
    #hint { margin-top:1rem; font-size:1rem; }
    #overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%;
               background:rgba(0,0,0,0.95); align-items:center; justify-content:center; }
    #overlay canvas { position:absolute; width:100%; height:100%; }
    #overlay .msg { position:relative; color:#0f0; font-size:1.5rem; white-space:pre-wrap;
                    opacity:0; transition:opacity .5s; }
    #overlay .msg.visible { opacity:1; }
  </style>
</head>
<body>
  <div id="app">
    <header><h1>Spot the Mistake</h1></header>
    <div class="board">
      <div class="controls">
        <button id="btnGen">Generate</button>
        <button id="btnAns">Answer</button>
      </div>
      <div id="gridContainer">
        <div id="grid"></div>
      </div>
    </div>
    <div id="hint"></div>
  </div>
  <div id="overlay">
    <canvas id="matCanvas"></canvas>
    <div class="msg" id="msg">Congrats! Now imagine testing across 20+ configs per release.</div>
  </div>
  <script>
    // Dynamic grid sizing
    function updateGridSize() {
      const size = Math.min(window.innerWidth * 0.8, window.innerHeight * 0.8);
      document.documentElement.style.setProperty('--grid-size', size + 'px');
    }
    window.addEventListener('resize', () => {
      updateGridSize(); initMatrix();
    });
    window.addEventListener('load', () => {
      updateGridSize(); initMatrix(); document.getElementById('btnGen').click();
    });

    // Inject character pool from server
    const char_pool = {{ char_pool | tojson }};
    const rows = {{rows}}, cols = {{cols}};
    let current = null;

    async function fetchPattern() {
      const res = await fetch('/generate');
      current = await res.json();
      return current;
    }

    function render(info) {
      const grid = document.getElementById('grid');
      grid.innerHTML = '';
      document.getElementById('hint').textContent = '';
      document.getElementById('overlay').style.display = 'none';
      document.getElementById('msg').classList.remove('visible');
      const cellSize = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--cell-size'));
      info.pattern.forEach((row, r) => row.forEach((ch, c) => {
        const cell = document.createElement('div');
        cell.className = 'cell';
        cell.textContent = ch;
        // decoy slight shift
        const d = info.decoys.find(x => x.r===r && x.c===c);
        if (d) cell.style.transform = `translateY(${d.off * cellSize}px)`;
        // target glitch always rotation
        if (r===info.target[0] && c===info.target[1]) {
          cell.style.transform = `rotate(${info.angle}deg)`;
        }
        grid.appendChild(cell);
      }));
    }

    // Matrix rain
    const canvas = document.getElementById('matCanvas'), ctx = canvas.getContext('2d');
    let drops = [], colCount=0, fontSize=16, anim;
    function initMatrix(){ canvas.width=window.innerWidth; canvas.height=window.innerHeight;
      colCount=Math.floor(canvas.width/fontSize); drops=Array(colCount).fill(0);
    }
    function drawMatrix(){ ctx.fillStyle='rgba(0,0,0,0.1)'; ctx.fillRect(0,0,canvas.width,canvas.height);
      ctx.fillStyle='#0f0'; ctx.font=fontSize+'px monospace';
      for(let i=0;i<colCount;i++){ const txt=char_pool[Math.floor(Math.random()*char_pool.length)];
        const x=i*fontSize, y=drops[i]*fontSize; ctx.fillText(txt,x,y); drops[i]+=8;
        if(y>canvas.height&&Math.random()>.975) drops[i]=0; }
      anim=requestAnimationFrame(drawMatrix);
    }
    function startMatrix(){initMatrix();drawMatrix();}
    function typeMessage(){ const el=document.getElementById('msg'); el.classList.add('visible');
      const text=el.textContent; el.textContent=''; let i=0; const tick=()=>{if(i<text.length){el.textContent+=text[i++];setTimeout(tick,40);}}; tick(); }

    document.getElementById('btnGen').onclick = async ()=>{ const info=await fetchPattern(); render(info);
      const g=document.getElementById('grid'); g.classList.add('rain'); setTimeout(()=>g.classList.remove('rain'),1000);
    };
    document.getElementById('btnAns').onclick = () => { if(!current) return;
      Array.from(document.getElementById('grid').children).forEach(c=>c.classList.remove('highlight'));
      const idx=current.target[0]*cols+current.target[1]; document.getElementById('grid').children[idx].classList.add('highlight');
      const h=`Rotated '${current.char}' at (row ${current.target[0]+1}, col ${current.target[1]+1}) by ${current.angle.toFixed(1)}°.`;
      document.getElementById('hint').textContent=h;
    };
    document.getElementById('grid').onclick=e=>{ if(!e.target.classList.contains('cell')||!current) return;
      const idx=[...document.getElementById('grid').children].indexOf(e.target);
      const r=Math.floor(idx/cols), c=idx%cols; if(r===current.target[0]&&c===current.target[1]){
        document.getElementById('overlay').style.display='flex'; startMatrix(); setTimeout(typeMessage,800);
      }};
    window.onresize=initMatrix; window.onload=()=>document.getElementById('btnGen').click();
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
    # always rotation only
    while True:
        angle=random.uniform(-rot_max,rot_max)
        if abs(angle)>=rot_min: break
    glitch={'type':'rotate','dx':0,'dy':0,'angle':angle}
    others=[(r,c) for r in range(rows) for c in range(cols) if (r,c)!=(tr,tc)]
    decs=[{'r':r,'c':c,'off':random.uniform(-0.05,0.05)} for r,c in random.sample(others,decoys)]
    info={'pattern':pattern,'target':[tr,tc],'char':pattern[tr][tc],'decoys':decs,**glitch}
    return jsonify(info)

if __name__=='__main__': app.run(debug=True,port=5000)