const test=require('node:test'),assert=require('node:assert/strict');
const {catalog,analyze}=require('../skills/guanyuan-html-bi-generic/assets/templates/engine.js');
const {mount}=require('../skills/guanyuan-html-bi-generic/assets/templates/view.js');
const context={currentLabel:'synthetic current',baselineLabel:'synthetic baseline',qualityConfirmed:true,cohortConfirmed:true,threshold:0.2};
const rows=[{period:'baseline',group:'A',visitors:100,leads:40,orders:20,sales:400},{period:'current',group:'A',visitors:80,leads:30,orders:15,sales:300},{period:'baseline',group:'B',visitors:60,leads:24,orders:12,sales:240},{period:'current',group:'B',visitors:70,leads:28,orders:14,sales:280}];
test('contributions include offsetting gains; ratios use weighted totals',()=>{
 const a=analyze('overview',rows,context);assert.equal(a.delta,-60);assert.equal(a.groups.reduce((s,g)=>s+g.delta,0),a.delta);assert.equal(a.groups[0].group,'A');assert.equal(a.average,20);assert.equal(analyze('channels',rows,context).groups[1].conversion,0.2);
});
test('quality, missing periods, missing metrics and duplicate grain block conclusions',()=>{
 for(const kind of Object.keys(catalog)){
  assert.throws(()=>analyze(kind,rows,{...context,qualityConfirmed:false}));
  assert.throws(()=>analyze(kind,rows.slice(1),context));
  assert.throws(()=>analyze(kind,[...rows,rows[0]],context));
  for(const invalid of [null,NaN,Infinity,-1,'30'])assert.throws(()=>analyze(kind,[{...rows[0],[catalog[kind].fields[0]]:invalid},...rows.slice(1)],context));
 }
});
test('funnel rejects non-nested counts and unconfirmed cohorts',()=>{
 assert.throws(()=>analyze('funnel',rows,{...context,cohortConfirmed:false}));
 assert.throws(()=>analyze('funnel',[{...rows[0],leads:101},...rows.slice(1)],context));
 const a=analyze('funnel',rows,context);assert.equal(a.stages[1].rate,29/58);
});
test('zero baseline is unevaluable; stable periods do not generate alerts',()=>{
 const zero=rows.map(r=>({...r,sales:r.period==='baseline'?0:r.sales}));
 const a=analyze('monitor',zero,context);assert.equal(a.rate,null);assert.equal(a.alerts.length,0);assert.equal(a.notEvaluable.length,2);
 const stable=rows.map(r=>({...r,sales:100}));assert.equal(analyze('monitor',stable,context).alerts.length,0);
 assert.throws(()=>analyze('monitor',rows,{...context,threshold:0}));
});
test('four layouts render; drill-down recomputes evidence and empty rerender clears handler',()=>{
 const c={innerHTML:'',onclick:null};
 for(const kind of Object.keys(catalog)){mount(c,kind,rows,context);assert.ok(c.innerHTML.includes(catalog[kind].title));assert.ok(c.innerHTML.includes(kind==='funnel'?'29':'580'));}
 mount(c,'overview',rows,context);
 c.onclick({target:{closest:()=>({dataset:{group:'0'}})}});
 assert.ok(c.innerHTML.includes('增减 -100'));assert.ok(!c.innerHTML.includes('增减 -60'));
 c.onclick({target:{closest:()=>({dataset:{reset:'1'}})}});assert.ok(c.innerHTML.includes('增减 -60'));
 mount(c,'overview',[],context);assert.equal(c.onclick,null);assert.ok(c.innerHTML.includes('role="status"'));
 mount(c,'overview',rows,{...context,qualityConfirmed:false});assert.equal(c.onclick,null);assert.ok(c.innerHTML.includes('role="alert"'));
});
test('channel conversion requires unique converted users within visitors',()=>{
 assert.throws(()=>analyze('channels',rows.map((r,i)=>i===0?{...r,orders:101}:r),context));
});
test('untrusted labels are escaped, including context and scope',()=>{
 const c={innerHTML:'',onclick:null},bad=rows.map(r=>({...r,group:r.group==='A'?'<img src=x>':r.group}));
 mount(c,'overview',bad,{...context,currentLabel:'<script>x</script>',dashboardTitle:'<img src=x>',unit:'<svg onload=x>'},null,'unknown');
 assert.ok(!c.innerHTML.includes('<img'));assert.ok(!c.innerHTML.includes('<svg onload'));assert.ok(!c.innerHTML.includes('<script>'));assert.ok(c.innerHTML.includes('&lt;img'));
});

test('zero-valued periods render without non-finite chart coordinates or rates',()=>{
 const zero=rows.map(r=>({...r,visitors:0,leads:0,orders:0,sales:0}));
 const c={innerHTML:'',onclick:null};
 for(const kind of Object.keys(catalog)){
  mount(c,kind,zero,context);
  assert.ok(!/NaN|Infinity/.test(c.innerHTML));
  assert.ok(c.innerHTML.includes('不可计算'));
 }
});
