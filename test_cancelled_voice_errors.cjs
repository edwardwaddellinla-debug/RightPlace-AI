// Regression guard: delayed browser speech errors must not affect a cancelled session.
const fs=require('fs'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
assert.match(html,/r\.onerror=e=>\{if\(activeSpeech!==r\)return;/);
assert.match(html,/r\.onend=\(\)=>\{clearTimeout\(timeout\);if\(activeSpeech!==r\)return;/);
assert.match(html,/r\.onresult=e=>\{if\(failed\|\|activeSpeech!==r\)return;/);
console.log('Cancelled speech sessions ignore delayed error, result, and end callbacks.');
