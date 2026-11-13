"""Offline deployment preflight; never prints secret values."""
import os
from pathlib import Path
from public_launch_guard import check_public_launch

KEYS=('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY')

def inspect_deployment(env=None, root=None):
    env=os.environ if env is None else env
    root=Path(__file__).resolve().parent if root is None else Path(root)
    findings=[]
    for filename in ('server.py','index.html','Dockerfile','render.yaml'):
        if not (root/filename).is_file():
            findings.append('Missing required file: '+filename)
    try:
        check_public_launch(env)
    except RuntimeError:
        findings.append('Public paid-AI deployment blocked by launch guard; do not bypass without authentication and shared spending controls.')
    # A free Render container does not provide durable local SQLite storage.
    # Research jobs and deletion state must not be represented as persistent.
    render_file=root/'render.yaml'
    if render_file.is_file():
        render_text=render_file.read_text(encoding='utf-8')
        if 'plan: free' in render_text and 'disk:' not in render_text:
            findings.append('Render free service has ephemeral SQLite storage: research jobs and saved records may disappear on redeploy or restart. Use a durable database before promising persistence.')
    configured=[name for name,key in [('OpenAI',KEYS[0]),('Claude',KEYS[1]),('Gemini',KEYS[2])] if env.get(key)]
    if not configured:
        findings.append('No AI provider configured: site will show preview answers only.')
    if env.get('RIGHTPLACE_ALLOW_PUBLIC_PAID')=='yes' and env.get('HOST','127.0.0.1') not in ('127.0.0.1','localhost','::1'):
        findings.append('Public paid-AI override enabled: per-IP limits are not sufficient protection against distributed abuse.')
    return {'ready_for_real_ai':bool(configured) and not findings, 'configured_providers':configured, 'findings':findings}

if __name__=='__main__':
    import json
    print(json.dumps(inspect_deployment(),indent=2))
