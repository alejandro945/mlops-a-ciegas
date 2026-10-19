// Renders talk/assets/screens/*.png from a rehearsal's evidence folder, with the AWS account id masked.
// The evidence (evidencia-e2e/<date>/) stays out of the repo because it holds the account id; it is collected with the
// AWS CLI after a full run of the demo: s3 ls, list-component-versions, list-core-devices, list-deployments, the alarm
// history, the Lambda's log, the formatted events (watch.txt), the dashboard's charts (get-metric-widget-image, w-*.png)
// and its Logs Insights results (q-*.json).
// Needs playwright-core and Google Chrome:
//   npm i playwright-core && node talk/tools/screens/render.js evidencia-e2e/2026-10-18 talk/assets/screens
const {chromium}=require('playwright-core'); const fs=require('fs'); const path=require('path');
const [,,EV,OUT]=process.argv;
const rd=f=>fs.readFileSync(path.join(EV,f),'utf8');
const lines=f=>rd(f).split('\n').filter(Boolean);
const mask=s=>s.replace(/\b\d{12}\b/g,'‹cuenta›');
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const img=f=>'data:image/png;base64,'+fs.readFileSync(path.join(EV,f)).toString('base64');
const DAY=path.basename(EV);                                       // e.g. 2026-10-18

function color(s){
  return s.replace(/\bALERT\b/g,'<b class="al">ALERT</b>')
          .replace(/· missed fault/g,'<b class="mf">· missed fault</b>')
          .replace(/(· arrived \d+ s late)/g,'<b class="lt">$1</b>')
          .replace(/\b(HEALTHY|RUNNING|ACTIVE)\b/g,'<b class="ok">$1</b>')
          .replace(/(OK to ALARM)/g,'<b class="al">$1</b>')
          .replace(/("rolled_back_to": "1\.0\.0")/g,'<b class="al">$1</b>');
}
const L=(s,cls='')=>`<div class="l ${cls}">${color(esc(mask(s)))}</div>`;
const cmd=s=>`<div class="l cmd">$ ${esc(s)}</div>`;
const note=s=>`<div class="note">${s}</div>`;
const gap='<div class="gap"></div>';
const short=l=>l.replace(/\s+\d+ ms/,'').replace(/ \(threshold [\d.]+\)/,'');
const table=(rows,cols,hot)=>`<table><tr>${cols.map(c=>`<th>${c}</th>`).join('')}</tr>${rows.map(r=>
  `<tr${hot&&hot(r)?' class="hot"':''}>${cols.map(c=>`<td>${color(esc(String(r[c]??'')))}</td>`).join('')}</tr>`).join('')}</table>`;
const q=n=>JSON.parse(rd(fs.readdirSync(EV).find(f=>f.startsWith('q-'+n))));
const w=n=>img(fs.readdirSync(EV).find(f=>f.startsWith('w-'+n)));

const watch=lines('watch.txt');
const late=watch.filter(l=>/arrived \d+ s late/.test(l)).slice(0,6);
const missed=watch.filter(l=>/pump-01 .*missed fault/.test(l)).slice(0,2);
const back=watch.find(l=>/pump-01\s+v1\.0\.0\s+ALERT/.test(l)&&l>missed[0]);
const deps=lines('deployments.txt').filter(l=>!/\|\s+\S+\s+\|\s+\S+\s+\|\s+20\d\d-/.test(l)||l.includes(DAY));
const alarm=lines('alarm-history.txt').find(l=>l.startsWith(DAY)&&/OK to ALARM/.test(l));
const lambda=lines('lambda.txt').find(l=>/rolled_back_to/.test(l));

