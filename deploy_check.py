"""Read-only deployment readiness audit. No secrets printed or network calls made."""
import os, json
from public_launch_guard import check_public_launch
from pathlib import Path

def audit(env=None):
    e=os.environ if env is None else env
    providers=[name for name,key in [('OpenAI','OPENAI_API_KEY'),('Claude','ANTHROPIC_API_KEY'),('Gemini','GEMINI_API_KEY')] if e.get(key)]
    db=e.get('RIGHTPLACE_DB','rightplace.db')
    persistent=db.startswith('/data/') and e.get('RIGHTPLACE_PERSISTENT_DISK')=='yes'
    warnings=[]
    try:
        check_public_launch(e)
    except RuntimeError as exc:
        warnings.append(str(exc))
    if not providers: warnings.append('No AI provider key: real answers will not work.')
    if not persistent: warnings.append('Research history and usage counters may be lost on free/ephemeral hosting; do not promise persistence.')
    if not e.get('BRAVE_API_KEY'): warnings.append('Deep Solve web research is not connected.')
    warnings.append('Public deployment with billable keys is NOT approved: no user authentication, distributed abuse protection, or hard external spending cap.')
    warnings.append('Sleeping free hosting cannot run reliable hourly background research.')
    return {'ready_for_public_paid_launch':False,'configured_providers':providers,'database_path':db,'persistent_storage_verified':persistent,'warnings':warnings}

if __name__=='__main__':
    print(json.dumps(audit(),indent=2))
