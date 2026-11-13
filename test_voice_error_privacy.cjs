const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const code=html.slice(html.indexOf('const SR=window.SpeechRecognition'),html.indexOf("$('mic').onclick="));
const elements={};for(const k of ['mic','voiceStatus','question','askBtn'])elements[k]={value:'',textContent:'',classList:{toggle(){}},setAttribute(){},click(){}};
let instance,timer;class Speech{start(){instance=this;this.onstart()}abort(){}}
const ctx={answerInFlight:false,window:{isSecureContext:true,SpeechRecognition:Speech},setTimeout(fn){timer=fn;return 1},clearTimeout(){timer=null},alert(){},$:id=>elements[id]};vm.createContext(ctx);vm.runInContext(code,ctx);
vm.runInContext("mic('question')",ctx);instance.onerror({error:'private-provider-token-123'});
assert(!elements.voiceStatus.textContent.includes('private-provider-token-123'));
assert(elements.voiceStatus.textContent.includes('retry'));assert.equal(timer,null);
vm.runInContext("mic('question')",ctx);instance.onerror({error:'service-not-allowed'});
assert(elements.voiceStatus.textContent.includes('service blocked'));
console.log('PASS: speech provider errors do not leak untrusted error strings');
