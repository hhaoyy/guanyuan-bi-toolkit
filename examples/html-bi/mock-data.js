// Entirely synthetic: fixed fictional values, no external input and no network.
(function () {
  'use strict';
  const moon = [40,48,44,56,60,68,72];
  const mars = [24,28,32,30,38,42,46];
  const rows = moon.flatMap((orders,index) => [
    {day:`2099-01-0${index+1}`,store:'月球站',orders,sales:orders*15},
    {day:`2099-01-0${index+1}`,store:'火星站',orders:mars[index],sales:mars[index]*18}
  ]);
  const columns = records => [['day','store','orders','sales'].map(name => ({name,data:records.map(row => row[name])}))];
  const container = document.getElementById('container');
  const draw = data => CafeDashboard.mount(container,data,{synthetic:true,title:'星际咖啡店 · 经营手记'});
  document.getElementById('demo-reset').onclick = () => draw(columns(rows));
  document.getElementById('demo-empty').onclick = () => draw(columns([]));
  document.getElementById('demo-error').onclick = () => draw([[{name:'day',data:['2099-01-01']}]]);
  draw(columns(rows));
})();
