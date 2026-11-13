const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
const code=html.slice(html.indexOf('const SR=window.SpeechRecognition'),html.indexOf("$('mic').onclick="));
let speech,clicks=0,stops=0,aborts=0;
const els={};for(const key of ['mic','voiceStatus','question','askBtn'])els[key]={value:'',textContent:'',classList:{toggle(){}},setAttribute(){},click(){clicks++}};
class Speech{constructor(){speech=this}start(){this.onstart()}stop(){stops++;this.onend()}abort(){aborts++}}
const ctx={window:{isSecureContext:true,SpeechRecognition:Speech},answerInFlight:false,$:id=>els[id],setTimeout:()=>1,clearTimeout(){},alert(){}};
vm.createContext(ctx);vm.runInContext(code,ctx);
const tap=()=>vm.runInContext("mic('question')",ctx);
tap();speech.onresult({results:[[{transcript:'How do I fix my truck?'}]]});tap();
assert.equal(stops,1);assert.equal(aborts,0);assert.equal(clicks,1);assert.equal(els.question.value,'How do I fix my truck?');
tap();tap();assert.equal(aborts,1);assert.equal(clicks,1);
console.log('PASS: tap to finish submits recognized speech; empty tap cancels');
