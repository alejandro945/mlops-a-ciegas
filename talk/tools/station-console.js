/* The AWS console, redrawn from the run's own data (no screenshots): one panel per act, live with the replay.
   Inlined into talk/estacion.html by build_station.py. Uses the page's globals: D, M, EV, DEVS, T0, T1, t, cur,
   perMin, hms, TZ, $. Every number on a panel comes from the evidence folder of the run (events, judge.json,
   alarm-history.txt, deployments.txt, lambda.txt); only the look is the console's. */
const CONS={
  cores:   {svc:'IoT Greengrass', bc:['AWS IoT','Greengrass','<b>Core devices</b>']},
  insights:{svc:'Logs Insights', bc:['CloudWatch','Logs','<b>Logs Insights</b>']},
  metric:  {svc:'CloudWatch', bc:['CloudWatch','Dashboards','<b>station</b>']},
  sfn:     {svc:'Step Functions', bc:['Step Functions','State machines','station-judge','<b>Execution</b>']},
  deploys: {svc:'IoT Greengrass', bc:['AWS IoT','Greengrass','<b>Deployments</b>']},
  alarm:   {svc:'CloudWatch Alarms', bc:['CloudWatch','Alarms','<b>station-missed-faults</b>']},
  lambda:  {svc:'Lambda · logs', bc:['CloudWatch','Log groups','<b>/aws/lambda/station-rollback</b>']},
  s3:      {svc:'Amazon S3', bc:['Amazon S3','Buckets','<b>station · artefactos</b>']},
  component:{svc:'IoT Greengrass', bc:['AWS IoT','Greengrass','Components','<b>com.station.Listener</b>']},
  dashboard:{svc:'CloudWatch', bc:['CloudWatch','Dashboards','<b>station</b>']},
};
let conOpen=false, conForce=null, conLast=0;
/* the console lives docked in the right panel of the station (two-thirds scale), and opens full size with A or a click */
const conKind=()=>conForce||(M[cur]&&M[cur].con)||'cores';
const DOCKED=()=>!!$('#dock')&&!document.documentElement.classList.contains('cononly');
function showOv(kind){ const k=kind||conKind(); if(!k||!CONS[k]) return; conForce=kind||null; conOpen=true; $('#ov').prepend($('#cw')); $('#ov').style.display='block'; renderCon(true); }
function hideOv(){ conOpen=false; conForce=null; $('#ov').style.display='none'; if(DOCKED()){ $('#dock').appendChild($('#cw')); renderCon(true); } }
function renderCon(force){
  if(!conOpen&&!DOCKED()) return; const now=performance.now(); if(!force&&now-conLast<150) return; conLast=now;
  const k=conKind(); if(!k||!CONS[k]) return; const c=CONS[k];
  $('#cw-bc').innerHTML=c.bc.map((x,i)=>i<c.bc.length-1?'<a>'+x+'</a><span>›</span>':x).join('');
  let h=''; try{ h=PANEL[k](); }catch(e){ console.error(e); h='<pre>'+esc(e.message)+'</pre>'; }
  $('#cw-bd').innerHTML=h; $('#ov-t').textContent=hms(t);
}

function hmsm(ms){ return new Date(ms+TZ).toISOString().slice(11,23); }
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const IC={
  ok:'<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4.6 8.3l2.2 2.2 4.6-4.8" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
  bad:'<svg viewBox="0 0 16 16"><path d="M8 1.6L15 14.2H1z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8 6v4.2M8 11.8v.5" stroke="currentColor" stroke-width="1.8"/></svg>',
  run:'<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 4v4.4l3 1.8" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
};
const pill=(s,c,i)=>'<span class="pl '+c+'">'+(i?IC[i]:'')+s+'</span>';
const H=(t,n,sub)=>'<div class="h1">'+t+(n!=null?' <span class="n">('+n+')</span>':'')+'</div>'+(sub?'<div class="sb">'+sub+'</div>':'');
/* a row that just appeared glows for 4 s of replay time (computed, so re-rendering never restarts it) */
const fresh=t0=>{ const a=(t-t0)/1000; return a>=0&&a<4?' style="background:rgba(255,214,102,'+(0.6*(1-a/4)).toFixed(2)+')"':''; };
function T(cols,rows,empty){
  return '<div class="box"><table class="ctb"><thead><tr>'+cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>'+
    (rows.length?rows.join(''):'<tr><td colspan="'+cols.length+'" class="mt">'+(empty||'Sin resultados todavía')+'</td></tr>')+'</tbody></table></div>';
}
function jsonHi(o,hot){ return '{\n'+Object.entries(o).map(([k,v])=>'  <span class="k">"'+k+'"</span>: '+
  (typeof v==='number'?'<span class="nv'+(hot&&hot.includes(k)?' r':'')+'">'+v+'</span>':'<span class="s">"'+esc(v)+'"</span>')).join(',\n')+'\n}'; }
