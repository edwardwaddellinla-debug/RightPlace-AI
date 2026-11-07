#!/usr/bin/env python3
"""End-to-end local HTTP smoke test; no API keys or external calls needed."""
import json, os, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
with socket.socket() as s:
    s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
with tempfile.TemporaryDirectory() as tmp:
    env=os.environ.copy()
    for key in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','BRAVE_API_KEY'):
        env.pop(key,None)
    env.update(HOST='127.0.0.1',PORT=str(port),RIGHTPLACE_DB=str(Path(tmp)/'smoke.db'))
    process=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        base=f'http://127.0.0.1:{port}'
        for _ in range(50):
            if process.poll() is not None:raise RuntimeError('Server exited before readiness')
            try:
                with urllib.request.urlopen(base+'/api/health',timeout=.4) as response:
                    health=json.load(response)
                break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('Server did not start')
        assert health['ok'] and not health['ai_providers'],health
        with urllib.request.urlopen(base+'/',timeout=3) as response:
            page=response.read().decode()
        assert 'id="mic"' in page and 'id="askBtn"' in page
        request=urllib.request.Request(base+'/api/ask',data=json.dumps({'question':'Can you hear me?'}).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(request,timeout=3) as response:
            answer=json.load(response)
        assert answer['mode']=='demo' and answer['results']==[],answer
        print('PASS: live local HTTP server, homepage, health, and honest no-key answer')
    finally:
        process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait()
