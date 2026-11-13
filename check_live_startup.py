"""Local deployment smoke check. Never calls paid AI providers or prints secrets."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parent

def available_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

def check():
    port = available_port()
    with tempfile.TemporaryDirectory() as folder:
        env = dict(os.environ)
        for name in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'BRAVE_API_KEY'):
            env.pop(name, None)
        env.update(HOST='127.0.0.1', PORT=str(port), RIGHTPLACE_DB=str(Path(folder)/'test.db'), PYTHONUNBUFFERED='1')
        proc = subprocess.Popen([sys.executable, str(ROOT/'server.py')], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            base=f'http://127.0.0.1:{port}'
            for attempt in range(45):
                if proc.poll() is not None:
                    raise RuntimeError(f'Server exited before becoming ready (exit {proc.returncode})')
                try:
                    with urllib.request.urlopen(base+'/api/health', timeout=1) as response:
                        health=json.load(response)
                    break
                except (OSError, ValueError):
                    time.sleep(.2)
            else:
                raise RuntimeError('Health endpoint did not respond within 9 seconds')
            assert health['ok'] is True, 'Health endpoint returned unhealthy status'
            assert health['ai_providers'] == [], 'Smoke check must not use provider keys'
            with urllib.request.urlopen(base+'/', timeout=2) as response:
                page=response.read().decode('utf-8')
            assert '<html' in page.lower(), 'Home page is not HTML'
            print('PASS: Server starts and responds to /api/health')
            print('PASS: Home page loads as HTML')
            print('PASS: Smoke test runs without AI keys or paid API calls')
        finally:
            proc.terminate()
            try:proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill();proc.communicate()

if __name__=='__main__':
    check()
