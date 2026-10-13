// Captures the deck's DOM state at each step (for QA and for the PowerPoint).
// node snap.js deck.html out.json "id:step,id:all,..." | all | steps
// The PowerPoint uses it with "flujo:all,aws:all,poc:0,a2:0" (the architectures and the sequence, one image per click).
const fs=require('fs'); const {JSDOM}=require('jsdom'); const {createCanvas,GlobalFonts}=require('@napi-rs/canvas');
const F='/usr/share/fonts/truetype/crosextra/';
const reg=(f,n)=>{ if(fs.existsSync(f)) GlobalFonts.registerFromPath(f,n); };
reg(F+'Carlito-Regular.ttf','Carlito'); reg(F+'Carlito-Bold.ttf','Carlito');
reg('/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf','Courier New');
reg('/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf','Courier New');
const [,,src,out,spec]=process.argv;
let html=fs.readFileSync(src,'utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'http://localhost/',beforeParse(w){
  w.matchMedia=()=>({matches:false,addListener(){},removeListener(){}});
  w.requestAnimationFrame=()=>0;
  w.HTMLCanvasElement.prototype.getContext=function(){
    if(!this._nc){ const nc=createCanvas(10,10); this._nc=nc; this._ctx=nc.getContext('2d');
      Object.defineProperty(this,'width',{get(){return nc.width},set(v){nc.width=v}});
      Object.defineProperty(this,'height',{get(){return nc.height},set(v){nc.height=v}}); }
    return this._ctx; };
  const dim=(el,k)=>{ const c=el.parentElement; const st=c.getAttribute('style')||''; const g=n=>{const m=st.match(new RegExp(n+':\\s*(-?\\d+)px'));return m?+m[1]:0;};
    return k==='w'?1600-g('left')-g('right'):900-g('top')-g('bottom'); };
  Object.defineProperty(w.HTMLCanvasElement.prototype,'clientWidth',{get(){return dim(this,'w')}});
  Object.defineProperty(w.HTMLCanvasElement.prototype,'clientHeight',{get(){return dim(this,'h')}});
}});
const w=dom.window, d=w.document, D=w.__deck;
if(!D){ console.error('no __deck'); process.exit(1); }
const slides=D.slides;
let req=[];
if(!spec||spec==='all'){ slides.forEach((sl,k)=>req.push([k,D.S[k].n-1])); }
else if(spec==='steps'){ slides.forEach((sl,k)=>{ for(let st=0;st<D.S[k].n;st++) req.push([k,st]); }); }
else spec.split(',').forEach(x=>{ const [id,st]=x.split(':'); const k=slides.findIndex(s=>s.dataset.id===id); if(k<0) throw 'no '+id;
  if(st==='all'){ for(let j=0;j<D.S[k].n;j++) req.push([k,j]); } else req.push([k, st==='last'?D.S[k].n-1:+st]); });
function bake(svg){ // turns the opacity that CSS sets in the browser into attributes
  const stack=svg.closest('.stack'), morphed=stack&&stack.classList.contains('morphed');
  const layB=svg.classList.contains('lay-b'), layA=svg.classList.contains('lay-a');
  svg.querySelectorAll('*').forEach(e=>{
    let o=1; const cl=e.classList;
    if(e.hasAttribute('data-on')&&!cl.contains('vis')) o=0;
    if(e.hasAttribute('data-off')&&cl.contains('gone')) o=0;
    if(cl.contains('dim')) o*=.16; if(cl.contains('soft')) o*=.35; if(cl.contains('hid')) o=0;
    if(e.hasAttribute('data-node')){ if(layB&&!morphed) o=0; if(layA&&morphed) o=0; }
    if(o!==1){ const prev=e.getAttribute('opacity'); e.setAttribute('opacity',String((prev?+prev:1)*o)); }
  });
  if(layB) [...svg.children].forEach(c=>{ if(!c.hasAttribute('data-node')) c.remove(); });
  if(stack){ svg.setAttribute('data-qa-stack','1'); }
}
const pages=[];
for(const [k,st] of req){
  D.show(k); D.setStep(k,st);
  const sl=slides[k], a=D.A[k];
  const clone=sl.cloneNode(true);
  if(a){ D.sizeC(a); a.g.clearRect(0,0,a.W,a.H); a.def.draw(a.g,a.W,a.H,st,1,2.2);
    const url='data:image/png;base64,'+a.cv._nc.toBuffer('image/png').toString('base64');
    const cv=clone.querySelector('canvas.anim'); const img=d.createElement('img'); img.setAttribute('src',url);
    img.setAttribute('style','position:absolute;left:0;top:0;width:100%;height:100%'); cv.replaceWith(img); }
  // bake on the live slide then copy svgs
  const svgs=[];
  const live=[...sl.querySelectorAll('svg')].filter(s=>!s.parentElement.closest('svg'));
  const cl=[...clone.querySelectorAll('svg')].filter(s=>!s.parentElement.closest('svg'));
  live.forEach((s,j)=>{
    const tmp=s.cloneNode(true); s.parentElement.insertBefore(tmp,s); bake(tmp); tmp.remove();
    svgs.push({svg:tmp.outerHTML, stack:!!s.closest('.stack'), cls:s.getAttribute('class')||''});
    const ph=d.createElement('img'); ph.setAttribute('data-svg',String(j)); cl[j].replaceWith(ph); });
  pages.push({id:sl.dataset.id,num:sl.dataset.num,step:st,n:D.S[k].n,html:clone.outerHTML.replace('class="s','class="s on'),svgs});
}
const css=[...d.querySelectorAll('style')].map(s=>s.textContent).join('\n');
fs.writeFileSync(out,JSON.stringify({css,pages}));
console.log('pages',pages.length);
