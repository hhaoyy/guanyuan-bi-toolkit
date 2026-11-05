(function(root){
'use strict';
const E=root.BITemplates || (typeof require==='function'?require('./engine.js'):null);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const n=v=>v===null?'—':new Intl.NumberFormat('zh-CN',{maximumFractionDigits:2}).format(v);
const pct=v=>v===null?'不可计算':n(v*100)+'%';
function mount(container,kind,rows,context,scope=null,theme='business'){
 container.onclick=null;
 const themeName=['business','compact','dark'].includes(theme)?theme:'business';
 const wrap=body=>`<main class="bi-template ${themeName}">${body}</main>`;
 let a;try{a=E.analyze(kind,rows,context,scope);}catch(e){container.innerHTML=wrap(`<section role="alert"><h2>暂不能分析</h2><p>${esc(e.message)}</p></section>`);return;}
 if(a.status==='empty'){container.innerHTML=wrap('<section role="status"><h2>当前范围没有数据</h2><p>检查筛选范围，不将缺失当零。</p></section>');return;}
 const spec=E.catalog[kind];
 const kpi=(label,value,unit='')=>`<article class="bi-kpi"><span>${label}</span><strong>${value}</strong><small>${unit}</small></article>`;
 let metrics=kpi(kind==='funnel'?'转化用户':'销售额',n(a.current[kind==='funnel'?'orders':'sales']),kind==='funnel'?'人':esc(context.unit||'单位待确认'))+kpi('对比变化',pct(a.rate),'完整可比周期');
 if(kind==='overview')metrics+=kpi('订单数',n(a.current.orders),'单')+kpi('客单价',n(a.average),'总销售额 / 总订单');
 if(kind==='channels')metrics+=kpi('转化率',pct(a.current.visitors===0?null:a.current.orders/a.current.visitors),'转化用户 / 访问用户');
 if(kind==='monitor')metrics+=kpi('命中分组',n(a.alerts.length),'绝对变化率 ≥ '+pct(context.threshold));
 const rowTable=`<table><thead><tr><th>分组（点击下钻）</th><th>本期</th><th>基期</th><th>增减</th>${kind==='channels'?'<th>转化率</th>':''}</tr></thead><tbody>${a.groups.map((g,i)=>`<tr><td><button data-group="${i}">${esc(g.group)}</button></td><td>${n(g.current)}</td><td>${n(g.baseline)}</td><td>${n(g.delta)}</td>${kind==='channels'?`<td>${pct(g.conversion)}</td>`:''}</tr>`).join('')}</tbody></table>`;
 let body='';
 if(kind==='funnel') body=`<section class="bi-panel"><h2>同一 cohort 的阶段转化</h2>${a.stages.map(s=>`<div class="bi-stage"><h3>${s.label}</h3><strong>${pct(s.rate)}</strong><p>${n(s.from)} → ${n(s.to)} 人 · 流失 ${n(s.from-s.to)} 人</p><div class="bi-track"><i style="width:${(s.rate||0)*100}%"></i></div></div>`).join('')}</section>`;
 else if(kind==='monitor') body=`<section class="bi-panel"><h2>需要检查的分组</h2>${a.alerts.length?a.alerts.map(g=>`<p class="bi-alert">${esc(g.group)}：变化 ${pct(g.rate)}</p>`).join(''):'<p>没有分组命中指定阈值。</p>'}${a.notEvaluable.map(g=>`<p>${esc(g.group)}：基期为零，变化率不可计算。</p>`).join('')}</section>`;
 else if(kind==='overview') {const max=Math.max(...a.groups.map(g=>Math.abs(g.delta)),1);body=`<section class="bi-panel"><h2>销售额变化贡献</h2><p>展示有符号增减额，包含抵消变化。</p>${a.groups.map(g=>`<div class="bi-contribution"><span>${esc(g.group)} · ${n(g.delta)}</span><div class="bi-track"><i class="${g.delta<0?'negative':''}" style="width:${Math.abs(g.delta)/max*100}%"></i></div></div>`).join('')}</section>`;}
 else body=`<section class="bi-panel"><h2>规模与效率一起看</h2><p>按绝对变化贡献排序；高转化率不自动意味着可以扩大投入。</p>${rowTable}</section>`;
 const lead=a.groups[0];
 const finding=`本期${kind==='funnel'?'转化用户':'销售额'} ${n(a.facts[0].current)}，基期 ${n(a.facts[0].baseline)}，增减 ${n(a.delta)}（${pct(a.rate)}）。${lead&&lead.delta!==0?'绝对变化最大的分组是 '+esc(lead.group)+'，增减 '+n(lead.delta)+'。':''}`;
 container.innerHTML=wrap(`<header><span class="bi-eyebrow">QUESTION → EVIDENCE → ACTION</span><h1>${spec.title}</h1><p>${spec.question}</p><p>${esc(context.currentLabel)} 对比 ${esc(context.baselineLabel)} · ${scope===null?'全部分组':esc(scope)}</p>${scope!==null?'<button data-reset="1">← 返回全部</button>':''}</header><div class="bi-kpis">${metrics}</div><div class="bi-grid">${body}<aside class="bi-panel bi-insight"><span class="bi-eyebrow">分析发现 · 规则计算</span><h2>先看变化，再查原因</h2><p>${finding}</p><h3>下一步验证</h3><p>${esc(a.next)}</p><small>当前证据支持描述与分解，不支持因果判断。</small></aside></div>${kind!=='channels'?`<section class="bi-panel bi-detail"><h2>对比证据</h2>${rowTable}</section>`:''}<footer>${esc(context.evidenceLabel||'来源与刷新时间待确认')} · 当前筛选范围内重新计算</footer>`);
 container.onclick=e=>{const b=e.target.closest&&e.target.closest('button');if(!b)return;if(b.dataset.reset)mount(container,kind,rows,context,null,themeName);else if(b.dataset.group!==undefined){const g=a.groups[Number(b.dataset.group)];if(g)mount(container,kind,rows,context,g.group,themeName);}};
}
const api={mount};root.BITemplateView=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
