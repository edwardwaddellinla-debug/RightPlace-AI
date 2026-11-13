"""Require owner authentication for a billable deployment on a public interface."""
import base64
import binascii
import hashlib
import hmac
import os

KEYS=('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','BRAVE_API_KEY')
LOOPBACK=('127.0.0.1','localhost','::1')

def private_pilot_configured(env=None):
    e=os.environ if env is None else env
    password=e.get('RIGHTPLACE_PRIVATE_PASSWORD','')
    return 24 <= len(password) <= 128 and password.isascii() and all(33 <= ord(c) <= 126 for c in password)

def private_pilot_required(env=None):
    e=os.environ if env is None else env
    return e.get('HOST','127.0.0.1').strip().lower() not in LOOPBACK and any(e.get(k) for k in KEYS)

def owner_authorized(headers, env=None):
    e=os.environ if env is None else env
    if not private_pilot_configured(e) or len(headers)!=1:
        return False
    scheme, _, encoded=headers[0].partition(' ')
    if scheme.lower()!='basic' or not encoded or len(encoded)>256:
        return False
    try:
        presented=base64.b64decode(encoded,validate=True)
    except (ValueError,binascii.Error):
        return False
    expected=('owner:'+e['RIGHTPLACE_PRIVATE_PASSWORD']).encode('ascii')
    return hmac.compare_digest(hashlib.sha256(presented).digest(),hashlib.sha256(expected).digest())

def check_public_launch(env=None):
    e=os.environ if env is None else env
    public=e.get('HOST','127.0.0.1').strip().lower() not in LOOPBACK
    billable=any(e.get(k) for k in KEYS)
    if public and billable and not private_pilot_configured(e):
        raise RuntimeError('Refusing public startup with billable keys unless a private pilot password is configured.')
    return {'public_bind':public,'billable_provider_configured':billable,'blocked':False}