function qb(q,n){ return '<div class="qb"><div class="ql">Log group: <b>/station/events</b> · Logs Insights QL</div><pre>'+esc(q)+'</pre></div>'+
  '<div class="qs">'+IC.ok+' Completed · <b>'+n+'</b> records matched</div>'; }
const mmss=s=>String(Math.floor(s/60)).padStart(2,'0')+':'+(s%60).toFixed(3).padStart(6,'0');
const who=n=>/^(shadow|reject|promote)-/.test(n)?'el juez · Step Functions':/^rollback-/.test(n)?'la Lambda · alarma':'deploy.sh';

const kb=n=>n>=1048576?(n/1048576).toFixed(1)+' MB':(n/1024).toFixed(1)+' KB';
const kf=n=>n>=1000?(n/1000).toFixed(n>=10000?0:2).replace(/\.?0+$/,'')+'K':String(n);
const FOLDER='<svg viewBox="0 0 16 16" class="fd"><path d="M1.5 3.5h4.2l1.4 1.6h7.4v8.4H1.5z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>';
/* the input level per pump, as the dashboard's line chart (the drift shows as one pump jumping) */
function inputChart(W,Hh){
  const B=20000, b0=Math.floor(T0/B), b1=Math.floor(T1/B);
  const sum=DEVS.map(()=>({})); EV.forEach(e=>{ if(e.t>t) return; const k=Math.floor(e.t/B), s=sum[e.d]; s[k]=s[k]||[0,0]; s[k][0]+=e.z; s[k][1]++; });
  const mx=Math.max(2.4,...sum.flatMap(s=>Object.values(s).map(v=>v[0]/v[1])))*1.08;
  const X=k=>64+(k-b0)/Math.max(1,b1-b0)*(W-96), Y=v=>Hh-44-v/mx*(Hh-64);
  const COL=['#0972D3','#FF9900','#2EA597','#D91515','#9469D6'];
  let s='';
  for(let g=0;g<=4;g+=2){ const v=mx*g/4; s+='<line x1="64" x2="'+(W-32)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#E9EBED"/><text x="54" y="'+(Y(v)+6)+'" text-anchor="end" font-size="17" fill="#5F6B7A">'+v.toFixed(1)+'</text>'; }
  for(let k=b0;k<=b1;k+=9) s+='<text x="'+X(k)+'" y="'+(Hh-14)+'" text-anchor="middle" font-size="17" fill="#5F6B7A">'+hms(k*B).slice(0,5)+'</text>';
  sum.forEach((sm,i)=>{ const ks=Object.keys(sm).map(Number).sort((a,b)=>a-b); if(!ks.length) return;
    s+='<polyline fill="none" stroke="'+COL[i]+'" stroke-width="3.5" stroke-linejoin="round" points="'+ks.map(k=>X(k).toFixed(1)+','+Y(sm[k][0]/sm[k][1]).toFixed(1)).join(' ')+'"/>'; });
  return {svg:'<svg viewBox="0 0 '+W+' '+Hh+'" class="ch">'+s+'</svg>', lg:'<div class="lgd">'+DEVS.map((d,i)=>'<span><i style="background:'+COL[i]+'"></i>'+d+'</span>').join('')+'</div>'};
}

const PANEL={
  /* IoT Greengrass › Core devices */
  cores(){
    const last=DEVS.map(()=>null); EV.forEach(e=>{ if(e.a<=t&&(!last[e.d]||e.a>last[e.d].a)) last[e.d]=e; });
    const rows=DEVS.map((d,i)=>'<tr><td><a>'+d+'</a></td><td>'+pill('Healthy','ok','ok')+'</td><td>aws_nucleus</td><td>'+(i===0?'StationRing0':'StationRing1')+
      '</td><td class="m">'+(last[i]?'v'+last[i].v:'—')+'</td><td class="m">'+(last[i]?hms(last[i].a):'—')+'</td></tr>');
    return H('Greengrass core devices',DEVS.length,'Cada bomba es un contenedor con el nucleus de Greengrass y su propio certificado X.509')+
      T(['Name','Status','Runtime','Thing group','Modelo','Último evento'],rows);
  },

  /* CloudWatch › Logs Insights: one pump's decisions (act 1) or the events that arrived late (act 2) */
  insights(){
    const m=M[cur]||{};
    if(m.k==='acto1'&&m.dev){
      const dv=DEVS.indexOf(m.dev), rs=EV.filter(e=>e.d===dv&&e.a<=t).sort((a,b)=>b.a-a.a);
      const q='fields @timestamp, device, model_version, alert, score, threshold\n| filter device = "'+m.dev+'"\n| sort @timestamp desc\n| limit 8';
      return qb(q,rs.length)+T(['@timestamp','device','model_version','alert','score','threshold'],rs.slice(0,8).map(e=>
        '<tr'+(e.al?' class="hot"':'')+fresh(e.a)+'><td class="m">'+hmsm(e.a)+'</td><td>'+DEVS[e.d]+'</td><td class="m">'+e.v+'</td><td class="m">'+
        (e.al?'<b class="r">true</b>':'false')+'</td><td class="m">'+e.s.toFixed(4)+'</td><td class="m">'+e.h.toFixed(4)+'</td></tr>'));
    }
    const rs=EV.filter(e=>e.a<=t&&e.a-e.t>10000).sort((a,b)=>a.t-b.t);
    const q='fields @timestamp, device, ts, alert, (arrived_ts - ts) / 1000 as segundos_tarde\n| filter arrived_ts - ts > 10000\n| sort ts asc';
    const rows=rs.slice(0,7).map(e=>'<tr'+fresh(e.a)+'><td class="m">'+hmsm(e.a)+'</td><td>'+DEVS[e.d]+'</td><td class="m">'+hms(e.t)+'</td><td class="m">'+
      (e.al?'<b class="r">true</b>':'false')+'</td><td class="m"><b>'+((e.a-e.t)/1000).toFixed(1)+'</b></td></tr>');
    if(rs.length>7) rows.push('<tr><td colspan="5" class="mt">… y '+(rs.length-7)+' más</td></tr>');
    return qb(q,rs.length)+T(['@timestamp (llegó)','device','decidió','alert','segundos_tarde'],rows,'Nada tarde todavía: los eventos de la bomba sin red esperan en su cola local');
  },

  /* Amazon S3 › the artifacts bucket: one folder per version, nothing overwritten; and the clips kept */
  s3(){
    const S=D.s3||{versions:[],clips:{n:0,reason:{}}};
    const what=v=>v.shadow?'la v'+(S.versions.find(x=>!x.shadow&&x.v!==v.v&&x.v.startsWith('2'))||{v:'2.0.0'}).v+' en sombra junto a la 1.0.0 (judge.sh)':v.v.startsWith('1')?'el modelo que hoy decide':'la versión candidata';
    const rows=S.versions.map(v=>'<tr><td><a>'+FOLDER+v.v+'/</a></td><td>Folder</td><td class="m">'+v.files.length+'</td><td class="m">'+kb(v.files.reduce((a,f)=>a+f.size,0))+
      '</td><td class="m">'+hms(v.t)+'</td><td>'+what(v)+'</td></tr>');
    const R={alert:'alertas',near:'cerca del umbral',sample:'muestra normal',disagree:'desacuerdo con la sombra'};
    const chips=Object.entries(S.clips.reason).sort((a,b)=>b[1]-a[1]).map(([k,n])=>'<span class="chip"><b>'+n+'</b> '+(R[k]||k)+'</span>').join('');
    return '<div class="h1">station/ <span class="n">('+S.versions.length+')</span></div><div class="sb">Una carpeta por versión: lo que ya se publicó no se toca, y Greengrass verifica la huella de cada archivo</div>'+
      T(['Name','Type','Archivos','Tamaño','Subida','Qué es'],rows)+
      '<div class="box cl"><div class="wt">'+FOLDER+'clips/ · <b>'+S.clips.n+'</b> clips que valen la pena, subidos por lotes con stream manager</div><div class="chips">'+chips+'</div></div>';
  },

  /* IoT Greengrass › Components › com.station.Listener: the versions and the threshold each one carries */
  component(){
    const S=D.s3||{versions:[],thr:{}}, vs=[...S.versions].reverse();
    const rows=vs.map(v=>'<tr><td><a>'+v.v+'</a></td><td>'+pill('Deployable','ok','ok')+'</td><td class="m">'+hms(v.t)+'</td><td class="m">v'+(v.shadow?'1.0.0':v.v)+
      '</td><td class="m">'+(v.shadow?'v2.0.0':'—')+'</td><td class="m">'+(+v.thr).toFixed(3)+'</td></tr>');
    const cfg={topic:'station/events',intervalSeconds:'3',threshold:String((+((S.thr||{})['1.0.0']||0)).toFixed(3))};
    return H('com.station.Listener',null,'Component · Private · cada versión apunta a sus archivos en S3, con su huella')+
      T(['Version','Status','Created','Decide','En sombra','threshold'],rows)+
      '<div class="box"><div class="wt">Default configuration · 1.0.0 · el umbral es configuración: se cambia sin reentrenar</div><pre class="js sm">'+jsonHi(cfg)+'</pre></div>';
  },

  /* CloudWatch › Dashboards › station: the totals of the run and the input per pump */
  dashboard(){
    const ev=EV.filter(e=>e.a<=t), byV={}; ev.forEach(e=>{ byV[e.v]=(byV[e.v]||0)+1; });
    const al=ev.filter(e=>e.al).length, mf=ev.filter(e=>e.f&&!e.al).length, on=D.alarm&&t>=D.alarm;
    const vv=Object.keys(byV).sort();
    const ch=inputChart(1380,180);
    const W=(tt,body)=>'<div class="box wd"><div class="wt">'+tt+'</div>'+body+'</div>';
    return '<div class="h1">station · lo que decide el modelo, sin el audio</div><div class="sb">1 · Input: ¿el sensor dice la verdad? · 2 · Output: ¿cambió lo que decide? · 3 · Autenticidad: ¿es el modelo que mandamos?</div>'+
      '<div class="wds">'+
        W('Gate · rollback alarm','<div class="gw">'+(on?pill('station-missed-faults','bad big','bad'):pill('station-missed-faults','ok big','ok'))+'</div>')+
        W('Clips per version','<div class="nums">'+vv.map((v,i)=>'<div><b style="color:'+(i?'#FF9900':'#0972D3')+'">'+kf(byV[v])+'</b><span>v'+v+'</span></div>').join('')+'</div>')+
        W('Alerts','<div class="nums"><div><b>'+al+'</b><span>all pumps</span></div></div>')+
        W('Faults nobody heard','<div class="nums"><div><b class="r">'+mf+'</b><span>missed faults</span></div></div>')+
      '</div><div class="box"><div class="wt">Input level per pump (std devs from what it learned)</div>'+ch.svg+ch.lg+'</div>';
  },

  /* CloudWatch › Dashboards › station: the input level per pump (the drift) */
  metric(){
    const B=20000, b0=Math.floor(T0/B), b1=Math.floor(T1/B), W=1380, Hh=400;
    const sum=DEVS.map(()=>({})); EV.forEach(e=>{ if(e.t>t) return; const k=Math.floor(e.t/B), s=sum[e.d]; s[k]=s[k]||[0,0]; s[k][0]+=e.z; s[k][1]++; });
    const mx=Math.max(2.4,...sum.flatMap(s=>Object.values(s).map(v=>v[0]/v[1])))*1.08;
    const X=k=>64+(k-b0)/Math.max(1,b1-b0)*(W-96), Y=v=>Hh-44-v/mx*(Hh-64);
    const COL=['#0972D3','#FF9900','#2EA597','#D91515','#9469D6'];
    let s='';
    for(let g=0;g<=4;g++){ const v=mx*g/4; s+='<line x1="64" x2="'+(W-32)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#E9EBED"/><text x="54" y="'+(Y(v)+6)+'" text-anchor="end" font-size="17" fill="#5F6B7A">'+v.toFixed(1)+'</text>'; }
    for(let k=b0;k<=b1;k+=9) s+='<text x="'+X(k)+'" y="'+(Hh-14)+'" text-anchor="middle" font-size="17" fill="#5F6B7A">'+hms(k*B).slice(0,5)+'</text>';
    sum.forEach((sm,i)=>{ const ks=Object.keys(sm).map(Number).sort((a,b)=>a-b); if(!ks.length) return;
      s+='<polyline fill="none" stroke="'+COL[i]+'" stroke-width="3.5" stroke-linejoin="round" points="'+ks.map(k=>X(k).toFixed(1)+','+Y(sm[k][0]/sm[k][1]).toFixed(1)).join(' ')+'"/>'; });
    const lg=DEVS.map((d,i)=>'<span><i style="background:'+COL[i]+'"></i>'+d+'</span>').join('');
    return H('station',null,'1 · Input: ¿el sensor dice la verdad? Un salto sin un solo error es deriva')+
      '<div class="box"><div class="wt">Input level per pump (std devs from what it learned)</div><svg viewBox="0 0 '+W+' '+Hh+'" class="ch">'+s+'</svg><div class="lgd">'+lg+'</div></div>';
  },

  /* Step Functions › station-judge › the execution, state by state */
  sfn(){
    const jx=(D.judge||[]).filter(x=>x.start<=t).pop();
    if(!jx) return H('station-judge',null,'Standard · el juez todavía no ha arrancado')+'<div class="box mt">Sin ejecuciones: el juez arranca con judge.sh</div>';
    const en=jx.enter||{}, ex=jx.exit||{}, at=k=>en[k]!=null&&en[k]<=t, out=k=>ex[k]!=null&&ex[k]<=t;
    const done=jx.stop&&t>=jx.stop, fail=jx.status!=='SUCCEEDED', inp=jx.input||{}, v=jx.verdict||{};
    const st=done?(fail?pill('Failed','bad','bad'):pill('Succeeded','ok','ok')):pill('Running','run','run');
    let h='<div class="eh"><div class="h1">Execution: '+esc(jx.name)+'</div><div class="kv">'+
      '<div><span>Execution status</span>'+st+'</div><div><span>Start time</span><b>'+hms(jx.start)+'</b></div>'+
      '<div><span>Duration</span><b class="m">'+mmss(Math.max(0,(done?jx.stop:t)-jx.start)/1000)+'</b></div>'+
      '<div><span>Candidata</span><b>v'+esc(inp.candidate)+' en sombra · '+esc(inp.canary)+'</b></div></div></div>';
    if(done&&fail) h+='<div class="ban">'+IC.bad+'<b>CandidateRejected</b> in step: CandidateRejected<span>'+esc(jx.cause||'')+'</span></div>';
    /* the graph, laid out as the console lays out station-judge (positions taken from its Graph view) */
    const N={DeployInShadow:[345,74,'gg','AWS IoT Greengrass V2: CreateDeployment'],Bake:[345,126,'wait','Wait state'],
      Measure:[246,178,'cwl','Amazon CloudWatch Logs: StartQuery'],WaitForQuery:[246,230,'wait','Wait state'],
      ReadQuery:[132,282,'cwl','Amazon CloudWatch Logs: GetQueryResults'],'QueryDone?':[246,334,'choice','Choice state'],
      Verdict:[345,390,'pass','Pass state'],'Passes?':[450,446,'choice','Choice state'],
      PromoteRing0:[345,506,'gg','AWS IoT Greengrass V2: CreateDeployment'],PromoteRing1:[345,558,'gg','AWS IoT Greengrass V2: CreateDeployment'],
      RememberLastGood:[345,610,'ssm','AWS Systems Manager: PutParameter'],Promoted:[345,666,'succeed','Succeed state'],
      Reject:[588,558,'gg','AWS IoT Greengrass V2: CreateDeployment'],Notify:[588,610,'sns','Amazon SNS: Publish'],
      CandidateRejected:[588,666,'fail','Fail state'],QueryFailed:[106,666,'fail','Fail state']};
    const NW=232, NH=42, ord=Object.keys(en).filter(k=>en[k]<=t).sort((a,b)=>en[a]-en[b]), fk=ord[ord.length-1];
    const stt=k=>!at(k)?'idle':(k==='CandidateRejected'||k==='QueryFailed')?'fail':(out(k)||k==='Promoted'||(done&&!fail))?'ok':'run';
    const FILL={idle:['#FFFFFF','#C6CDD5','#5F6B7A'],run:['#E1EEFB','#0972D3','#0972D3'],ok:['#DDF2D6','#9FD38E','#29733A'],fail:['#FAD6D3','#E8908A','#D91515']};
    const glyph=(kind,x,y,c)=>{ /* the flow states' own icons, as the console draws them */
      const s='fill="none" stroke="'+c+'" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
      if(kind==='wait') return '<circle cx="'+x+'" cy="'+(y+1)+'" r="8" '+s+'/><path d="M'+x+' '+(y-3)+'v4l3 2M'+(x-3)+' '+(y-10)+'h6" '+s+'/>';
      if(kind==='choice') return '<circle cx="'+x+'" cy="'+(y-6)+'" r="3" '+s+'/><circle cx="'+(x-7)+'" cy="'+(y+7)+'" r="3" '+s+'/><circle cx="'+(x+7)+'" cy="'+(y+7)+'" r="3" '+s+'/><path d="M'+x+' '+(y-3)+'v3l-6 4M'+x+' '+y+'l6 4" '+s+'/>';
      if(kind==='pass') return '<path d="M'+(x-9)+' '+y+'h18M'+x+' '+(y-9)+'v18M'+(x+5)+' '+(y-4)+'l4 4-4 4M'+(x-5)+' '+(y-4)+'l-4 4 4 4" '+s+'/>';
      if(kind==='fail') return '<circle cx="'+x+'" cy="'+y+'" r="8.5" '+s+'/><path d="M'+(x-3.5)+' '+(y-3.5)+'l7 7M'+(x+3.5)+' '+(y-3.5)+'l-7 7" '+s+'/>';
      if(kind==='succeed') return '<circle cx="'+x+'" cy="'+y+'" r="8.5" '+s+'/><path d="M'+(x-4)+' '+y+'l3 3 5-6" '+s+'/>';
      return ''; };
    const curve=(x1,y1,x2,y2)=>{ const m=(y1+y2)/2; return 'M'+x1+' '+y1+' C'+x1+' '+m+' '+x2+' '+m+' '+x2+' '+y2; };
    const E=(d,lab,lx,ly)=>'<path d="'+d+'" fill="none" stroke="#9BA7B6" stroke-width="1.6" marker-end="url(#sa)"/>'+
      (lab?(()=>{ const w=lab.length*6.4+14; return '<rect x="'+(lx-w/2)+'" y="'+(ly-10)+'" width="'+w+'" height="19" rx="4" fill="#FFFFFF" stroke="#C6CDD5"/><text x="'+lx+'" y="'+(ly+4)+'" text-anchor="middle" font-size="11" fill="#5F6B7A">'+lab+'</text>'; })():'');
    const bot=k=>[N[k][0],N[k][1]+NH/2], top=k=>[N[k][0],N[k][1]-NH/2-2];
    let g='';
    g+=E(curve(345,38,345,N.DeployInShadow[1]-NH/2-2));
    [['DeployInShadow','Bake'],['Bake','Measure'],['Measure','WaitForQuery'],['WaitForQuery','ReadQuery'],['ReadQuery','QueryDone?'],['Verdict','Passes?'],
     ['PromoteRing0','PromoteRing1'],['PromoteRing1','RememberLastGood'],['RememberLastGood','Promoted'],['Reject','Notify'],['Notify','CandidateRejected']]
      .forEach(([a,b])=>{ const p=bot(a), q=top(b); g+=E(curve(p[0],p[1],q[0],q[1])); });
    g+=E(curve(246,355,345,N.Verdict[1]-NH/2-2),'Status = Complete',296,365);
    g+=E('M'+(246+NW/2)+' 334 C405 334 405 230 '+(246+NW/2+2)+' 230','Scheduled · Running',405,282);
    g+=E('M150 355 C60 420 60 600 100 '+(666-NH/2-2),'Default',62,520);
    g+=E(curve(450,467,345,506-NH/2-2),'clips ≥ mín. y pasa',392,477);
    g+=E('M'+(450+NW/2)+' 446 C705 446 705 126 '+(345+NW/2+2)+' 126','pocos clips: hornear más',650,290);
    g+=E('M'+(450+NW/2-24)+' 467 C588 490 588 520 588 '+(558-NH/2-2),'Default',588,507);
    g+=E('M106 687 C106 712 320 714 '+(345-17)+' 714')+E('M345 687 L345 '+(714-17))+E('M588 687 C588 712 370 714 '+(345+17)+' 714');
    g+='<circle cx="345" cy="22" r="16" fill="#FCE3C6" stroke="#E9A55A"/><text x="345" y="26" text-anchor="middle" font-size="10" fill="#8A4B08">Start</text>'+
       '<circle cx="345" cy="714" r="16" fill="#FCE3C6" stroke="#E9A55A"/><text x="345" y="718" text-anchor="middle" font-size="10" fill="#8A4B08">End</text>';
    Object.entries(N).forEach(([k,[cx,cy,ic,ty]])=>{
      const s=stt(k), f=FILL[s], x=cx-NW/2, y=cy-NH/2, sel=k===fk;
      g+='<rect x="'+x+'" y="'+y+'" width="'+NW+'" height="'+NH+'" rx="7" fill="'+f[0]+'" stroke="'+(sel?(s==='fail'?'#D91515':s==='run'?'#0972D3':'#37A33C'):f[1])+'" stroke-width="'+(sel?3:1.3)+'"/>';
      if(SFNIC[ic]) g+='<image href="'+SFNIC[ic]+'" x="'+(x+7)+'" y="'+(y+7)+'" width="26" height="26"/>';
      else g+=glyph(ic,x+20,cy,s==='idle'?'#5F6B7A':f[2]);
      g+='<text x="'+(x+40)+'" y="'+(y+14)+'" font-size="9" fill="#5F6B7A">'+ty+'</text>'+
         '<text x="'+(x+40)+'" y="'+(y+33)+'" font-size="18" font-weight="700" fill="'+(s==='idle'?'#5F6B7A':'#16191F')+'">'+k+'</text>';
      if(s!=='idle') g+=s==='ok'?'<circle cx="'+(x+NW-12)+'" cy="'+cy+'" r="6" fill="none" stroke="#29733A" stroke-width="1.4"/><path d="M'+(x+NW-15)+' '+cy+'l2.2 2.2 4-4.4" fill="none" stroke="#29733A" stroke-width="1.4"/>':
        s==='fail'?'<circle cx="'+(x+NW-12)+'" cy="'+cy+'" r="6" fill="none" stroke="#D91515" stroke-width="1.4"/><path d="M'+(x+NW-14.5)+' '+(cy-2.5)+'l5 5M'+(x+NW-9.5)+' '+(cy-2.5)+'l-5 5" stroke="#D91515" stroke-width="1.4"/>':
        '<circle cx="'+(x+NW-12)+'" cy="'+cy+'" r="6" fill="none" stroke="#0972D3" stroke-width="1.6" stroke-dasharray="26 12"/>';
    });
    const svg='<svg viewBox="-14 0 728 736" class="sg"><defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0L10,5L0,10z" fill="#9BA7B6"/></marker></defs>'+g+'</svg>';
    const zb='<div class="zb">'+['+','−','◎','⊟','⛶'].map(s=>'<i>'+s+'</i>').join('')+'</div>';
    const LI=(c,s,l)=>'<span><i style="border-color:'+c+';color:'+c+'">'+s+'</i>'+l+'</span>';
    const leg='<div class="leg">'+LI('#0972D3','◷','In progress')+LI('#D91515','✕','Failed')+LI('#E07B00','!','Caught error')+LI('#5F6B7A','–','Canceled')+LI('#29733A','✓','Succeeded')+'</div>';
    /* the step's panel, as the console shows it: tabs, then the state's input or output in a code editor */
    const code=o=>{ const L=jsonHi(o,['missed','missedRate']).split('\n'); return '<div class="ce">'+L.map((l,i)=>'<div><b>'+(i+1)+'</b>'+l+'</div>').join('')+'</div>'; };
    const TY={DeployInShadow:'Task',Bake:'Wait',Measure:'Task',WaitForQuery:'Wait',ReadQuery:'Task','QueryDone?':'Choice',Verdict:'Pass','Passes?':'Choice',
      Reject:'Task',Notify:'Task',CandidateRejected:'Fail',PromoteRing0:'Task',PromoteRing1:'Task',RememberLastGood:'Task',Promoted:'Succeed',QueryFailed:'Fail'};
    const sk=out('Verdict')?'Verdict':fk;
    let d='<div class="sdh"><div class="h2">'+esc(sk||'—')+'</div><span class="btn">Test state</span></div>'+
      '<div class="tabs"><b>Input/Output</b><span>Variables</span><span>Details</span><span>Definition</span><span>Events</span></div>'+
      '<div class="adv"><i></i>Advanced view<em>'+(TY[sk]||'')+' · '+(stt(sk)==='run'?pill('In progress','run','run'):stt(sk)==='fail'?pill('Failed','bad','bad'):pill('Succeeded','ok','ok'))+'</em></div>';
    if(out('Verdict')){
      d+='<div class="lb">⌄ State output <a>Learn more</a></div>'+code({clips:v.clips,missed:v.missed,extra:v.extra,missedRate:+(+v.missedRate).toFixed(3)})+
         '<div class="rule">La regla: ≥ '+inp.minClips+' clips · no oídas ≤ '+Math.round(inp.maxMissedRate*100)+' % · extra ≤ '+Math.round(inp.maxExtraRate*100)+' %</div>';
    } else if(at('Bake')){
      const el=Math.min(inp.bakeSeconds,Math.max(0,((out('Bake')?ex.Bake:t)-en.Bake)/1000));
      d+='<div class="lb">⌄ State input <a>Learn more</a></div>'+code({candidate:inp.candidate,active:inp.active,canary:inp.canary,bakeSeconds:inp.bakeSeconds})+
         '<div class="rule">La v'+esc(inp.candidate)+' escucha en sombra; decide la v'+esc(inp.active)+' · <b>'+Math.floor(el)+' s</b> de '+inp.bakeSeconds+' s</div><div class="pb"><i style="width:'+(el/inp.bakeSeconds*100).toFixed(1)+'%"></i></div>';
    } else {
      d+='<div class="lb">⌄ State input <a>Learn more</a></div>'+code({candidate:inp.candidate,carrier:inp.carrier,active:inp.active,canary:inp.canary});
    }
    return h+'<div class="sfw"><div class="box gv"><div class="gvh"><div class="wt">Graph view</div><span class="btn">Actions ▾</span><span class="gear">⚙</span></div>'+zb+svg+leg+'</div><div class="box sd">'+d+'</div></div>';
  },

  /* IoT Greengrass › Deployments: every deployment of the run, who created it, which one runs */
  deploys(){
    const ds=D.deploys.filter(x=>x.t<=t&&x.t>=T0-180000).sort((a,b)=>b.t-a.t), latest={};
    ds.forEach(x=>{ if(!latest[x.g]) latest[x.g]=x; });
    const rows=ds.map(x=>'<tr'+fresh(x.t)+'><td><a>'+esc(x.name)+'</a></td><td>'+esc(x.g)+'</td><td>'+(latest[x.g]===x?pill('Active','ok','ok'):pill('Inactive','mute'))+
      '</td><td class="m">'+hms(x.t)+'</td><td>'+who(x.name)+'</td></tr>');
    return H('Greengrass deployments',ds.length,'Un despliegue por ring · el último de cada grupo es el que corre en las bombas')+
      T(['Deployment','Target','Status','Created','Lo creó'],rows);
  },

  /* CloudWatch › Alarms › station-missed-faults */
  alarm(){
    const on=D.alarm&&t>=D.alarm, THR=8, W=1380, Hh=300;
    const m0=Math.floor(T0/60000), m1=Math.floor(T1/60000), mN=Math.min(m1,Math.floor(t/60000));
    const mx=Math.max(12,...Object.values(perMin))*1.1;
    const X=m=>64+(m-m0)/Math.max(1,m1-m0)*(W-96), Y=v=>Hh-64-v/mx*(Hh-84);
    let s='';
    [0,mx/2,mx].forEach(v=>{ s+='<line x1="64" x2="'+(W-32)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#E9EBED"/><text x="54" y="'+(Y(v)+6)+'" text-anchor="end" font-size="17" fill="#5F6B7A">'+Math.round(v)+'</text>'; });
    s+='<line x1="64" x2="'+(W-32)+'" y1="'+Y(THR)+'" y2="'+Y(THR)+'" stroke="#D91515" stroke-dasharray="7 5" stroke-width="2.2"/>'+
       '<text x="74" y="'+(Y(THR)-9)+'" font-size="17" fill="#D91515" font-weight="600">MissedFaults &gt;= 8 for 1 datapoints within 1 minute</text>';
    const pts=[]; for(let m=m0;m<=mN;m++) pts.push([X(m),Y(perMin[m]||0)]);
    if(pts.length) s+='<polyline fill="none" stroke="#0972D3" stroke-width="3.5" stroke-linejoin="round" points="'+pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')+'"/>'+
      pts.map(p=>'<circle cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="4" fill="#0972D3"/>').join('');
    for(let m=m0;m<=m1;m+=2) s+='<text x="'+X(m)+'" y="'+(Hh-36)+'" text-anchor="middle" font-size="17" fill="#5F6B7A">'+hms(m*60000).slice(0,5)+'</text>';
    const xa=X(Math.max(T0,Math.min(t,D.alarm||t))/60000), xt=X(t/60000), x0=X(T0/60000);
    s+='<rect x="'+x0+'" y="'+(Hh-22)+'" width="'+Math.max(0,xa-x0)+'" height="16" fill="#69AE34"/>'+(on?'<rect x="'+xa+'" y="'+(Hh-22)+'" width="'+Math.max(4,xt-xa)+'" height="16" fill="#D91515"/>':'');
    const hs=(D.alarmHist||[]).filter(x=>x.t<=t&&x.t>=T0-1800000).sort((a,b)=>b.t-a.t)
      .map(x=>'<tr'+fresh(x.t)+'><td class="m">'+hms(x.t)+'</td><td>State update</td><td>'+(/to ALARM/.test(x.s)?'<b class="r">'+esc(x.s)+'</b>':esc(x.s))+'</td><td>'+(/to ALARM/.test(x.s)?'invoca la Lambda station-rollback':'—')+'</td></tr>');
    return '<div class="ah"><div class="h1">station-missed-faults</div>'+(on?pill('In alarm','bad big','bad'):pill('OK','ok big','ok'))+'</div>'+
      '<div class="sb">Metric alarm · namespace Station · las fallas que nadie oyó, por minuto</div>'+
      '<div class="box"><div class="wt">MissedFaults</div><svg viewBox="0 0 '+W+' '+Hh+'" class="ch">'+s+'</svg></div>'+T(['Date','Type','Description','Acción'],hs);
  },

  /* CloudWatch › Log groups › /aws/lambda/station-rollback */
  lambda(){
    const L=(D.lam&&D.lam.lines)||[], rs=L.filter(x=>x.t<=t);
    const rows=rs.map(x=>'<tr'+(/rolled_back_to/.test(x.msg)?' class="hot"':'')+fresh(x.t)+'><td class="m">'+hmsm(x.t)+'</td><td class="m"><div class="lm">'+
      esc(x.msg).replace(/(&quot;rolled_back_to&quot;: &quot;[\d.]+&quot;)/,'<b class="r">$1</b>')+'</div></td></tr>');
    return H('Log events',null,'/aws/lambda/station-rollback · la función que invoca la alarma: despliega al ring 0 la última versión buena')+
      T(['Timestamp','Message'],rows,'Sin eventos todavía: la Lambda espera a que la alarma pase a ALARM');
  },
};
