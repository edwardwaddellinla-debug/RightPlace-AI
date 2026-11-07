"""Fail closed before exposing billable model keys on a public network."""
import os

KEYS=('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY')
LOOPBACK=('127.0.0.1','localhost','::1')

def check_public_launch(env=None):
    e=os.environ if env is None else env
    host=e.get('HOST','127.0.0.1').strip().lower()
    billable=any(e.get(k) for k in KEYS)
    public=host not in LOOPBACK
    if public and billable and e.get('RIGHTPLACE_ALLOW_PUBLIC_PAID')!='yes':
        raise RuntimeError('Refusing public network exposure with billable AI keys. Add authentication and gateway spending controls before explicitly setting RIGHTPLACE_ALLOW_PUBLIC_PAID=yes.')
    return {'public_bind':public,'billable_provider_configured':billable,'blocked':False}
