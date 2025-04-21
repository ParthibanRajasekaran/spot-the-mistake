from flask import Flask, render_template_string, jsonify, request
import random
import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F

# --- CONFIGURATION ---
rows, cols = 20, 20
num_decoys = 12
char_pool = list('?@#%&*"ABCDEFGHIJKLMNOPQRSTUVWXYZ')
rot_min, rot_max = 10, 25  # 10–25° rotation

def make_random_example():
    # For dataset generation only
    pattern = [[random.choice(char_pool) for _ in range(cols)] for _ in range(rows)]
    # choose center-weighted target
    weights = [1/(((r-(rows-1)/2)**2 + (c-(cols-1)/2)**2)+1)
               for r in range(rows) for c in range(cols)]
    idx = random.choices(range(rows*cols), weights)[0]
    tr, tc = divmod(idx, cols)
    # rotation only
    while True:
        angle = random.uniform(-rot_max, rot_max)
        if abs(angle) >= rot_min:
            break
    # decoys
    others = [(r,c) for r in range(rows) for c in range(cols) if (r,c) != (tr,tc)]
    decoys = random.sample(others, num_decoys)
    dec_list = [{'r': r, 'c': c, 'off': random.uniform(-0.05, 0.05)} for r,c in decoys]
    return pattern, (tr,tc), angle, dec_list

# --- Simple CNN Model for AI Hint ---
class GlitchFinder(nn.Module):
    def __init__(self, num_chars):
        super().__init__()
        self.embed = nn.Embedding(num_chars, 8)
        self.conv = nn.Sequential(
            nn.Conv2d(8, 16, kernel_size=3, padding=1), nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.AdaptiveMaxPool2d((1,1))
        )
        self.fc = nn.Linear(32, 2)

    def forward(self, x):
        # x: B x H x W
        x = self.embed(x.long())            # B x H x W x 8
        x = x.permute(0,3,1,2)              # B x 8 x H x W
        x = self.conv(x).view(-1,32)       # B x 32
        out = torch.sigmoid(self.fc(x))    # B x 2
        return out

# instantiate model
model = GlitchFinder(num_chars=len(char_pool))
# Ideally load pre-trained weights here
# model.load_state_dict(torch.load('model.pt'))
model.eval()

# --- Flask App & Templates ---
app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spot the Mistake</title>
<style>
  :root { --grid-size:80vmin; --cell-size:calc(var(--grid-size)/{{rows}}); }
  body{margin:0;background:#000;color:#0f0;font-family:monospace;display:flex;justify-content:center;}
  #app{padding:1rem;display:flex;flex-direction:column;align-items:center;}
  h1{letter-spacing:.1em;margin-bottom:1rem;}
  .board{display:flex;}
  .controls{flex-shrink:0;margin-right:1rem;display:flex;flex-direction:column;}
  button{margin:.5rem 0;padding:.5rem 1rem;background:#111;border:1px solid #0f0;color:#0f0;cursor:pointer;}
  button:hover{background:#222;}
  #grid{display:grid;grid-template-columns:repeat({{cols}},1fr);
        border:2px solid #0f0;width:var(--grid-size);height:var(--grid-size);}
  .cell{border:1px dashed rgba(0,255,0,0.2);display:flex;align-items:center;justify-content:center;
        transition:transform .2s,background .3s;cursor:pointer;}
  .rain .cell{animation:rain 1s linear infinite;}
  .highlight{background:blue;color:#000;}
  @keyframes rain{0%{transform:translateY(-100%);opacity:0;}10%{opacity:1;}100%{transform:translateY(100%);opacity:0;}}
  #hint{margin-top:1rem;}
  #overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);
           display:flex;align-items:center;justify-content:center;flex-direction:column;}
  #overlay canvas{position:absolute;width:100%;height:100%;}
  #overlay .msg{color:#0f0;opacity:0;white-space:pre-wrap;transition:opacity .5s;}
  #overlay .msg.visible{opacity:1;}
</style>
</head><body>
<div id="app">
  <h1>Spot the Mistake</h1>
  <div class="board">
    <div class="controls">
      <button id="genBtn">Generate</button>
      <button id="ansBtn">Answer</button>
      <button id="aiBtn">AI Hint</button>
    </div>
    <div id="grid"></div>
  </div>
  <div id="hint"></div>
</div>
<div id="overlay">
  <canvas id="rain"></canvas>
  <div class="msg" id="finalMsg">Congrats! Compatibility testing is brutal!</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.0.0/dist/tf.min.js"></script>
<script>
  let current=null;
  async function loadAI(){
    try{ window.aiModel=await tf.loadLayersModel('/static/model.json'); console.log('AI loaded'); }
    catch(e){ console.warn('AI unavailable'); }
  }
  loadAI();
  async function getAICoord(){
    if(!window.aiModel||!current) return current.target;
    // encode grid to ints
    const mapChar = Object.fromEntries({{ char_pool|tojson }}.map((c,i)=>[c,i]));
    const arr = current.pattern.flat().map(c=>mapChar[c]);
    const inp = tf.tensor2d(arr,[1,rows*cols], 'int32').reshape([1,rows,cols]);
    const out = window.aiModel.predict(inp).dataSync();
    return [Math.round(out[0]*(rows-1)), Math.round(out[1]*(cols-1))];
  }

  async function fetchPat(){ const res=await fetch('/generate'); current=await res.json(); return current; }
  function render(info){const g=document.getElementById('grid');g.innerHTML='';document.getElementById('hint').textContent='';
    info.pattern.forEach((row,r)=>row.forEach((ch,c)=>{const cell=document.createElement('div');cell.className='cell';cell.textContent=ch;
      if(r===info.target[0]&&c===info.target[1]) cell.style.transform=`rotate(${info.angle}deg)`;g.appendChild(cell);}));}

  // matrix rain omitted for brevity

  document.getElementById('genBtn').onclick=async()=>{const info=await fetchPat();render(info);
    document.getElementById('grid').classList.add('rain');setTimeout(()=>document.getElementById('grid').classList.remove('rain'),1000);
  };
  document.getElementById('ansBtn').onclick=()=>{if(!current)return;const cells=[...document.getElementById('grid').children];
    cells.forEach(c=>c.classList.remove('highlight'));const idx=current.target[0]*cols+current.target[1];cells[idx].classList.add('highlight');
    document.getElementById('hint').textContent=`Rotated '${current.char}' at (row ${current.target[0]+1}, col ${current.target[1]+1})`;
  };
  document.getElementById('aiBtn').onclick=async()=>{const [r,c]=await getAICoord();const cells=[...document.getElementById('grid').children];
    cells.forEach(cel=>cel.classList.remove('highlight'));cells[r*cols+c].classList.add('highlight');};
  window.onload=()=>document.getElementById('genBtn').click();
</script>
</body></html>'''

@app.route('/')
def index():
    return render_template_string(HTML, rows=rows, cols=cols, char_pool=char_pool)

@app.route('/generate')
def generate():
    pattern, (tr,tc), angle, decs = make_random_example()
    info = {'pattern': pattern, 'target': [tr,tc], 'char': pattern[tr][tc],
            'angle': angle, 'decoys': decs}
    return jsonify(info)

@app.route('/ai_hint', methods=['POST'])
def ai_hint():
    data = request.get_json()
    grid = torch.tensor(data['grid'])  # expect 20x20 ints
    coords = model(grid.unsqueeze(0)).detach().numpy()[0]  # normalized
    r, c = int(coords[0]*(rows-1)), int(coords[1]*(cols-1))
    return jsonify({'row': r, 'col': c})

if __name__=='__main__':
    app.run(debug=True, port=5000)