// Invented equal-length, complete periods. No production data or IDs.
const sample=[
 {period:'baseline',group:'月球站',visitors:1000,leads:400,orders:200,sales:4000},
 {period:'current',group:'月球站',visitors:800,leads:300,orders:150,sales:3000},
 {period:'baseline',group:'火星站',visitors:600,leads:240,orders:120,sales:2400},
 {period:'current',group:'火星站',visitors:700,leads:280,orders:140,sales:2800},
 {period:'baseline',group:'木星站',visitors:400,leads:160,orders:80,sales:1600},
 {period:'current',group:'木星站',visitors:400,leads:160,orders:80,sales:1600}
];
function draw(){
 const kind=document.getElementById('kind').value,theme=document.getElementById('theme').value,state=document.getElementById('state').value;
 const rows=state==='empty'?[]:sample.map(r=>({...r}));
 if(state==='invalid') rows[0].sales=null;
 // Same invented numbers illustrate channel-attributed, deduplicated cohorts.
 if(kind==='channels')for(const r of rows)r.group=r.group.replace('站','频道');
 if(state==='invalid'&&kind==='funnel')rows[0].orders=null;
 document.getElementById('contract').textContent=BITemplates.catalog[kind].layout+' · 所需指标：'+BITemplates.catalog[kind].fields.join(', ');
 BITemplateView.mount(document.getElementById('preview'),kind,rows,{currentLabel:'2099-01-08—01-14',baselineLabel:'2099-01-01—01-07',unit:'星币',qualityConfirmed:state!=='incomplete',cohortConfirmed:true,threshold:0.2,evidenceLabel:'合成快照 · 2099-01-15 · 规则计算示范，未调用 AI 服务'},null,theme);
}
for(const id of ['kind','theme','state'])document.getElementById(id).addEventListener('change',draw);
draw();
