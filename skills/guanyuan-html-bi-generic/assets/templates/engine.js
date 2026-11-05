(function(root) {
'use strict';
const catalog = {
 overview:{title:'经营总览',question:'整体表现如何，变化主要来自哪里？',fields:['orders','sales'],layout:'指标 → 周期对比 → 门店贡献 → 下一步'},
 funnel:{title:'转化漏斗',question:'同一批用户在哪个环节流失？',fields:['visitors','leads','orders'],layout:'同 cohort 阶段 → 转化率 → 最大流失环节 → 验证'},
 channels:{title:'渠道对比',question:'哪些渠道贡献规模，哪些转化较好？',fields:['visitors','orders','sales'],layout:'规模与效率 → 渠道矩阵 → 变化贡献 → 验证'},
 monitor:{title:'异常监控',question:'哪些分组偏离已确认的变化阈值？',fields:['sales'],layout:'规则状态 → 异常列表 → 对比证据 → 调查建议'}
};
function analyze(kind, rows, context, scope=null) {
 const spec=catalog[kind]; if(!spec) throw new Error('未知模板');
 if(!context || context.qualityConfirmed!==true || !context.currentLabel || !context.baselineLabel) throw new Error('请先确认完整可比周期、刷新时间、粒度与口径');
 if(kind==='funnel' && context.cohortConfirmed!==true) throw new Error('漏斗需要同 cohort、阶段嵌套与成熟度确认');
 if(kind==='monitor' && (!Number.isFinite(context.threshold) || context.threshold<=0)) throw new Error('监控需要明确的正数变化阈值');
 if(!Array.isArray(rows)) throw new Error('结果集必须为数组');
 const seen=new Set();
 for(const r of rows) {
  if(!r || typeof r.group!=='string' || !r.group.trim() || !['baseline','current'].includes(r.period)) throw new Error('分组或周期无效');
  const key=JSON.stringify([r.period,r.group]);if(seen.has(key)) throw new Error('重复周期和分组');seen.add(key);
  for(const f of spec.fields) if(typeof r[f]!=='number' || !Number.isFinite(r[f]) || r[f]<0) throw new Error('指标缺失或无效：'+f);
  for(const f of spec.fields.filter(f=>f!=='sales')) if(!Number.isInteger(r[f])) throw new Error('人数/订单必须是整数');
  if(kind==='channels' && r.orders>r.visitors) throw new Error('转化用户不能超过访问用户，请确认去重口径');
  if(kind==='funnel' && (r.leads>r.visitors || r.orders>r.leads)) throw new Error('阶段不嵌套，不能按漏斗解释');
 }
 const groups=[...new Set(rows.map(r=>r.group))];
 for(const g of groups) for(const p of ['baseline','current']) if(!seen.has(JSON.stringify([p,g]))) throw new Error('分组缺少可比周期，不将缺失当零');
 const selected=rows.filter(r=>scope===null || r.group===scope);
 if(!selected.length) return {status:'empty',kind,groups:[],facts:[],next:'检查筛选范围与结果集'};
 const sum=p=>Object.fromEntries(spec.fields.map(f=>[f,selected.filter(r=>r.period===p).reduce((a,r)=>a+r[f],0)]));
 const current=sum('current'),baseline=sum('baseline');
 if([...Object.values(current),...Object.values(baseline)].some(v=>!Number.isFinite(v))) throw new Error('汇总溢出');
 const ratio=(n,d)=>d===0?null:n/d;
 const metric=kind==='funnel'?'orders':'sales';
 const delta=current[metric]-baseline[metric];
 const parts=groups.filter(g=>scope===null || g===scope).map(group=>{
  const c=selected.find(r=>r.group===group&&r.period==='current'),b=selected.find(r=>r.group===group&&r.period==='baseline');
  return {group,current:c[metric],baseline:b[metric],delta:c[metric]-b[metric],rate:ratio(c[metric]-b[metric],b[metric]),conversion:c.visitors===undefined?null:ratio(c.orders,c.visitors)};
 }).sort((a,b)=>Math.abs(b.delta)-Math.abs(a.delta));
 const facts=[{metric,current:current[metric],baseline:baseline[metric],delta,rate:ratio(delta,baseline[metric])}];
 const result={status:'ok',kind,current,baseline,facts,groups:parts,delta,rate:ratio(delta,baseline[metric]),average:ratio(current.sales,current.orders),next:'核对主要变化分组的营业天数、流量与口径变化；贡献不代表原因。'};
 if(kind==='funnel') {
  result.stages=[{label:'访问 → 意向',from:current.visitors,to:current.leads,rate:ratio(current.leads,current.visitors)},{label:'意向 → 下单',from:current.leads,to:current.orders,rate:ratio(current.orders,current.leads)}];
  result.next='核对流失环节的用户路径与观察窗口；阶段数量不足以判断流失原因。';
 }
 if(kind==='monitor') {result.alerts=parts.filter(p=>p.rate!==null&&Math.abs(p.rate)>=context.threshold);result.notEvaluable=parts.filter(p=>p.rate===null);result.next='先核对刷新和口径，再检查异常分组；阈值命中不等于统计异常或业务原因。';}
 return result;
}
const api={catalog,analyze};root.BITemplates=api;if(typeof module!=='undefined') module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
