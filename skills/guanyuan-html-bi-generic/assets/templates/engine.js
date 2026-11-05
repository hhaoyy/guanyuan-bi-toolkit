(function(root) {
'use strict';
const catalog = {
 overview:{title:'经营总览',question:'整体表现如何，变化主要来自哪里？',fields:['orders','sales'],layout:'指标 → 周期对比 → 门店贡献 → 下一步'},
 funnel:{title:'转化漏斗',question:'同一批用户在哪个环节流失？',fields:['visitors','leads','orders'],layout:'同 cohort 阶段 → 转化率 → 最大流失环节 → 验证'},
 channels:{title:'渠道对比',question:'哪些渠道贡献规模，哪些转化较好？',fields:['visitors','orders','sales'],layout:'规模与效率 → 渠道矩阵 → 变化贡献 → 验证'},
 monitor:{title:'异常监控',question:'哪些分组偏离已确认的变化阈值？',fields:['sales'],layout:'规则状态 → 异常列表 → 对比证据 → 调查建议'}
};

const fmt=v=>v===null?'不可计算':new Intl.NumberFormat('zh-CN',{maximumFractionDigits:2}).format(v);
const divide=(a,b)=>b===0?null:a/b;
function enrich(a,rows,context,scope){
 const selected=rows.filter(r=>scope===null||r.group===scope);
 a.evidence=[];a.insights=[];a.actions=[];
 const evidence=(id,label,b,c,unit='')=>{const e={id,label,baseline:b,current:c,delta:b===null||c===null?null:c-b,unit};a.evidence.push(e);return e;};
 const finding=(id,title,detail,refs)=>a.insights.push({id,title,detail,evidenceIds:refs});
 const action=(id,label)=>a.actions.push({id,label,status:'ready'});
 const c=a.current,b=a.baseline;
 evidence('total',a.kind==='funnel'?'转化用户':'销售额',a.facts[0].baseline,a.facts[0].current);
 for(const [i,g] of a.groups.entries())evidence('group-'+i,g.group,g.baseline,g.current);
 if(a.kind==='overview'){
  const oldAverage=divide(b.sales,b.orders),newAverage=divide(c.sales,c.orders);
  evidence('orders','订单',b.orders,c.orders);evidence('average','客单价',oldAverage,newAverage);
  const losses=a.groups.filter(g=>g.delta<0).reduce((s,g)=>s-g.delta,0),gains=a.groups.filter(g=>g.delta>0).reduce((s,g)=>s+g.delta,0);
  finding('contribution',a.delta===0?'总体持平，仍需检查分组抵消':'先定位销售变化来自哪里',`销售额增减 ${fmt(a.delta)}；下降分组合计减少 ${fmt(losses)}，增长分组合计增加 ${fmt(gains)}。`,['total',...a.groups.map((_,i)=>'group-'+i)]);
  finding('drivers','订单量与客单价分别看',`订单 ${fmt(b.orders)} → ${fmt(c.orders)}；客单价 ${fmt(oldAverage)} → ${fmt(newAverage)}。${oldAverage===null||newAverage===null?'零订单周期无法拆解客单价影响。':'点击拆解查看量价影响，避免把分组贡献误当原因。'}`,['orders','average']);
  action('sales-drivers','执行：拆解订单量与客单价');
 }else if(a.kind==='funnel'){
  const pairs=[['visitors','leads','访问 → 意向'],['leads','orders','意向 → 下单']];
  a.stages=a.stages.map((stage,i)=>{const [from,to,label]=pairs[i],oldRate=divide(b[to],b[from]),newRate=divide(c[to],c[from]);evidence('stage-'+i,label,oldRate===null?null:oldRate*100,newRate===null?null:newRate*100,'个百分点');return {...stage,baselineRate:oldRate,changePP:oldRate===null||newRate===null?null:(newRate-oldRate)*100};});
  evidence('visitors','访问人数',b.visitors,c.visitors);
  const changed=a.stages.filter(s=>s.changePP!==null).sort((x,y)=>x.changePP-y.changePP),worst=changed.find(s=>s.changePP<0);
  finding('stage-change',worst?'优先检查 '+worst.label:'没有可确认的阶段转化率下降',a.stages.map(s=>`${s.label}：${fmt(s.baselineRate===null?null:s.baselineRate*100)}% → ${fmt(s.rate===null?null:s.rate*100)}%，变化 ${fmt(s.changePP)} 个百分点`).join('；'),['stage-0','stage-1']);
  finding('traffic','同时检查入口规模',`访问人数 ${fmt(b.visitors)} → ${fmt(c.visitors)}。人数最多的流失环节，不一定是本期恶化的环节。`,['visitors']);
  action('stage-decomposition','执行：分解入口与各阶段变化');
 }else if(a.kind==='channels'){
  for(const [i,g] of a.groups.entries()){
   const old=selected.find(r=>r.group===g.group&&r.period==='baseline'),now=selected.find(r=>r.group===g.group&&r.period==='current');
   const br=divide(old.orders,old.visitors),cr=divide(now.orders,now.visitors);
   evidence('traffic-'+i,g.group+' 访问',old.visitors,now.visitors);evidence('conversion-'+i,g.group+' 转化率',br===null?null:br*100,cr===null?null:cr*100,'个百分点');
   if(i<2)finding('channel-'+i,g.group+'：规模与效率',`访问 ${fmt(old.visitors)} → ${fmt(now.visitors)}；转化率 ${fmt(br===null?null:br*100)}% → ${fmt(cr===null?null:cr*100)}%；销售额增减 ${fmt(g.delta)}。`,['group-'+i,'traffic-'+i,'conversion-'+i]);
  }
  finding('cost-gap','尚不能据此调整投放预算','当前契约没有获客成本、收益周期或增量证据；转化率排名不能证明增加预算后的回报。',[]);
  action('channel-decomposition','执行：逐渠道拆解流量与转化');
 }else{
  const alerts=[...a.alerts].sort((x,y)=>Math.abs(y.delta)-Math.abs(x.delta));
  finding('threshold',alerts.length?`${alerts.length} 个分组命中变化阈值`:'没有分组命中指定阈值',alerts.length?alerts.map(g=>`${g.group}：${fmt(g.rate*100)}%，超过阈值 ${fmt((Math.abs(g.rate)-context.threshold)*100)} 个百分点，金额增减 ${fmt(g.delta)}`).join('；'):`变化率绝对值阈值为 ${fmt(context.threshold*100)}%。`,alerts.map(g=>'group-'+a.groups.indexOf(g)));
  finding('history-gap','持续性尚未验证',`只有两个聚合周期，不能判断异常持续时间或季节性。${a.notEvaluable.length} 个分组因零基期无法计算变化率。`,['total']);
  action('alert-priority','执行：按金额影响排列调查顺序');
 }
 a.actions.push({id:'daily-evidence',label:'逐日调查（需接入数据）',status:'needs_data',requires:['同范围逐日数据','刷新水位与完整性证据']});
 return a;
}
function executeInvestigation(kind,rows,context,scope,id){
 const a=analyze(kind,rows,context,scope);
 if(a.status!=='ok')return {status:'blocked',reason:'当前范围没有可分析数据'};
 const action=a.actions.find(x=>x.id===id);if(!action)throw new Error('调查动作不属于当前模板');
 if(action.status!=='ready')return {status:'needs_data',requires:action.requires,reason:'当前输入只有周期汇总；需要授权的逐日数据接口。'};
 const b=a.baseline,c=a.current;
 if(id==='sales-drivers'){
  const old=divide(b.sales,b.orders),now=divide(c.sales,c.orders);
  if(old===null||now===null)return {status:'not_evaluable',reason:'零订单周期无法执行量价分解'};
  return {status:'complete',method:'先变订单量，再变客单价；顺序分解，不是因果证明',rows:[{factor:'订单量影响',value:(c.orders-b.orders)*old},{factor:'客单价影响',value:c.orders*(now-old)}],total:a.delta};
 }
 if(id==='stage-decomposition'){
  if(b.visitors===0||b.leads===0||c.visitors===0||c.leads===0)return {status:'not_evaluable',reason:'零分母无法执行阶段分解'};
  const r1=b.leads/b.visitors,r2=b.orders/b.leads,n1=c.leads/c.visitors,n2=c.orders/c.leads;
  return {status:'complete',method:'先入口人数，再第一阶段，最后第二阶段；顺序影响可加总，不证明因果',rows:[{factor:'访问人数',value:(c.visitors-b.visitors)*r1*r2},{factor:'访问 → 意向',value:c.visitors*(n1-r1)*r2},{factor:'意向 → 下单',value:c.visitors*n1*(n2-r2)}],total:a.delta};
 }
 if(id==='channel-decomposition')return {status:'complete',method:'分解转化用户变化：先流量，再转化率；不等于预算收益',rows:a.groups.map(g=>{const old=rows.find(r=>r.group===g.group&&r.period==='baseline'),now=rows.find(r=>r.group===g.group&&r.period==='current');return {group:g.group,trafficEffect:old.visitors===0?null:(now.visitors-old.visitors)*old.orders/old.visitors,conversionEffect:old.visitors===0||now.visitors===0?null:now.visitors*(now.orders/now.visitors-old.orders/old.visitors),total:now.orders-old.orders};})};
 return {status:'complete',method:'按绝对金额影响排序；持续时间需要逐日证据',rows:[...a.alerts].sort((x,y)=>Math.abs(y.delta)-Math.abs(x.delta)).map(g=>({group:g.group,delta:g.delta,changePercent:g.rate*100,excessPP:(Math.abs(g.rate)-context.threshold)*100}))};
}
function investigate(kind,rows,context,scope,id){
 const out=executeInvestigation(kind,rows,context,scope,id);
 const money=context.unit||'金额单位待确认';
 out.units=kind==='overview'?{value:money}:kind==='funnel'?{value:'人'}:kind==='channels'?{trafficEffect:'人',conversionEffect:'人',total:'人'}:{delta:money,changePercent:'%',excessPP:'个百分点'};
 if(out.status!=='complete'){out.nextStep=out.status==='needs_data'?'先接入同范围的逐日数据，并核对刷新时间和完整性，再执行逐日调查。':'先核对缺失值和零分母；补齐可比数据后重新计算，不据此作原因判断。';return out;}
 if(kind==='overview'||kind==='funnel'){
  const losses=out.rows.filter(r=>r.value<0).sort((a,b)=>a.value-b.value);
  const lead=losses[0];
  out.nextStep=lead?(kind==='overview'?(lead.factor==='订单量影响'?'优先查看订单减少最多的分组及日期，再检查客流和营业时长。':'优先查看客单价下降的分组，再检查商品结构、折扣和退款口径。'):`优先调查「${lead.factor}」：${lead.factor==='访问人数'?'按来源和日期检查入口访问变化。':'按来源和日期检查该阶段转化变化，并核对观察窗口。'}`):'没有负向分解项；先核对增长或持平是否符合预期，不强行解释为下降。';
 }else if(kind==='channels'){
  const lead=out.rows.filter(r=>r.total<0).sort((a,b)=>a.total-b.total)[0];
  out.nextStep=lead?(lead.trafficEffect===null||lead.conversionEffect===null?`${lead.group} 存在零分母，先补齐可比访问数据。`:`优先检查 ${lead.group} 的${lead.trafficEffect<=lead.conversionEffect?'流量来源与逐日访问量':'转化路径与观察窗口'}；预算判断仍需成本和收益证据。`):'没有转化用户净减少的渠道；结合成本和收益证据再评估后续动作。';
 }else out.nextStep=out.rows.length?`先核对 ${out.rows[0].group} 的数据刷新与口径，再接入逐日数据判断偏离持续时间；不要仅因阈值命中调整业务。`:'当前没有命中阈值的分组；按原计划继续观察，无需人为生成异常处理任务。';
 return out;
}
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
 return enrich(result,rows,context,scope);
}
const api={catalog,analyze,investigate};root.BITemplates=api;if(typeof module!=='undefined') module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
