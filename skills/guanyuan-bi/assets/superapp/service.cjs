'use strict';
// Host supplies authenticated adapters; this module has no credentials or HTTP listener.
const KINDS=new Set(['overview','funnel','channels','monitor']);
function validRequest(q){
 if(!q||q.schemaVersion!==1||typeof q.requestId!=='string'||q.requestId.length>128||!KINDS.has(q.template)||typeof q.sourceRef!=='string'||!q.sourceRef||q.sourceRef.length>200||!['local','ai'].includes(q.mode))throw Error('invalid_request');
 if(q.scope!==null&&(typeof q.scope!=='string'||q.scope.length>200))throw Error('invalid_scope');
 if(typeof q.window!=='string'||q.window.length>100)throw Error('invalid_window');
 if(q.action!==undefined&&(typeof q.action!=='string'||q.action.length>80))throw Error('invalid_action');
 return {schemaVersion:1,requestId:q.requestId,template:q.template,sourceRef:q.sourceRef,scope:q.scope,window:q.window,mode:q.mode,...(q.action?{action:q.action}:{})};
}
function createService({engine,authenticate,authorize,loadSnapshot,provider,investigateDaily}){
 if(![authenticate,authorize,loadSnapshot].every(x=>typeof x==='function'))throw Error('authentication_and_data_adapters_required');
 return async function handle(request,transportContext,{signal}={}){
  const q=validRequest(request);
  const principal=await authenticate(transportContext);if(!principal)throw Error('unauthenticated');
  const permission=await authorize(principal,q);if(!permission||permission.allowed!==true)throw Error('forbidden');
  // Server, not browser, supplies trusted context, revision, data and freshness evidence.
  const snapshot=await loadSnapshot(principal,q,{signal});
  if(!snapshot||typeof snapshot.revision!=='string'||!snapshot.revision||typeof snapshot.observedAt!=='string'||!Number.isFinite(Date.parse(snapshot.observedAt)))throw Error('invalid_snapshot');
  const analysis=engine.analyze(q.template,snapshot.rows,snapshot.context,q.scope);
  if(analysis.status!=='ok')throw Error('no_data');
  let investigation=null,ai=null;
  if(q.action){
   if(!analysis.actions.some(a=>a.id===q.action))throw Error('action_not_allowed');
   investigation=engine.investigate(q.template,snapshot.rows,snapshot.context,q.scope,q.action);
   if(investigation.status==='needs_data'&&investigateDaily){
    const allowed=await authorize(principal,{...q,operation:'daily-evidence'});
    if(!allowed||allowed.allowed!==true)throw Error('investigation_forbidden');
    investigation=await investigateDaily(principal,q,snapshot,{signal});
    if(!investigation||!['complete','needs_data','not_evaluable'].includes(investigation.status))throw Error('invalid_investigation');
   }
  }
  if(q.mode==='ai'){
   if(permission.allowAI!==true)throw Error('ai_data_use_not_allowed');
   if(!provider)throw Error('ai_not_configured');
   // Only authorized scoped aggregate evidence is sent; no raw rows or browser-selected tools.
   const pack={template:q.template,scope:q.scope,periods:{current:snapshot.context.currentLabel,baseline:snapshot.context.baselineLabel},revision:snapshot.revision,evidence:analysis.evidence};
   const raw=await provider(pack,{signal});
   const ids=new Set(analysis.evidence.map(e=>e.id));
   if(!raw||typeof raw.summary!=='string'||raw.summary.length>6000||!Array.isArray(raw.evidenceIds)||!raw.evidenceIds.length||raw.evidenceIds.some(id=>!ids.has(id)))throw Error('invalid_ai_evidence');
   ai={summary:raw.summary,evidenceIds:[...new Set(raw.evidenceIds)],notice:'AI 解释引用已知证据；引用有效不等于因果或文字事实已验证。'};
  }
  if(signal?.aborted)throw Error('cancelled');
  return {schemaVersion:1,requestId:q.requestId,template:q.template,scope:q.scope,window:q.window,revision:snapshot.revision,observedAt:snapshot.observedAt,generatedAt:new Date().toISOString(),mode:q.mode,analysis,investigation,ai};
 };
}
// Pass an initialized official MCP SDK Client. MCP is a tool protocol, not an LLM.
// The selected tool must implement the analysis contract and may host an approved AI service.
function mcpProvider(client,toolName){
 if(!client||typeof client.callTool!=='function'||typeof toolName!=='string'||!toolName)throw Error('mcp_adapter_required');
 return async(pack,{signal}={})=>{
  const result=await client.callTool({name:toolName,arguments:{evidence:pack}},undefined,{signal,timeout:30000});
  if(result.isError)throw Error('mcp_tool_failed');
  if(result.structuredContent)return result.structuredContent;
  const texts=(result.content||[]).filter(c=>c.type==='text');
  if(texts.length!==1||texts[0].text.length>12000)throw Error('invalid_mcp_result');
  return JSON.parse(texts[0].text);
 };
}
module.exports={createService,mcpProvider,validRequest};
