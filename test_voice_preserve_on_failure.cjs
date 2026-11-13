const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
const code=html.slice(html.indexOf('const SR=window.SpeechRecognition'),html.indexOf("$('mic').onclick="));
let speech,timeoutFn,clicks=0;
const els={};for(const id of ['mic','voiceStatus','question','askBtn'])els[id]={value:'',textContent:'',classList:{toggle(){}},setAttribute(){},click(){clicks++}};
class Speech{constructor(){speech=this}start(){this.onstart()}stop(){this.onend()}abort(){}}
const ctx={window:{isSecureContext:true,SpeechRecognition:Speech},answerInFlight:false,$:id=>els[id],setTimeout:fn=>(timeoutFn=fn,1),clearTimeout(){},alert(){}};
vm.createContext(ctx);vm.runInContext(code,ctx);
function start(){vm.runInContext("mic('question')",ctx)}
start();speech.onresult({results:[[{transcript:'My truck loses power'}]]});speech.onerror({error:'network'});
assert.equal(els.question.value,'My truck loses power');assert.equal(clicks,0);assert.match(els.voiceStatus.textContent,/saved below/);
start();speech.onresult({results:[[{transcript:'under load'}]]});timeoutFn();
assert.equal(els.question.value,'My truck loses power under load');assert.equal(clicks,0);
start();speech.onerror({error:'network'});assert.equal(els.question.value,'My truck loses power under load');
console.log('PASS: speech failure/timeout retains recognized words without auto-submitting');
