'use strict';
const $=id=>document.getElementById(id),esc=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names={factor:'分解项',value:'影响量',group:'分组',trafficEffect:'流量影响',conversionEffect:'转化率影响',total:'转化用户增减',baseline:'基期',current:'本期',delta:'增减',changePercent:'变化率',excessPP:'超阈值幅度'};
function table(rows,units={}){if(!rows?.length)return '<p>无命中项目。</p>';const keys=Object.keys(rows[0]);return '<table><thead><tr>'+keys.map(k=>'<th>'+esc((names[k]||k)+(units[k]?'（'+units[k]+'）':''))+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+keys.map(k=>'<td>'+esc(typeof r[k]==='number'?Number(r[k].toFixed(3)):r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table>';}
const client=BIAnalysisClient.controller({transport:async(payload,{signal})=>{const r=await fetch('/api/demo/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal});if(!r.ok)throw Error('demo_request_failed');return r.json();},onState:s=>{
 $('status').textContent=s.message||'分析已更新';$('result').innerHTML='';
 if(s.status!=='ready')return;
 const r=s.result;
 $('status').textContent=`${r.mode==='ai'?'AI 辅助解释':'本地诊断'} · 数据版本 ${r.revision} · 生成于 ${new Date(r.generatedAt).toLocaleTimeString()}`;
 $('result').innerHTML=r.analysis.insights.map(f=>`<article><h2>${esc(f.title)}</h2><p>${esc(f.detail)}</p><small class="muted">证据：${esc(f.evidenceIds.map(id=>r.analysis.evidence.find(e=>e.id===id)?.label||id).join('、')||'当前数据范围的限制')}</small></article>`).join('')+'<article><h2>继续调查</h2>'+r.analysis.actions.map(a=>a.status==='ready'?`<button data-action="${esc(a.id)}">${esc(a.label)}</button>`:`<p><button disabled>${esc(a.label)}</button><span class="muted">暂不可执行。需补充：${esc((a.requires||[]).join('、'))}。</span></p>`).join('')+'</article>'+(r.investigation?`<article><h2>调查执行结果</h2><p>${esc(r.investigation.method||r.investigation.reason)}</p>${r.investigation.rows?table(r.investigation.rows,r.investigation.units):''}<h3>下一步建议</h3><p>${esc(r.investigation.nextStep||'核对调查返回的证据后决定下一步。')}</p>${r.investigation.requires?'<p>需要补充：'+esc(r.investigation.requires.join('、'))+'</p>':''}</article>`:'')+(r.ai?`<article><h2>AI 解释</h2><p>${esc(r.ai.summary)}</p><small>${esc(r.ai.notice)}</small></article>`:'')+'<details><summary>查看计算证据与数据时间</summary><p>'+esc(r.observedAt)+'</p>'+table(r.analysis.evidence.map(e=>({group:e.label,baseline:e.baseline,current:e.current,delta:e.delta})))+'</details>';
 }});
function context(){client.autoRefresh($('auto').checked?30000:0,$('mode').value);client.setContext({template:$('kind').value,scope:$('scope').value||null,sourceRef:'synthetic-cafe',window:'two-weeks'});if($('auto').checked)client.run($('mode').value);}
for(const id of ['kind','scope','mode'])$(id).addEventListener('change',context);
$('refresh').onclick=()=>client.run($('mode').value);
$('auto').onchange=()=>{client.autoRefresh($('auto').checked?30000:0,$('mode').value);if($('auto').checked)client.run($('mode').value);};
$('result').onclick=e=>{const b=e.target.closest('button[data-action]');if(b&&!b.disabled)client.run($('mode').value,b.dataset.action);};
window.addEventListener('pagehide',()=>client.dispose());context();client.run();
