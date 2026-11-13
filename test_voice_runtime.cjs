const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const code=html.slice(html.indexOf('const SR=window.SpeechRecognition'),html.indexOf("$('mic').onclick="));
function setup({secure=true,supported=true}={}){
 let clicks=0, timer, instance;
 const elements={};for(const k of ['mic','voiceStatus','question','askBtn'])elements[k]={value:'',textContent:'',attributes:{},classes:new Set(),classList:{toggle(name,on){if(on)this.owner.classes.add(name);else this.owner.classes.delete(name)}},setAttribute(k,v){this.attributes[k]=v},click(){clicks++}};
 for(const v of Object.values(elements))v.classList.owner=v;
 class Speech{constructor(){instance=this}start(){this.onstart()}stop(){this.onend()}abort(){/* simulate browser that never fires onend */}}
 const context={answerInFlight:false,window:{isSecureContext:secure,SpeechRecognition:supported?Speech:undefined},setTimeout(fn){timer=fn;return 1},clearTimeout(){timer=null},alert(){},$:id=>elements[id],console};
 vm.createContext(context);vm.runInContext(code,context);
 return {mic:()=>vm.runInContext("mic('question')",context),get instance(){return instance},get clicks(){return clicks},get timer(){return timer},elements};
}
let x=setup();x.mic();assert(x.elements.mic.classes.has('listening'));x.instance.onerror({error:'not-allowed'});x.instance.onend();assert(!x.elements.mic.classes.has('listening'));assert(x.elements.voiceStatus.textContent.includes('permission denied'));assert.equal(x.clicks,0);assert.equal(x.timer,null);const errored=x.instance;x.mic();assert.notEqual(x.instance,errored);assert(x.elements.mic.classes.has('listening'));
x=setup();x.mic();x.instance.onresult({results:[[{transcript:'How do I repair a faucet?'}]]});x.instance.onend();assert.equal(x.clicks,1);assert.equal(x.elements.question.value,'How do I repair a faucet?');
x=setup();x.mic();x.instance.onresult({results:[[{transcript:'First guess'}]]});x.instance.onresult({results:[[{transcript:'Corrected final question'}]]});x.instance.onend();assert.equal(x.elements.question.value,'Corrected final question');assert.equal(x.clicks,1);
x=setup();x.mic();x.timer();x.instance.onresult({results:[[{transcript:'late transcript'}]]});assert.equal(x.elements.question.value,'');
x=setup();x.mic();x.timer();assert(!x.elements.mic.classes.has('listening'));assert(x.elements.voiceStatus.textContent.includes('timed out'));assert.equal(x.clicks,0);const old=x.instance;x.mic();assert.notEqual(x.instance,old);old.onend();assert(x.elements.mic.classes.has('listening'));x.instance.onend();
x=setup();x.elements.question.value='Existing draft';x.mic();x.instance.onresult({results:[[{transcript:'spoken addition'}]]});x.instance.onend();assert.equal(x.clicks,0);assert.equal(x.elements.question.value,'Existing draft spoken addition');assert(x.elements.voiceStatus.textContent.includes('Review it'));
x=setup();x.mic();const cancelled=x.instance;x.mic();assert(!x.elements.mic.classes.has('listening'));assert(x.elements.voiceStatus.textContent.includes('cancelled'));assert.equal(x.timer,null);cancelled.onresult({results:[[{transcript:'ignore cancelled'}]]});cancelled.onend();assert.equal(x.clicks,0);assert.equal(x.elements.question.value,'');
x=setup({secure:false});x.mic();assert(!x.instance);assert(x.elements.voiceStatus.textContent.includes('HTTPS'));
x=setup({supported:false});x.mic();assert(!x.instance);assert(x.elements.voiceStatus.textContent.includes('unavailable'));
console.log('PASS: 10 runtime microphone scenarios (permission denial, transcript submission, timeout, HTTPS, unsupported browser)');
