const test=require('node:test'),assert=require('node:assert/strict');
const engine=require('../skills/guanyuan-html-bi-generic/assets/templates/engine.js');
const {createService,mcpProvider}=require('../skills/guanyuan-bi/assets/superapp/service.cjs');
const {controller,gatewayTransport}=require('../skills/guanyuan-bi/assets/superapp/client.js');
const context={qualityConfirmed:true,cohortConfirmed:true,currentLabel:'C',baselineLabel:'B',threshold:0.2};
const rows=[{period:'baseline',group:'A',orders:200,sales:4000,visitors:1000,leads:400},{period:'current',group:'A',orders:150,sales:3000,visitors:800,leads:300}];
const snapshot={revision:'r1',observedAt:'2099-01-15T00:00:00Z',rows,context};
const query={schemaVersion:1,requestId:'synthetic-request',template:'overview',sourceRef:'synthetic',scope:null,window:'two-weeks',mode:'local'};
const defaults={engine,authenticate:async()=>({id:'test'}),authorize:async()=>({allowed:true,allowAI:true}),loadSnapshot:async()=>snapshot};
const sum=r=>r.rows.reduce((s,r)=>s+r.value,0);
test('distinct executable investigations reconcile with total changes',()=>{
 const sales=engine.investigate('overview',rows,context,null,'sales-drivers');assert.equal(sum(sales),-1000);assert.equal(sales.rows[1].value,0);
 const funnel=engine.investigate('funnel',rows,context,null,'stage-decomposition');assert.ok(Math.abs(sum(funnel)+50)<1e-9);assert.ok(funnel.rows[1].value<0);assert.equal(funnel.rows[2].value,0);
 const channels=engine.investigate('channels',rows,context,null,'channel-decomposition');assert.ok(Math.abs(channels.rows[0].trafficEffect+channels.rows[0].conversionEffect+50)<1e-9);
 const alerts=engine.investigate('monitor',rows,context,null,'alert-priority');assert.ok(Math.abs(alerts.rows[0].excessPP-5)<1e-9);
});
test('zero denominators and absent daily data never fabricate investigation',()=>{
 const emptyBase=rows.map(r=>r.period==='baseline'?{...r,orders:0,sales:0}:r);
 assert.equal(engine.investigate('overview',emptyBase,context,null,'sales-drivers').status,'not_evaluable');
 assert.equal(engine.investigate('monitor',rows,context,null,'daily-evidence').status,'needs_data');
 assert.throws(()=>engine.investigate('overview',rows,context,null,'arbitrary-tool'));
});
test('unauthorized sources rejected before loading data; browser rows ignored',async()=>{
 let loaded=false;const denied=createService({...defaults,authorize:async()=>({allowed:false}),loadSnapshot:async()=>{loaded=true;return snapshot;}});
 await assert.rejects(()=>denied(query,{}),/forbidden/);assert.equal(loaded,false);
 const service=createService(defaults);const result=await service({...query,rows:[],context:{qualityConfirmed:true},user:'admin'},{});assert.equal(result.analysis.current.sales,3000);
});
test('MCP provider receives only authorized evidence, and citations are validated',async()=>{
 let called;const client={callTool:async(...args)=>{called=args;return {structuredContent:{summary:'Synthetic hypothesis',evidenceIds:['orders'],actions:['delete']}};}};
 const service=createService({...defaults,provider:mcpProvider(client,'approved-analysis')});
 const result=await service({...query,mode:'ai'},{});assert.equal(called[0].name,'approved-analysis');assert.equal(called[0].arguments.evidence.rows,undefined);assert.equal(result.ai.actions,undefined);
 const bad=createService({...defaults,provider:async()=>({summary:'unsupported',evidenceIds:['invented']})});await assert.rejects(()=>bad({...query,mode:'ai'},{}),/invalid_ai_evidence/);
 const failed=mcpProvider({callTool:async()=>({isError:true,content:[]})},'approved');await assert.rejects(()=>failed({},{}),/mcp_tool_failed/);
});
test('AI unconfigured or not permitted is explicit; daily investigation rechecks authorization',async()=>{
 await assert.rejects(()=>createService(defaults)({...query,mode:'ai'},{}),/ai_not_configured/);
 let called=false;const service=createService({...defaults,authorize:async()=>({allowed:true,allowAI:false}),provider:async()=>{called=true;}});await assert.rejects(()=>service({...query,mode:'ai'},{}),/ai_data_use_not_allowed/);assert.equal(called,false);
 const daily=createService({...defaults,authorize:async(_,q)=>({allowed:!q.operation}),investigateDaily:async()=>{called=true;}});await assert.rejects(()=>daily({...query,action:'daily-evidence'},{}),/investigation_forbidden/);assert.equal(called,false);
});
function result(q){return {...q,revision:'r1',observedAt:'2099-01-15T00:00:00Z',generatedAt:new Date().toISOString()};}
test('late responses never overwrite new scope; invalid echo rejected',async()=>{
 const waiting=[],states=[];const c=controller({transport:q=>new Promise(resolve=>waiting.push({q,resolve})),onState:s=>states.push(s)});
 c.setContext(query);const old=c.run();c.setContext({...query,scope:'A'});const newer=c.run();waiting[1].resolve(result(waiting[1].q));await newer;waiting[0].resolve(result(waiting[0].q));await old;assert.equal(states.at(-1).result.scope,'A');assert.equal(states.filter(s=>s.status==='ready').length,1);c.dispose();
 const bad=controller({transport:async q=>({...result(q),scope:'wrong'}),onState:s=>states.push(s)});bad.setContext(query);await bad.run();assert.equal(states.at(-1).status,'error');bad.dispose();
});
test('timeout finishes even if provider ignores abort; direct URLs rejected',async()=>{
 const states=[],c=controller({transport:()=>new Promise(()=>{}),onState:s=>states.push(s),timeoutMs:5});c.setContext(query);await c.run();assert.equal(states.at(-1).status,'error');c.dispose();
 assert.throws(()=>gatewayTransport('https://example.invalid/model'));
 const t=gatewayTransport('/api/gateway/routes/analysis',async()=>({ok:true,status:204,headers:{get:()=>''}}));await assert.rejects(()=>t(query,{}),/未返回/);
});

test('fresh snapshot revisions and values are fetched per request',async()=>{
 let v=0;const service=createService({...defaults,loadSnapshot:async()=>{v++;return {...snapshot,revision:'v'+v,rows:rows.map(r=>r.period==='current'?{...r,sales:r.sales+v}:r)};}});
 const first=await service(query,{}),second=await service({...query,requestId:'second'},{});assert.notEqual(first.revision,second.revision);assert.notEqual(first.analysis.current.sales,second.analysis.current.sales);
});
