import { useState, useEffect, useCallback, useRef } from "react";

const ROWS = 20, COLS = 38, CS = 22;
const D = { EMPTY: 0, WALL: 1, VF: 2, VB: 3, PATH: 4 };

class PQ {
  constructor() { this.h = []; }
  push(p, v) {
    this.h.push([p, v]);
    let i = this.h.length - 1;
    while (i > 0) {
      const par = (i - 1) >> 1;
      if (this.h[par][0] <= this.h[i][0]) break;
      [this.h[par], this.h[i]] = [this.h[i], this.h[par]]; i = par;
    }
  }
  pop() {
    const top = this.h[0], last = this.h.pop();
    if (this.h.length) {
      this.h[0] = last; let i = 0;
      while (true) {
        let s=i,l=2*i+1,r=2*i+2;
        if (l<this.h.length&&this.h[l][0]<this.h[s][0]) s=l;
        if (r<this.h.length&&this.h[r][0]<this.h[s][0]) s=r;
        if (s===i) break;
        [this.h[s],this.h[i]]=[this.h[i],this.h[s]]; i=s;
      }
    }
    return top;
  }
  get size() { return this.h.length; }
}

const K=(r,c)=>r*COLS+c, KR=k=>Math.floor(k/COLS), KC=k=>k%COLS;
const DIRS=[[-1,0],[1,0],[0,-1],[0,1]];
const MH=(r1,c1,r2,c2)=>Math.abs(r1-r2)+Math.abs(c1-c2);
function mkPath(prev,ek){const p=[];let c=ek;while(c!==-1&&c!==undefined){p.unshift(c);c=prev[c];}return p;}

function algoDijkstra(walls,sk,ek){
  const dist=new Float32Array(ROWS*COLS).fill(Infinity),prev=new Int32Array(ROWS*COLS).fill(-1),vis=new Uint8Array(ROWS*COLS),pq=new PQ(),steps=[];
  dist[sk]=0;pq.push(0,sk);
  while(pq.size){const[d,k]=pq.pop();if(vis[k])continue;vis[k]=1;steps.push(k);if(k===ek)break;const r=KR(k),c=KC(k);for(const[dr,dc]of DIRS){const nr=r+dr,nc=c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)continue;const nk=K(nr,nc);if(walls[nk]||vis[nk])continue;if(d+1<dist[nk]){dist[nk]=d+1;prev[nk]=k;pq.push(d+1,nk);}}}
  return{steps,path:vis[ek]?mkPath(prev,ek):[]};
}
function algoAStar(walls,sk,ek){
  const er=KR(ek),ec=KC(ek),g=new Float32Array(ROWS*COLS).fill(Infinity),prev=new Int32Array(ROWS*COLS).fill(-1),vis=new Uint8Array(ROWS*COLS),pq=new PQ(),steps=[];
  g[sk]=0;pq.push(MH(KR(sk),KC(sk),er,ec),sk);
  while(pq.size){const[,k]=pq.pop();if(vis[k])continue;vis[k]=1;steps.push(k);if(k===ek)break;const r=KR(k),c=KC(k);for(const[dr,dc]of DIRS){const nr=r+dr,nc=c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)continue;const nk=K(nr,nc);if(walls[nk]||vis[nk])continue;const ng=g[k]+1;if(ng<g[nk]){g[nk]=ng;prev[nk]=k;pq.push(ng+MH(nr,nc,er,ec),nk);}}}
  return{steps,path:vis[ek]?mkPath(prev,ek):[]};
}
function algoBidir(walls,sk,ek){
  const dF=new Float32Array(ROWS*COLS).fill(Infinity),dB=new Float32Array(ROWS*COLS).fill(Infinity),pF=new Int32Array(ROWS*COLS).fill(-1),pB=new Int32Array(ROWS*COLS).fill(-1),vF=new Uint8Array(ROWS*COLS),vB=new Uint8Array(ROWS*COLS),qF=new PQ(),qB=new PQ(),sF=[],sB=[];
  dF[sk]=0;qF.push(0,sk);dB[ek]=0;qB.push(0,ek);let meet=-1,best=Infinity;
  while(qF.size||qB.size){
    if(qF.size){const[d,k]=qF.pop();if(!vF[k]){vF[k]=1;sF.push(k);if(vB[k]&&d+dB[k]<best){best=d+dB[k];meet=k;}const r=KR(k),c=KC(k);for(const[dr,dc]of DIRS){const nr=r+dr,nc=c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)continue;const nk=K(nr,nc);if(walls[nk]||vF[nk])continue;if(d+1<dF[nk]){dF[nk]=d+1;pF[nk]=k;qF.push(d+1,nk);}}}}
    if(qB.size){const[d,k]=qB.pop();if(!vB[k]){vB[k]=1;sB.push(k);if(vF[k]&&dF[k]+d<best){best=dF[k]+d;meet=k;}const r=KR(k),c=KC(k);for(const[dr,dc]of DIRS){const nr=r+dr,nc=c+dc;if(nr<0||nr>=ROWS||nc<0||nc>=COLS)continue;const nk=K(nr,nc);if(walls[nk]||vB[nk])continue;if(d+1<dB[nk]){dB[nk]=d+1;pB[nk]=k;qB.push(d+1,nk);}}}}
    if(meet>=0&&qF.size&&qB.size&&qF.h[0][0]+qB.h[0][0]>=best)break;
  }
  let path=[];
  if(meet>=0){const fwd=mkPath(pF,meet);const bwd=[];let c=pB[meet];while(c!==-1){bwd.push(c);c=pB[c];}path=[...fwd,...bwd];}
  const ml=Math.max(sF.length,sB.length),steps=[];
  for(let i=0;i<ml;i++){if(i<sF.length)steps.push({k:sF[i],dir:'F'});if(i<sB.length)steps.push({k:sB[i],dir:'B'});}
  return{steps,path};
}

