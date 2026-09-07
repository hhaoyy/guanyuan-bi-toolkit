(function (root) {
  'use strict';
  const fields = ['day', 'store', 'orders', 'sales'];
  const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = value => new Intl.NumberFormat('zh-CN', {maximumFractionDigits: 2}).format(value);

  function columnsToRows(data) {
    if (!Array.isArray(data) || !Array.isArray(data[0])) throw new Error('缺少数据集：请将结果集绑定到 data[0]。');
    const columns = data[0];
    const byName = new Map();
    for (const column of columns) {
      if (!column || typeof column.name !== 'string' || !Array.isArray(column.data)) throw new Error('数据列结构异常。');
      if (byName.has(column.name)) throw new Error('出现重复字段名。');
      byName.set(column.name, column.data);
    }
    for (const field of fields) if (!byName.has(field)) throw new Error('字段缺失：' + field);
    const size = byName.get('day').length;
    if (fields.some(field => byName.get(field).length !== size)) throw new Error('数据列长度不一致。');
    const keys = new Set();
    return Array.from({length: size}, (_, i) => {
      const row = Object.fromEntries(fields.map(field => [field, byName.get(field)[i]]));
      if (typeof row.day !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(row.day)) throw new Error('统计日格式异常。');
      const parsed = new Date(row.day + 'T00:00:00Z');
      if (!Number.isFinite(parsed.getTime()) || parsed.toISOString().slice(0,10) !== row.day) throw new Error('统计日无效。');
      if (typeof row.store !== 'string' || !row.store.trim()) throw new Error('门店不能为空。');
      for (const field of ['orders','sales']) {
        if (row[field] === null || row[field] === undefined || !['number','string'].includes(typeof row[field]) || String(row[field]).trim() === '') throw new Error('指标存在缺失值。');
        row[field] = Number(row[field]);
        if (!Number.isFinite(row[field]) || row[field] < 0) throw new Error('指标必须为非负有限数字。');
      }
      if (!Number.isInteger(row.orders)) throw new Error('订单数必须为整数。');
      const key = JSON.stringify([row.day,row.store]);
      if (keys.has(key)) throw new Error('数据粒度重复：每个日期和门店只能有一行。');
      keys.add(key);
      return row;
    });
  }

  function summarize(rows, store = null) {
    const filtered = rows.filter(row => store === null || row.store === store);
    const orders = filtered.reduce((sum,row) => sum + row.orders,0);
    const sales = filtered.reduce((sum,row) => sum + row.sales,0);
    if (!Number.isFinite(orders) || !Number.isFinite(sales)) throw new Error('汇总结果超出数值范围。');
    const days = new Map(), stores = new Map();
    for (const row of filtered) {
      days.set(row.day,(days.get(row.day) || 0) + row.sales);
      stores.set(row.store,(stores.get(row.store) || 0) + row.sales);
    }
    return {orders,sales,average: orders === 0 ? null : sales/orders,
      days:[...days].sort((a,b) => a[0].localeCompare(b[0])),
      stores:[...stores].sort((a,b) => b[1]-a[1]),count:filtered.length};
  }

  function mount(container, data, options = {}) {
    const synthetic = options.synthetic === true;
    const title = options.title || '经营看板';
    container.onchange = null;
    const header = `<div class="topline"><span class="brand">◈ GUANYUAN BI TOOLKIT</span><span class="chip">${synthetic ? '100% 合成数据 · DEMO' : 'HTML BI STARTER'}</span></div>`;
    let rows;
    try { rows = columnsToRows(data); }
    catch (error) {
      container.innerHTML = `<main class="cafe">${header}<section class="state error" role="alert"><h2>数据暂时无法展示</h2><p>${escapeHtml(error.message)}</p><p>请按数据契约检查输入后重新加载。</p></section></main>`;
      return;
    }
    if (!rows.length) {
      container.innerHTML = `<main class="cafe">${header}<section class="state" role="status"><h2>这里还没有数据 ☕</h2><p>当前结果集为空。请检查筛选范围和数据刷新状态。</p></section></main>`;
      return;
    }
    const stores = [...new Set(rows.map(row => row.store))].sort();
    function draw(store) {
      const s = summarize(rows,store);
      const max = Math.max(...s.days.map(item => item[1]),1);
      const selectedIndex = store === null ? 0 : stores.indexOf(store)+1;
      const optionsHtml = ['全部门店',...stores].map((label,index) => `<option value="${index}"${index === selectedIndex ? ' selected' : ''}>${escapeHtml(label)}</option>`).join('');
      container.innerHTML = `<main class="cafe">${header}
        <section class="hero"><div><div class="eyebrow">A SMALL DASHBOARD, A CLEARER PICTURE</div><h1>${escapeHtml(title)} <span aria-hidden="true">☕</span></h1><p>${synthetic ? '宇宙很大，先看清今天卖了多少杯咖啡。' : '订单、销售额与每日趋势。'}</p></div><label><span class="scope-label">查看范围</span><select aria-label="门店范围">${optionsHtml}</select></label></section>
        <section class="kpis" aria-label="核心指标"><div class="kpi primary"><div class="label">累计销售额</div><div class="value">${number(s.sales)}<span class="unit">${synthetic ? '星币' : '金额单位见数据契约'}</span></div><div class="caption">所选范围 · 销售额合计</div></div><div class="kpi"><div class="label">累计订单</div><div class="value">${number(s.orders)}<span class="unit">单</span></div><div class="caption">${s.days.length} 个统计日</div></div><div class="kpi"><div class="label">客单价</div><div class="value">${s.average === null ? '—' : number(s.average)}<span class="unit">${synthetic ? '星币 / 单' : '金额 / 单'}</span></div><div class="caption">总销售额 ÷ 总订单</div></div></section>
        <section class="panels"><div class="panel"><div class="panel-head"><h2>每天，都有一杯好消息</h2><span class="sub">销售额趋势</span></div><div class="chart" aria-label="每日销售额">${s.days.map(([day,value]) => `<div class="bar-group"><span class="bar-number">${number(value)}</span><div class="bar" style="height:${Math.round(value/max*150)}px"></div><span class="bar-day">${escapeHtml(day.slice(5))}</span></div>`).join('')}</div></div><div class="panel"><div class="panel-head"><h2>门店小榜单</h2><span class="sub">按销售额</span></div><div class="ranking">${s.stores.map(([name,value],index) => `<div class="rank-row"><span class="rank-name"><span class="rank-dot">0${index+1}</span>${escapeHtml(name)}</span><span class="rank-value">${number(value)}</span></div>`).join('')}</div><p class="sub">同一统计范围，保持一致口径。</p></div></section>
        <div class="note">${synthetic ? '🪐 月球站与火星站均为虚构门店。所有数字由示例代码生成，可放心用于学习与演示。' : '统计口径、币种与时间范围以数据契约为准。'}</div>
        <footer><span>${escapeHtml(s.days[0][0])} — ${escapeHtml(s.days[s.days.length-1][0])}</span><span>让看板好看，让数字有出处。</span></footer></main>`;
    }
    try { draw(null); } catch (error) {
      container.innerHTML = `<main class="cafe">${header}<section class="state error" role="alert"><h2>汇总失败</h2><p>${escapeHtml(error.message)}</p></section></main>`;
      return;
    }
    container.onchange = event => {
      if (event.target.tagName !== 'SELECT') return;
      const index = Number(event.target.value);
      if (!Number.isInteger(index) || index < 0 || index > stores.length) return;
      draw(index === 0 ? null : stores[index-1]);
    };
  }

  function renderChart(data, clickFunc, config) {
    const container = root.document && root.document.getElementById('container');
    if (container) mount(container,data);
  }
  root.CafeDashboard = {columnsToRows,summarize,mount,escapeHtml};
  root.renderChart = renderChart;
  if (typeof module !== 'undefined' && module.exports) module.exports = root.CafeDashboard;
  if (typeof root.GDPlugin === 'function') new root.GDPlugin().init(renderChart);
})(typeof window !== 'undefined' ? window : globalThis);
