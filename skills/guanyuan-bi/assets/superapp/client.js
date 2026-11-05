(function(root){
'use strict';
function gatewayTransport(path,fetcher=root.fetch.bind(root)){
 if(!/^\/api\/gateway\/routes\/[a-zA-Z0-9-]+$/.test(path))throw Error('需要已确认的同源观远网关路径');
 return async(payload,{signal})=>{
  const response=await fetcher(path,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal});
  if(!response.ok)throw Error('分析服务返回 HTTP '+response.status);
  if(response.status===204||response.status===205)throw Error('分析服务未返回结果');
  if(!/application\/json|\+json/.test(response.headers.get('content-type')||''))throw Error('分析接口必须返回约定的 JSON');
  return response.json();
 };
}
function controller({transport,onState,timeoutMs=30000}){
 let generation=0,current=null,abort=null,timer=null,disposed=false;
 function invalidate(){generation++;if(abort)abort.abort();abort=null;}
 function setContext(context){if(disposed)return;invalidate();current={...context};onState({status:'stale',message:'范围或数据已变化，请更新分析。'});}
 async function run(mode='local',action){
  if(disposed||!current)return;
  invalidate();const mine=generation;abort=new AbortController();const active=abort;
  const request={...current,schemaVersion:1,requestId:'analysis-'+mine+'-'+Date.now(),mode,...(action?{action}:{})};
  onState({status:'loading',message:'正在读取当前范围并分析…'});
  const timeout=setTimeout(()=>active.abort(),timeoutMs);
  try{
   const cancelled=new Promise((_,reject)=>active.signal.addEventListener('abort',()=>reject(Error('cancelled')),{once:true}));
   const result=await Promise.race([transport(request,{signal:active.signal}),cancelled]);
   if(mine!==generation||disposed)return;
   if(active.signal.aborted)throw Error('请求超时或已取消');
   if(!result||result.schemaVersion!==1||result.requestId!==request.requestId||result.template!==request.template||result.scope!==request.scope||result.window!==request.window||result.mode!==mode||typeof result.revision!=='string'||!result.revision||!Number.isFinite(Date.parse(result.observedAt))||!Number.isFinite(Date.parse(result.generatedAt)))throw Error('返回结果与当前分析范围不一致');
   onState({status:'ready',result});
  }catch(error){if(mine===generation&&!disposed)onState({status:'error',message:active.signal.aborted?'请求超时或取消，请重试。':'分析失败，请检查服务与访问权限。'});}
  finally{clearTimeout(timeout);if(mine===generation)abort=null;}
 }
 function autoRefresh(ms=0,mode='local'){
  clearInterval(timer);timer=null;
  if(ms){if(ms<10000)throw Error('刷新间隔至少 10 秒');timer=setInterval(()=>{if(!abort&&(!root.document||!root.document.hidden))run(mode);},ms);}
 }
 function dispose(){disposed=true;invalidate();clearInterval(timer);}
 return {setContext,run,autoRefresh,dispose};
}
const api={controller,gatewayTransport};root.BIAnalysisClient=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
