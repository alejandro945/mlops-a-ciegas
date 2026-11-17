/* The prologue: before the end-to-end validation, the resources are provisioned. Inlined into talk/estacion.html
   by build_station.py. D.prov: {t0 (replay ms where it starts), dur, groups [{name, n, at}], total, applyEnd, fleet,
   publish [[v, t]], deploy, start}: every count and time comes from the run (terraform-apply.txt, provision.json).
   Replay time t0 … t0+dur is the prologue; the clock shows the real time of each phase. */
const PV=D.prov||null;
/* phases, in seconds after t0: terraform (the groups tick in), the fleet (pumps one by one), publish, deploy, start */
const PH={tf:0, tfEnd:22, fleet:25, healthy:40, pub:43, dep:50, go:58};
function provPaint(){
  const el=$('#prov'); if(!PV){ if(el) el.style.display='none'; return; }
  const s=(t-PV.t0)/1000, on=s>=0&&s<PV.dur/1000;
  el.style.display=on?'block':'none';
  pumps.forEach((p,i)=>{ const inst=s>=PH.fleet+i*3, hz=s>=PH.healthy, dep=s>=PH.dep+2;
    p.classList.toggle('pv0',on&&!inst); p.classList.toggle('pv1',on&&inst);
    const tg=p.querySelector('.pvs'); if(tg) tg.textContent=!on?'':!inst?'':dep?'v1.0.0 · desplegada':hz?'Healthy':'instalada'; });
  $('#station').classList.toggle('pvon',on);
  if(!on) return;
  /* the clock: the real time of the phase */
  const real=s<PH.fleet?PV.applyEnd:s<PH.pub?PV.fleet:s<PH.dep?PV.publish[PV.publish.length-1][1]:s<PH.go?PV.deploy:PV.start;
  $('#clock').textContent=hms(real);
  const done=k=>s>=PH[k], ck=(ok,cur)=>'<i class="'+(ok?'ok':cur?'cur':'')+'">'+(ok?'✓':'')+'</i>';
  const gd=g=>g.ats.filter(a=>s>=a).length, tfN=PV.groups.reduce((a,g)=>a+gd(g),0);
  let h='<div class="ph">AWS · <b>us-east-1</b> · antes de la prueba, aprovisionar</div>';
  h+='<div class="pv-step'+(done('tfEnd')?' ok':' cur')+'">'+ck(done('tfEnd'),true)+'<div><div class="pt">Terraform · la infraestructura <span>'+tfN+' / '+PV.total+' recursos'+(done('tfEnd')?' · '+hms(PV.applyEnd):'')+'</span></div><div class="pg">'+
    PV.groups.map(g=>{ const d=gd(g); return '<div class="gc'+(d>=g.n?' ok':d?' go':'')+'"><b>'+d+'<span>/'+g.n+'</span></b>'+g.name+'</div>'; }).join('')+'</div></div></div>';
  h+='<div class="pv-step'+(done('healthy')?' ok':done('fleet')?' cur':'')+'">'+ck(done('healthy'),done('fleet'))+'<div><div class="pt">La flota · cinco bombas con Greengrass <span>'+(done('fleet')?hms(PV.fleet):'')+'</span></div>'+
    '<div class="pd">Cada bomba es un contenedor con el nucleus y su certificado: '+(done('healthy')?'las cinco Healthy':done('fleet')?'instalando…':'—')+'</div></div></div>';
  h+='<div class="pv-step'+(done('dep')?' ok':done('pub')?' cur':'')+'">'+ck(done('dep'),done('pub'))+'<div><div class="pt">publish.sh · el modelo versionado <span>'+(done('pub')?PV.publish.map(p=>'v'+p[0]+' '+hms(p[1])).join(' · '):'')+'</span></div>'+
    '<div class="pd">Cada versión a S3 y como componente de Greengrass, con la huella de cada archivo</div></div></div>';
  h+='<div class="pv-step'+(done('go')?' ok':done('dep')?' cur':'')+'">'+ck(done('go'),done('dep'))+'<div><div class="pt">deploy.sh 1.0.0 · los dos rings <span>'+(done('dep')?hms(PV.deploy):'')+'</span></div>'+
    '<div class="pd">El ring 0 y el ring 1 reciben la v1.0.0</div></div></div>';
  h+='<div class="pv-go'+(done('go')?' on':'')+'">▶ Comienza la validación de punta a punta'+(done('go')?' <span>'+hms(PV.start)+'</span>':'')+'</div>';
  el.innerHTML=h;
}
