const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const code=html.slice(html.indexOf('async function api('),html.indexOf('async function answer('));
async function run(){
 let clock,cleared=false,opts;
 const ctx={AbortController,JSON,Error,setTimeout:f=>(clock=f,1),clearTimeout:()=>{cleared=true},fetch:async(path,o)=>{opts=o;return {ok:true,json:async()=>({answer:'ready'})}}};
 vm.createContext(ctx);vm.runInContext(code,ctx);
 let r=await vm.runInContext("api('/api/ask',{question:'test'})",ctx);assert.equal(r.answer,'ready');assert(opts.signal);assert(cleared);
 cleared=false;ctx.fetch=async()=>new Promise((resolve,reject)=>{ctx.pendingReject=reject});
 const pending=vm.runInContext("api('/api/ask',{question:'test'})",ctx);
 clock();ctx.pendingReject(Object.assign(new Error('aborted'),{name:'AbortError'}));
 await assert.rejects(pending,/timed out after 45 seconds/);assert(cleared);
 console.log('PASS: API success and timeout recovery');
}
run().catch(e=>{console.error(e);process.exit(1)});
