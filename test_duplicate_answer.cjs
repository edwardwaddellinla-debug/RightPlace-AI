const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const start=html.indexOf('let answerInFlight=false;');
const end=html.indexOf("$('moreBtn').onclick",start);
assert(start>=0&&end>start);
let resolveAnswer, calls=0;
const elements={question:{value:'First question'},askBtn:{disabled:false},afterAnswer:{classList:{toggle(){}}},feedback:{classList:{toggle(){}}}};
const ctx={$:id=>elements[id],answer:()=>{calls++;return new Promise(resolve=>resolveAnswer=resolve)},currentQ:'',followupLog:[]};
vm.createContext(ctx);vm.runInContext(html.slice(start,end),ctx);
(async()=>{
 const p=elements.askBtn.onclick();
 assert.equal(calls,1);assert.equal(elements.askBtn.disabled,true);
 elements.question.value='Second question';await elements.askBtn.onclick();assert.equal(calls,1,'concurrent request blocked');
 resolveAnswer(true);await p;assert.equal(elements.askBtn.disabled,false);
 const p2=elements.askBtn.onclick();assert.equal(calls,2,'new request permitted after completion');resolveAnswer(false);await p2;
 console.log('PASS: duplicate answer requests blocked, next request permitted after completion');
})().catch(e=>{console.error(e);process.exit(1)});