function genCity(){const w=new Uint8Array(ROWS*COLS);for(let r=0;r<ROWS;r++)for(let c=0;c<COLS;c++){const road=(r%5<2)||(c%6<2);if(!road&&Math.random()>0.2)w[K(r,c)]=1;}return w;}
function genMaze(){const w=new Uint8Array(ROWS*COLS).fill(1),vis=new Uint8Array(ROWS*COLS);function carve(r,c){vis[K(r,c)]=1;w[K(r,c)]=0;const dirs=[[0,2],[0,-2],[2,0],[-2,0]].sort(()=>Math.random()-.5);for(const[dr,dc]of dirs){const nr=r+dr,nc=c+dc;if(nr>0&&nr<ROWS-1&&nc>0&&nc<COLS-1&&!vis[K(nr,nc)]){w[K(r+dr/2,c+dc/2)]=0;carve(nr,nc);}}}carve(1,1);return w;}

function drawCanvas(ctx, walls, display, start, end) {
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, COLS*CS, ROWS*CS);

  for (let r=0; r<ROWS; r++) {
    for (let c=0; c<COLS; c++) {
      const k=K(r,c), isSt=start[0]===r&&start[1]===c, isEn=end[0]===r&&end[1]===c, dv=display[k];
      let color=null;
      if      (isSt)        color='#16a34a';
      else if (isEn)        color='#dc2626';
      else if (dv===D.PATH) color='#f59e0b';
      else if (dv===D.VF)   color='#bfdbfe';
      else if (dv===D.VB)   color='#ddd6fe';
      else if (walls[k])    color='#334155';
      if (color) { ctx.fillStyle=color; ctx.fillRect(c*CS+1,r*CS+1,CS-2,CS-2); }
    }
  }
  ctx.strokeStyle='#f1f5f9'; ctx.lineWidth=0.5;
  for(let r=0;r<=ROWS;r++){ctx.beginPath();ctx.moveTo(0,r*CS);ctx.lineTo(COLS*CS,r*CS);ctx.stroke();}
  for(let c=0;c<=COLS;c++){ctx.beginPath();ctx.moveTo(c*CS,0);ctx.lineTo(c*CS,ROWS*CS);ctx.stroke();}
  const[sr,sc]=start,[er,ec]=end;
  ctx.font='bold 11px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#fff';
  ctx.fillText('S',sc*CS+CS/2,sr*CS+CS/2);ctx.fillText('E',ec*CS+CS/2,er*CS+CS/2);
}

const ALGO_DESC = {
  'Dijkstra':               'Explores all nodes in order of cost. Always finds the shortest path. Complexity: O((V+E) log V).',
  'A*':                     'Guides the search with a heuristic (Manhattan distance). Finds the same optimal path but visits far fewer nodes.',
  'Bidirectional Dijkstra': 'Runs two searches at once — from start and from end. They meet in the middle, roughly halving the work.',
};