const SHOTS={
  's3-versiones': {w:1180, body:
    cmd('aws s3 ls s3://station-‹cuenta›-us-east-1/station/ --recursive')+
    lines('s3-station.txt').map(l=>L(l,/model\.onnx/.test(l)?'hot':'')).join('')+gap+
    note('Una carpeta por versión: <code>station/1.0.0/</code> y <code>station/2.0.0/</code>, con el modelo, el umbral, el preprocesamiento y el código.')},
  'gg-componente': {w:1180, body:
    cmd('aws greengrassv2 list-component-versions --arn …:components:com.station.Listener')+
    lines('component-versions.txt').map(l=>L(l,/com\.station/.test(l)?'hot':'')).join('')+gap+
    note('Dos versiones publicadas del mismo componente. Greengrass calculó el digest de cada archivo al crearlas: una versión publicada no se toca.')},
  'gg-despliegues': {w:1240, body:
    cmd('aws greengrassv2 list-deployments --target-arn …StationRing0 / StationRing1')+
    deps.map(l=>L(l,/rollback-to|ACTIVE/.test(l)?'hot':'')).join('')+gap+
    note('Ring 0: la 1.0.0, la 2.0.0 y el rollback, que es el activo. Ring 1: nunca recibió la 2.0.0.')},
  'gg-equipos': {w:1420, body:
    `<div class="cols"><div>`+cmd('aws greengrassv2 list-core-devices')+lines('core-devices.txt').map(l=>L(l)).join('')+
    `</div><div>`+cmd('./demo/watch.sh   # pump-03 vuelve a la red tras 45 s')+late.map(l=>L(short(l),'hot')).join('')+
    note('Nada se perdió: la bomba siguió decidiendo sin red y su cola entregó todo al volver.')+`</div></div>`},
  'cw-dashboard': {w:1420, pad:10, body:
    `<div class="grid">`+
    [['input-level-per-pump','1 · Entrada'],['score-vs-threshold','2 · Salida'],['alerts-per-pump','2 · Salida'],
     ['which-version-runs-where','3 · Autenticidad'],['faults-nobody-heard','Gate']]
      .map(([n,k])=>`<figure><span>${k}</span><img src="${w(n)}"></figure>`).join('')+
    `<figure class="tb"><span>3 · Autenticidad · Logs Insights</span>`+
    table(q('the-fleet-now'),['device','version','fingerprint','clips','max_input'])+`</figure></div>`},
  'cw-alarma': {w:1420, body:
    `<div class="cols al2"><div><img class="chart" src="${w('faults-nobody-heard')}"></div><div>`+
    L(alarm.replace(/^\S+T(\d\d:\d\d:\d\d)\.\d+-05:00\s+/,'$1  alarma · '))+
    L(lambda.trim().replace(/,\s*"deploymentId".*$/,'}').replace(/^/,'lambda · '))+gap+
    cmd('./demo/watch.sh   # pump-01')+[...missed,back].map(l=>L(short(l),'hot')).join('')+`</div></div>`},
};

const CSS=`*{margin:0;padding:0;box-sizing:border-box}
body{background:#fff;font-family:"Courier New",Menlo,monospace;color:#071329}
.wrap{padding:22px 26px}
.l{font-size:17px;line-height:1.55;white-space:pre}
.l.cmd{color:#1F6C93;font-weight:700;margin-bottom:4px}
.l.hot{background:rgba(109,40,217,.07);border-left:3px solid #6D28D9;padding-left:8px;margin-left:-11px}
b.al{color:#6D28D9} b.mf{color:#C2410C} b.lt{color:#C2410C} b.ok{color:#16825D}
.gap{height:14px}
.note{font-family:Calibri,Carlito,"Segoe UI",Helvetica,Arial,sans-serif;font-size:19px;color:#475569;margin-top:6px}
.note code{font-family:"Courier New",monospace;font-size:17px;color:#071329}
.cols{display:grid;grid-template-columns:auto 1fr;gap:34px;align-items:start}
.cols.al2{grid-template-columns:560px 1fr;align-items:center}
.cols.al2 .l{font-size:16px}
.chart{width:560px;display:block}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
figure{position:relative;border:1px solid #D5DEEA;border-radius:6px;overflow:hidden}
figure span{position:absolute;right:8px;top:6px;font:700 12px Calibri,Carlito,Helvetica,sans-serif;letter-spacing:.06em;
  text-transform:uppercase;color:#6D28D9;background:#F4F7FC;padding:2px 6px;border-radius:4px}
figure img{width:100%;display:block}
figure.tb{padding:30px 10px 8px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{font:700 11px Calibri,Carlito,Helvetica,sans-serif;text-transform:uppercase;letter-spacing:.08em;color:#5C7290;text-align:left;padding:3px 6px}
td{padding:4px 6px;border-top:1px solid #E5EAF2;white-space:nowrap}`;

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
