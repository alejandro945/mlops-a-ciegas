// Renders talk/assets/screens/*.png from the Oct 12 rehearsal evidence (evidencia-e2e/en, kept out of the repo because
// it holds the AWS account id), with the account id masked. Needs playwright-core and Google Chrome:
//   npm i playwright-core && node talk/tools/screens/render.js evidencia-e2e/en talk/assets/screens
const {chromium}=require('playwright-core'); const fs=require('fs'); const path=require('path');
const [,,EV,OUT]=process.argv;
const rd=f=>fs.readFileSync(path.join(EV,f),'utf8');
const ACCT=(rd('03-healthy-publish-deploy.txt').match(/station-(\d{12})-/)||[])[1];
const mask=s=>ACCT?s.split(ACCT).join('‹cuenta›'):s;
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const img=f=>'data:image/png;base64,'+fs.readFileSync(path.join(EV,f)).toString('base64');

// a line of terminal output; hot = highlighted, dim = context
const L=(s,cls='')=>`<div class="l ${cls}">${color(esc(mask(s)))}</div>`;
function color(s){
  return s.replace(/\bALERT\b/g,'<b class="al">ALERT</b>')
          .replace(/· missed fault/g,'<b class="mf">· missed fault</b>')
          .replace(/(· arrived \d+ s late)/g,'<b class="lt">$1</b>')
          .replace(/\b(HEALTHY|RUNNING|ACTIVE)\b/g,'<b class="ok">$1</b>')
          .replace(/(OK to ALARM)/g,'<b class="al">$1</b>')
          .replace(/("rolled_back_to": "1\.0\.0")/g,'<b class="al">$1</b>');
}
const cmd=s=>`<div class="l cmd">$ ${esc(s)}</div>`;
const gap='<div class="gap"></div>';

const pub=rd('03-healthy-publish-deploy.txt').split('\n');
const pick=(re)=>pub.filter(l=>re.test(l));
const dep=rd('21-greengrass-deployments.txt').split('\n');
const late=rd('13-act2-network-back.txt').split('\n').filter(l=>/late/.test(l)).slice(0,6);
const act3=rd('16-act3-pump01-v2-and-back.txt').split('\n');
const alarm=rd('20-alarm-and-lambda.txt').split('\n');

const SHOTS={
  's3-versiones': {w:1300, body:
    cmd('./demo/publish.sh 1.0.0')+
    pick(/uploading build\/1\.0\.0|1\.0\.0 ready/).map((l,k)=>L(l,k?'dim':'hot')).join('')+gap+
    cmd('./demo/publish.sh 2.0.0')+
    pick(/uploading build\/2\.0\.0|2\.0\.0 ready/).map((l,k)=>L(l,k?'dim':'hot')).join('')+gap+
    '<div class="note">Una carpeta por versión: <code>station/1.0.0/</code> y <code>station/2.0.0/</code>. Nunca se pisa una.</div>'},
  'gg-componente': {w:1300, body:
    cmd('./demo/publish.sh 1.0.0 && ./demo/publish.sh 2.0.0')+
    pick(/creating com\.station|^com\.station\.Listener\t|ready to deploy/).map(l=>L(l.replace(/\t/g,'   '),/creating|REQUESTED/.test(l)?'hot':'dim')).join('')+gap+
    '<div class="note">Greengrass calcula el digest de cada archivo al crear la versión, y el umbral viaja como configuración.</div>'},
  'gg-despliegues': {w:1240, body:
    cmd('aws greengrassv2 list-deployments --target-arn …StationRing0 / StationRing1')+
    dep.filter(l=>/^#|^\||^\+|^-/.test(l)&&!/component installed/.test(l)).slice(0,14)
       .map(l=>L(l.replace(/^# deployments of /,'# '),/rollback-to|ACTIVE/.test(l)?'hot':'')).join('')},
  'gg-equipos': {w:1420, body:
    `<div class="cols"><div>`+
    cmd('aws greengrassv2 list-core-devices')+
    pub.slice(0,9).map(l=>L(l)).join('')+
    `</div><div>`+
    cmd('./demo/network.sh on pump-03   # tras 45 s sin red')+
    late.map(l=>L(l.replace(/\s+\d+ ms/,''),'hot')).join('')+
    `<div class="note">Nada se perdió: la bomba siguió decidiendo y su cola entregó todo al volver.</div></div></div>`},
  'cw-dashboard': {w:1420, body:
    `<div class="grid">${['40-dashboard-1-alerts.png','40-dashboard-2-score-threshold.png','40-dashboard-3-input.png',
      '40-dashboard-4-versions.png','40-dashboard-5-latency.png','40-dashboard-6-missed-faults.png']
      .map(f=>`<img src="${img(f)}">`).join('')}</div>`, pad:10},
  'cw-alarma': {w:1420, body:
    `<div class="cols al2"><div><img class="chart" src="${img('40-dashboard-6-missed-faults.png')}"></div><div>`+
    L(alarm.find(l=>/OK to ALARM/.test(l)).replace(/^\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)\.\d+\+00:00\s+/,'$1 UTC  alarma · '))+
    L(alarm.find(l=>/rolled_back_to/.test(l)).replace(/^\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)\s+/,'$1 UTC  lambda · ').replace(/,\s*"deploymentId".*$/,'}'))+gap+
    cmd('./demo/watch.sh   # pump-01')+
    [act3.find(l=>/missed fault/.test(l)), act3.filter(l=>/missed fault/.test(l))[1],
     act3.find(l=>/v1\.0\.0  ALERT/.test(l)&&l>'19:57')].map(l=>L(l.replace(/\s+\d+ ms/,'').replace(/ \(threshold [\d.]+\)/,''),'hot')).join('')+
    `</div></div>`},
};

const CSS=`*{margin:0;padding:0;box-sizing:border-box}
body{background:#fff;font-family:"Courier New",Menlo,monospace;color:#071329}
.wrap{padding:22px 26px}
.l{font-size:17px;line-height:1.55;white-space:pre}
.l.cmd{color:#1F6C93;font-weight:700;margin-bottom:4px}
.l.dim{color:#5C7290}
.l.hot{background:rgba(109,40,217,.07);border-left:3px solid #6D28D9;padding-left:8px;margin-left:-11px}
b.al{color:#6D28D9} b.mf{color:#C2410C} b.lt{color:#C2410C} b.ok{color:#16825D}
.gap{height:14px}
.note{font-family:Calibri,Carlito,"Segoe UI",Helvetica,Arial,sans-serif;font-size:19px;color:#475569;margin-top:6px}
.note code{font-family:"Courier New",monospace;font-size:17px;color:#071329}
.cols{display:grid;grid-template-columns:auto 1fr;gap:34px;align-items:start}
.cols.al2{grid-template-columns:560px 1fr;align-items:center}
.cols.al2 .l{font-size:16px}
.chart{width:560px;display:block}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.grid img{width:100%;display:block}`;

(async()=>{
  fs.mkdirSync(OUT,{recursive:true});
  const b=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const p=await b.newPage({deviceScaleFactor:2,viewport:{width:1600,height:900}});
  for(const [name,s] of Object.entries(SHOTS)){
    await p.setContent(`<style>${CSS}</style><div class="wrap" id="w" style="width:${s.w}px;${s.pad!=null?'padding:'+s.pad+'px':''}">${s.body}</div>`);
    await p.waitForTimeout(150);
    const el=await p.$('#w'); await el.screenshot({path:path.join(OUT,name+'.png')});
    const bb=await el.boundingBox(); console.log(name, Math.round(bb.width)+'x'+Math.round(bb.height));
  }
  await b.close();
})();