export default function App() {
  const canvasRef=useRef(null), wallsRef=useRef(new Uint8Array(ROWS*COLS)), displayRef=useRef(new Uint8Array(ROWS*COLS));
  const startRef=useRef([2,2]), endRef=useRef([ROWS-3,COLS-3]), mouseDownRef=useRef(false), timerRef=useRef(null), runningRef=useRef(false);
  const [mode,setMode]=useState('wall'), [algo,setAlgo]=useState('A*'), [speed,setSpeed]=useState('Normal');
  const [running,setRunning]=useState(false), [stats,setStats]=useState({visited:0,pathLen:0,time:0,status:'idle'});

  const redraw=useCallback(()=>{const c=canvasRef.current;if(c)drawCanvas(c.getContext('2d'),wallsRef.current,displayRef.current,startRef.current,endRef.current);},[]);
  useEffect(()=>{redraw();},[redraw]);

  const interact=useCallback((r,c)=>{
    if(runningRef.current)return;
    const k=K(r,c);
    if(mode==='start'){startRef.current=[r,c];setMode('wall');}
    else if(mode==='end'){endRef.current=[r,c];setMode('wall');}
    else if(mode==='wall'){const[sr,sc]=startRef.current,[er,ec]=endRef.current;if((r===sr&&c===sc)||(r===er&&c===ec))return;wallsRef.current[k]=1;}
    else if(mode==='erase'){wallsRef.current[k]=0;}
    redraw();
  },[mode,redraw]);

  const getCell=useCallback((e)=>{const canvas=canvasRef.current,rect=canvas.getBoundingClientRect(),sx=canvas.width/rect.width,sy=canvas.height/rect.height;const c=Math.floor((e.clientX-rect.left)*sx/CS),r=Math.floor((e.clientY-rect.top)*sy/CS);return(r>=0&&r<ROWS&&c>=0&&c<COLS)?[r,c]:null;},[]);
  const onMouseDown=useCallback((e)=>{mouseDownRef.current=true;const p=getCell(e);if(p)interact(...p);},[getCell,interact]);
  const onMouseMove=useCallback((e)=>{if(!mouseDownRef.current||!(mode==='wall'||mode==='erase'))return;const p=getCell(e);if(p)interact(...p);},[getCell,interact,mode]);
  const onMouseUp=useCallback(()=>{mouseDownRef.current=false;},[]);

  const stopAnim=useCallback(()=>{clearTimeout(timerRef.current);runningRef.current=false;setRunning(false);},[]);

  const run=useCallback(()=>{
    if(runningRef.current)return;
    displayRef.current=new Uint8Array(ROWS*COLS);redraw();
    runningRef.current=true;setRunning(true);setStats(s=>({...s,visited:0,pathLen:0,time:0,status:'running'}));
    const sk=K(...startRef.current),ek=K(...endRef.current),t0=performance.now();
    let result;
    if(algo==='Dijkstra')result=algoDijkstra(wallsRef.current,sk,ek);
    else if(algo==='A*')result=algoAStar(wallsRef.current,sk,ek);
    else result=algoBidir(wallsRef.current,sk,ek);
    const tAlgo=performance.now()-t0,{steps,path}=result;
    const CFG={Slow:{delay:30,batch:1},Normal:{delay:8,batch:4},Fast:{delay:1,batch:40}};
    const{delay,batch}=CFG[speed];let i=0;
    function tick(){
      if(!runningRef.current)return;
      if(i>=steps.length){for(const pk of path)displayRef.current[pk]=D.PATH;redraw();setStats({visited:steps.length,pathLen:path.length,time:Math.round(tAlgo*100)/100,status:path.length?'found':'no_path'});runningRef.current=false;setRunning(false);return;}
      for(let b=0;b<batch&&i<steps.length;b++,i++){const s=steps[i];if(typeof s==='number')displayRef.current[s]=D.VF;else displayRef.current[s.k]=s.dir==='F'?D.VF:D.VB;}
      redraw();timerRef.current=setTimeout(tick,delay);
    }
    tick();
  },[algo,speed,redraw]);

  const clearPath=useCallback(()=>{stopAnim();displayRef.current=new Uint8Array(ROWS*COLS);setStats({visited:0,pathLen:0,time:0,status:'idle'});redraw();},[stopAnim,redraw]);
  const clearAll=useCallback(()=>{stopAnim();wallsRef.current=new Uint8Array(ROWS*COLS);displayRef.current=new Uint8Array(ROWS*COLS);setStats({visited:0,pathLen:0,time:0,status:'idle'});redraw();},[stopAnim,redraw]);
  const loadCity=useCallback(()=>{stopAnim();wallsRef.current=genCity();displayRef.current=new Uint8Array(ROWS*COLS);setStats({visited:0,pathLen:0,time:0,status:'idle'});redraw();},[stopAnim,redraw]);
  const loadMaze=useCallback(()=>{stopAnim();wallsRef.current=genMaze();displayRef.current=new Uint8Array(ROWS*COLS);startRef.current=[1,1];endRef.current=[ROWS-2,COLS%2===0?COLS-2:COLS-3];setStats({visited:0,pathLen:0,time:0,status:'idle'});redraw();},[stopAnim,redraw]);
  useEffect(()=>()=>stopAnim(),[stopAnim]);

  // shared styles
  const card = { background:'#fff', border:'1px solid #e2e8f0', borderRadius:10, padding:'14px 16px' };
  const sectionLabel = { fontSize:11, fontWeight:600, color:'#94a3b8', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:10, display:'block' };

  const ToolBtn = ({label, onClick, active, color='#2563eb'}) => (
    <button onClick={onClick} style={{
      padding:'5px 13px', fontSize:13, borderRadius:6, fontFamily:'inherit',
      border:`1.5px solid ${active ? color : '#e2e8f0'}`,
      background: active ? `${color}10` : '#fff',
      color: active ? color : '#64748b',
      cursor:'pointer', fontWeight: active?600:400,
    }}>{label}</button>
  );

  const AlgoBtn = ({label, sub}) => (
    <button onClick={()=>setAlgo(label)} style={{
      textAlign:'left', padding:'9px 11px', borderRadius:7, fontFamily:'inherit',
      border:`1.5px solid ${algo===label?'#2563eb':'#e2e8f0'}`,
      background: algo===label ? '#eff6ff' : '#fff',
      color: algo===label ? '#1d4ed8' : '#374151',
      cursor:'pointer', width:'100%', marginBottom:5,
    }}>
      <div style={{ fontSize:13, fontWeight:algo===label?600:400 }}>{label}</div>
    </button>
  );

  const SpeedBtn = ({label}) => (
    <button onClick={()=>setSpeed(label)} style={{
      flex:1, padding:'6px 0', fontSize:12, borderRadius:6, fontFamily:'inherit',
      border:`1.5px solid ${speed===label?'#2563eb':'#e2e8f0'}`,
      background: speed===label?'#eff6ff':'#fff',
      color: speed===label?'#1d4ed8':'#64748b',
      cursor:'pointer', fontWeight: speed===label?600:400,
    }}>{label}</button>
  );

  const badgeStyle = running
    ? { bg:'#fef9c3', color:'#92400e', text:'Running…' }
    : stats.status==='found'
    ? { bg:'#dcfce7', color:'#15803d', text:`Found — ${stats.pathLen-2} steps` }
    : stats.status==='no_path'
    ? { bg:'#fee2e2', color:'#b91c1c', text:'No path found' }
    : { bg:'#f1f5f9', color:'#64748b', text:'Ready' };

  return (
    <div style={{ fontFamily:"'DM Sans',system-ui,sans-serif", background:'#f8fafc', minHeight:'100vh', padding:'22px 24px', color:'#1e293b' }} onMouseUp={onMouseUp}>

      {/* Header */}
      <div style={{ marginBottom:18 }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <h1 style={{ margin:0, fontSize:22, fontWeight:700, color:'#0f172a' }}>Pathfinding Visualizer</h1>
          <span style={{ fontSize:12, background:'#eff6ff', color:'#3b82f6', padding:'2px 10px', borderRadius:99, fontWeight:500 }}>CS Project</span>
        </div>
        <p style={{ margin:'5px 0 0', fontSize:13, color:'#94a3b8' }}>Visualizing Dijkstra, A*, and Bidirectional Dijkstra on a grid graph</p>
      </div>

      <div style={{ display:'flex', gap:20, alignItems:'flex-start', flexWrap:'wrap' }}>

        {/* Grid column */}
        <div style={{ flex:'1 1 auto', minWidth:300 }}>

          {/* Toolbar */}
          <div style={{ display:'flex', gap:6, marginBottom:10, flexWrap:'wrap', alignItems:'center' }}>
            <span style={{ fontSize:12, color:'#cbd5e1', marginRight:2 }}>Mode:</span>
            <ToolBtn label="Wall"  onClick={()=>setMode('wall')}  active={mode==='wall'}/>
            <ToolBtn label="Erase" onClick={()=>setMode('erase')} active={mode==='erase'}/>
            <ToolBtn label="Start" onClick={()=>setMode('start')} active={mode==='start'} color="#16a34a"/>
            <ToolBtn label="End"   onClick={()=>setMode('end')}   active={mode==='end'}   color="#dc2626"/>
            <div style={{flex:1}}/>
            <ToolBtn label="City"  onClick={loadCity} active={false}/>
            <ToolBtn label="Maze"  onClick={loadMaze} active={false}/>
            <ToolBtn label="Clear" onClick={clearAll} active={false}/>
          </div>

          {/* Canvas */}
          <div style={{ borderRadius:10, overflow:'hidden', border:'1px solid #e2e8f0', display:'inline-block', maxWidth:'100%' }}>
            <canvas ref={canvasRef} width={COLS*CS} height={ROWS*CS}
              style={{ display:'block', maxWidth:'100%', cursor:mode==='wall'?'crosshair':mode==='erase'?'cell':'copy' }}
              onMouseDown={onMouseDown} onMouseMove={onMouseMove}
            />
          </div>

          {/* Legend */}
          <div style={{ display:'flex', gap:16, marginTop:12, flexWrap:'wrap' }}>
            {[['#16a34a','Start'],['#dc2626','End'],['#334155','Wall'],['#bfdbfe','Visited (fwd)'],['#ddd6fe','Visited (bwd)'],['#f59e0b','Path']].map(([color,label])=>(
              <div key={label} style={{ display:'flex', alignItems:'center', gap:6 }}>
                <div style={{ width:13, height:13, background:color, borderRadius:3, border:'1px solid #e2e8f0' }}/>
                <span style={{ fontSize:12, color:'#94a3b8' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Side panel */}
        <div style={{ width:215, flexShrink:0, display:'flex', flexDirection:'column', gap:12 }}>

          {/* Algorithm picker */}
          <div style={card}>
            <span style={sectionLabel}>Algorithm</span>
            <AlgoBtn label="Dijkstra"/>
            <AlgoBtn label="A*"/>
            <AlgoBtn label="Bidirectional Dijkstra"/>
          </div>

          {/* Speed */}
          <div style={card}>
            <span style={sectionLabel}>Speed</span>
            <div style={{ display:'flex', gap:6 }}>
              <SpeedBtn label="Slow"/> <SpeedBtn label="Normal"/> <SpeedBtn label="Fast"/>
            </div>
          </div>

          {/* Run / Stop */}
          <button onClick={running?stopAnim:run} style={{
            padding:'10px', fontSize:14, fontWeight:600, borderRadius:8, fontFamily:'inherit',
            border:'none', background:running?'#dc2626':'#2563eb', color:'#fff', cursor:'pointer',
          }}>
            {running ? '⏹  Stop' : '▶  Run'}
          </button>
          <button onClick={clearPath} style={{
            padding:'7px', fontSize:13, borderRadius:8, fontFamily:'inherit',
            border:'1px solid #e2e8f0', background:'#fff', color:'#64748b', cursor:'pointer',
          }}>Clear path</button>

          {/* Results */}
          <div style={card}>
            <span style={sectionLabel}>Results</span>
            <div style={{ display:'inline-block', padding:'3px 12px', borderRadius:99,
              background:badgeStyle.bg, color:badgeStyle.color, fontSize:12, fontWeight:600, marginBottom:12 }}>
              {badgeStyle.text}
            </div>
            {[['Nodes visited', stats.visited||'—'],['Path length', stats.pathLen||'—'],['Time', stats.time?`${stats.time} ms`:'—']].map(([l,v])=>(
              <div key={l} style={{ display:'flex', justifyContent:'space-between', padding:'5px 0', borderTop:'1px solid #f1f5f9', fontSize:13 }}>
                <span style={{ color:'#94a3b8' }}>{l}</span>
                <span style={{ fontWeight:600, color:'#0f172a' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* About */}
          <div style={card}>
            <span style={sectionLabel}>About</span>
            <p style={{ margin:0, fontSize:12, color:'#64748b', lineHeight:1.65 }}>{ALGO_DESC[algo]}</p>
          </div>

          {/* Tips */}
          <div style={{ background:'#f8fafc', border:'1px solid #e2e8f0', borderRadius:10, padding:'12px 14px' }}>
            <span style={{ fontSize:11, fontWeight:600, color:'#cbd5e1', letterSpacing:'0.08em', textTransform:'uppercase', display:'block', marginBottom:7 }}>How to use</span>
            {['Click + drag to draw walls','Click Start/End to reposition','Try City or Maze presets','Compare visited nodes across algos'].map((t,i)=>(
              <div key={i} style={{ fontSize:12, color:'#94a3b8', lineHeight:1.9 }}>
                <span style={{ color:'#cbd5e1', marginRight:6 }}>{i+1}.</span>{t}
              </div>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}