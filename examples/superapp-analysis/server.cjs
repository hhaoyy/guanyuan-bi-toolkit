'use strict';
// Loopback-only synthetic demo, not a production authentication implementation.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const {createService}=require('../../skills/guanyuan-bi/assets/superapp/service.cjs');
const engine=require('../../skills/guanyuan-html-bi-generic/assets/templates/engine.js');
const root=path.resolve(__dirname,'../..');
const files=new Map([
 ['/',path.join(__dirname,'index.html')],['/app.js',path.join(__dirname,'app.js')],
 ['/client.js',path.join(root,'skills/guanyuan-bi/assets/superapp/client.js')],
 ...['engine.js','view.js','theme.css'].map(f=>['/'+f,path.join(root,'skills/guanyuan-html-bi-generic/assets/templates',f)])]);
const handle=createService({engine,authenticate:async()=>({id:'synthetic-demo-only'}),authorize:async(_,q)=>({allowed:q.sourceRef==='synthetic-cafe'&&q.window==='two-weeks',allowAI:false}),loadSnapshot:async()=>({revision:'synthetic-v1',observedAt:'2099-01-15T00:00:00Z',context:{currentLabel:'2099-01-08—01-14',baselineLabel:'2099-01-01—01-07',qualityConfirmed:true,cohortConfirmed:true,threshold:0.2,unit:'星币'},rows:[
 {period:'baseline',group:'月球站',visitors:1000,leads:400,orders:200,sales:4000},
 {period:'current',group:'月球站',visitors:800,leads:300,orders:150,sales:3000},
 {period:'baseline',group:'火星站',visitors:600,leads:240,orders:120,sales:2400},
 {period:'current',group:'火星站',visitors:700,leads:280,orders:140,sales:2800},
 {period:'baseline',group:'木星站',visitors:400,leads:160,orders:80,sales:1600},
 {period:'current',group:'木星站',visitors:400,leads:160,orders:80,sales:1600}]})});
const server=http.createServer(async(req,res)=>{
 res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
 if(req.url==='/api/demo/analyze'&&req.method==='POST'){
  let body='';try{for await(const chunk of req){body+=chunk;if(body.length>16000)throw Error('request_too_large');}const result=await handle(JSON.parse(body),{});res.setHeader('Content-Type','application/json');res.end(JSON.stringify(result));}catch(e){res.statusCode=400;res.setHeader('Content-Type','application/json');res.end(JSON.stringify({error:e.message}));}return;
 }
 const file=files.get(req.url);if(req.method!=='GET'||!file){res.statusCode=404;res.end();return;}
 res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.css')?'text/css':'application/javascript');res.end(fs.readFileSync(file));
});
const port=Number(process.env.PORT||8766);server.listen(port,'127.0.0.1',()=>console.log('Synthetic demo: http://127.0.0.1:'+port));
