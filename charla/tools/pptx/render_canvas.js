// Dibuja las animaciones de canvas del deck HTML como PNG (pasos) y cuadros (memes), para el PowerPoint.
// node render_canvas.js ../../devopsdays.html salida/
const fs=require('fs'), path=require('path'); const {JSDOM}=require('jsdom'); const {createCanvas,GlobalFonts}=require('@napi-rs/canvas');
const F='/usr/share/fonts/truetype/crosextra/', L='/usr/share/fonts/truetype/liberation2/';
for(const f of ['Carlito-Regular','Carlito-Bold']) if(fs.existsSync(F+f+'.ttf')) GlobalFonts.registerFromPath(F+f+'.ttf','Carlito');
for(const f of ['LiberationMono-Regular','LiberationMono-Bold']) if(fs.existsSync(L+f+'.ttf')) GlobalFonts.registerFromPath(L+f+'.ttf','Courier New');
const [,,src,out]=process.argv; fs.mkdirSync(out,{recursive:true});
const dom=new JSDOM(fs.readFileSync(src,'utf8'),{runScripts:'dangerously',pretendToBeVisual:true,url:'http://localhost/',beforeParse(w){
  w.matchMedia=()=>({matches:false,addListener(){},removeListener(){}}); w.requestAnimationFrame=()=>0;
  w.HTMLCanvasElement.prototype.getContext=function(){ if(!this._nc){ const nc=createCanvas(10,10); this._nc=nc; this._ctx=nc.getContext('2d');
      Object.defineProperty(this,'width',{get(){return nc.width},set(v){nc.width=v}}); Object.defineProperty(this,'height',{get(){return nc.height},set(v){nc.height=v}}); }
    return this._ctx; };
  const dim=(el,k)=>{ const st=el.parentElement.getAttribute('style')||''; const g=n=>{const m=st.match(new RegExp(n+':\\s*(-?\\d+)px'));return m?+m[1]:0;};
    return k==='w'?1600-g('left')-g('right'):900-g('top')-g('bottom'); };
  Object.defineProperty(w.HTMLCanvasElement.prototype,'clientWidth',{get(){return dim(this,'w')}});
  Object.defineProperty(w.HTMLCanvasElement.prototype,'clientHeight',{get(){return dim(this,'h')}});
}});
const D=dom.window.__deck, meta={};
D.slides.forEach((sl,k)=>{ const a=D.A[k]; if(!a) return; const id=sl.dataset.id, st0=sl.querySelector('.chart').getAttribute('style');
  D.show(k); D.sizeC(a);
  const box={}; st0.replace(/(left|right|top|bottom):\s*(\d+)px/g,(m,n,v)=>box[n]=+v);
  meta[id]={anim:a.cv.dataset.anim,steps:a.def.steps,box,W:a.W,H:a.H,files:[]};
  const draw=(st,p,t)=>{ a.g.setTransform(2,0,0,2,0,0); a.g.clearRect(0,0,a.W,a.H); a.def.draw(a.g,a.W,a.H,st,p,t); return a.cv._nc.toBuffer('image/png'); };
  for(let st=0;st<a.def.steps;st++){
    if(a.cv.dataset.anim==='memes'){ const fr=[]; const N=46;
      for(let f=0;f<N;f++){ const t=f*4.6/N, fn=`${id}_s${st}_f${String(f).padStart(2,'0')}.png`; fs.writeFileSync(path.join(out,fn),draw(st,1,t)); fr.push(fn); }
      meta[id].files.push(fr);
    } else { const fn=`${id}_s${st}.png`; fs.writeFileSync(path.join(out,fn),draw(st,1,2.2)); meta[id].files.push(fn); }
  }
});
fs.writeFileSync(path.join(out,'canvas.json'),JSON.stringify(meta,null,1));
console.log(Object.keys(meta).join(' '));
