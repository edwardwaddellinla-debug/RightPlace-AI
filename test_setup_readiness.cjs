const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const fn=html.match(/function voiceReadiness\(\)\{[\s\S]*?\n\}/)[0];
const elements={connection:{textContent:''},setupStatus:{textContent:''}};
const base={SR:function(){},$:id=>elements[id],AbortController, setTimeout,clearTimeout};
async function run(secure,providers,offline=false){
 const context={...base,window:{isSecureContext:secure},fetch:async()=>{if(offline)throw Error('offline');return {ok:true,json:async()=>({ai_providers:providers})}}};
 vm.createContext(context);vm.runInContext(fn+'\n'+html.match(/async function checkReadiness\(\)\{[\s\S]*?\n\}/)[0],context);
 await context.checkReadiness();return {...elements,voice:context.voiceReadiness()};
}
(async()=>{
 let x=await run(false,[]);assert.match(x.setupStatus.textContent,/HTTPS/);assert.match(x.connection.textContent,/Preview/);
 x=await run(true,['OpenAI']);assert.match(x.setupStatus.textContent,/not yet verified/);assert.match(x.connection.textContent,/configured/);
 x=await run(true,[],true);assert.match(x.setupStatus.textContent,/unreachable/);
 console.log('PASS: 3 setup readiness scenarios');
})().catch(e=>{console.error(e);process.exit(1)});
