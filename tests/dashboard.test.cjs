const test = require('node:test');
const assert = require('node:assert/strict');
const {columnsToRows,summarize,mount,escapeHtml} = require('../examples/html-bi/dashboard.js');
const columns = rows => [['day','store','orders','sales'].map(name => ({name,data:rows.map(r => r[name])}))];
const rows = [{day:'2099-01-01',store:'Moon',orders:2,sales:20},{day:'2099-01-01',store:'Mars',orders:8,sales:160}];

test('ratios use summed denominators, and scope is exact', () => {
  const parsed=columnsToRows(columns(rows));
  assert.equal(summarize(parsed).average,18);
  assert.equal(summarize(parsed,'Moon').sales,20);
  assert.equal(summarize([{...rows[0],orders:0,sales:0}]).average,null);
});
test('missing, malformed and duplicate records fail visibly', () => {
  assert.throws(() => columnsToRows([]));
  for (const value of [null,'',false,-1,'n/a']) assert.throws(() => columnsToRows(columns([{...rows[0],sales:value}])));
  assert.throws(() => columnsToRows(columns([rows[0],rows[0]])));
  assert.throws(() => columnsToRows(columns([{...rows[0],day:'2099-02-30'}])));
  const data=columns(rows);data[0][2].data.pop();assert.throws(() => columnsToRows(data));
});
test('data labels are escaped and select events rerender', () => {
  const container={innerHTML:'',onchange:null};
  mount(container,columns([{...rows[0],store:'<script>fiction</script>'},rows[1]]));
  assert.ok(container.innerHTML.includes('&lt;script&gt;'));
  assert.ok(!container.innerHTML.includes('<script>'));
  mount(container,columns(rows));
  container.onchange({target:{tagName:'SELECT',value:'2'}});
  assert.ok(container.innerHTML.includes('value="2" selected'));
  assert.equal(escapeHtml('"&<>'), '&quot;&amp;&lt;&gt;');
});
test('empty and invalid data clear stale event handlers', () => {
  const container={innerHTML:'',onchange:()=>{}};
  mount(container,columns([]));
  assert.ok(container.innerHTML.includes('还没有数据'));
  assert.equal(container.onchange,null);
  mount(container,[]);
  assert.ok(container.innerHTML.includes('role="alert"'));
});
