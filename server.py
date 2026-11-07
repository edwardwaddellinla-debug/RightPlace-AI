#!/usr/bin/env python3
"""RightPlace AI MVP: stdlib HTTP server, optional real model/search APIs, SQLite research jobs."""
import concurrent.futures, datetime, hashlib, hmac, html, json, os, re, secrets, sqlite3, threading, time, urllib.error, urllib.parse, urllib.request, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from parts_registry import setup_parts, lookup as lookup_parts
from identifiers import setup_identifiers, lookup_identifier
from public_launch_guard import check_public_launch

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
INTERVAL = max(900, int(os.environ.get("RESEARCH_INTERVAL_SECONDS", "3600")))


MAX_ROUNDS=max(1,min(8,int(os.environ.get('RESEARCH_MAX_ROUNDS','6'))))
MODELS={"OpenAI":("OPENAI_API_KEY","OPENAI_MODEL","gpt-4.1-mini"),"Claude":("ANTHROPIC_API_KEY","CLAUDE_MODEL","claude-haiku-4-5"),"Gemini":("GEMINI_API_KEY","GEMINI_MODEL","gemini-2.5-flash")}
DB_LOCK=threading.RLock()
# A conservative safeguard against accidental API spending. Limits are per server instance;
# use gateway protection and authenticated accounts before public deployment.
LIMITS={'/api/ask':(12,3600),'/api/benchmark':(4,3600),'/api/jobs':(5,3600)}
RATE_BUCKETS={}
RATE_LOCK=threading.Lock()
MAX_DAILY_AI_CALLS=max(1,int(os.environ.get('MAX_DAILY_AI_CALLS','100')))

def permit_request(route, address):
    max_req, window=LIMITS[route]
    key=(route,address)
    stamp=time.monotonic()
    with RATE_LOCK:
        times=[t for t in RATE_BUCKETS.get(key,[]) if stamp-t<window]
        if len(times)>=max_req:
            RATE_BUCKETS[key]=times
            return False
        times.append(stamp)
        RATE_BUCKETS[key]=times
    return True

def claim_ai_budget():
    # Atomic SQLite counter shared across threads, persists through restarts.
    day=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    with DB_LOCK:
        with connect() as c:
            current=c.execute('SELECT n FROM ai_budget WHERE day=?',(day,)).fetchone()
            if current and current['n']>=MAX_DAILY_AI_CALLS:return False
            c.execute('INSERT INTO ai_budget(day,n) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET n=n+1',(day,))
            return True

SYSTEM=("You are RightPlace AI. Answer accurately in clear everyday language, 1-3 concise sentences unless steps are explicitly requested. "
        "Never repeat steps already rejected, never market or sell products, do not guess precise specifications. "
        "Only ask essential clarifying questions. For legal, financial, health and hazardous work include essential cautions but no unnecessary lecture. "
        "Distinguish verified facts from estimates and uncertainty. Do not invent research, quotes or citations. "
        "For parts, never invent OEM numbers, supersessions, interchange, or fitment; distinguish evidence from confirmed compatibility. "
        "Provide useful how-to steps for ordinary tasks, with proportionate safety warnings; discuss sensitive or illegal topics factually "
        "without giving operational instructions that directly enable serious harm. Disclaimers do not replace safety checks.")

def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB,timeout=15)
    con.row_factory=sqlite3.Row
    return con

def setup():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,question TEXT NOT NULL,details TEXT NOT NULL DEFAULT '',status TEXT NOT NULL,round INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,next_run REAL NOT NULL,summary TEXT NOT NULL DEFAULT '',stopped INTEGER NOT NULL DEFAULT 0);CREATE TABLE IF NOT EXISTS findings(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,created_at TEXT NOT NULL,query TEXT NOT NULL,source_url TEXT NOT NULL,title TEXT NOT NULL,snippet TEXT NOT NULL,UNIQUE(job_id,source_url));CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,round INTEGER NOT NULL,created_at TEXT NOT NULL,notes TEXT NOT NULL,urls_checked INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS job_tokens(job_id TEXT PRIMARY KEY,token_hash TEXT NOT NULL);CREATE TABLE IF NOT EXISTS ai_budget(day TEXT PRIMARY KEY,n INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS tried_steps(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,created_at TEXT NOT NULL,step TEXT NOT NULL,UNIQUE(job_id,step));''')

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')

def token_hash(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def check_token(jid, token):
    if not token or not jid:return False
    with connect() as c:
        row=c.execute('SELECT token_hash FROM job_tokens WHERE job_id=?',(jid,)).fetchone()
        return bool(row and hmac.compare_digest(row['token_hash'],token_hash(token)))

def normalize_answer(answer):
    return re.sub(r'[^a-z0-9]+',' ', str(answer).lower()).strip()

def score_known_answer(answer, expected):
    # A narrow, transparent self-test for straightforward factual items, not a universal truth judge.
    # Match a short expected phrase on word boundaries, rejecting empty references.
    normalized=normalize_answer(answer)
    target=normalize_answer(expected)
    if not target or len(target)<2:return None
    return bool(re.search(r'(?<!\w)'+re.escape(target)+r'(?!\w)', normalized))


def post_json(url,payload,headers=None,timeout=35):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',**(headers or {})},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def get_json(url,headers=None,timeout=18):
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=timeout) as r:return json.load(r)

def ask_model(name,prompt,system=SYSTEM,timeout=35):
    keyenv,modelenv,default=MODELS[name]; key=os.getenv(keyenv)
    if not key:return {'provider':name,'available':False,'error':'API key not configured'}
    if not claim_ai_budget():return {'provider':name,'available':False,'error':'Daily AI request budget reached. Try again tomorrow.'}
    model=os.getenv(modelenv,default); t=time.perf_counter()
    try:
        if name=='OpenAI':
            d=post_json('https://api.openai.com/v1/responses',{'model':model,'instructions':system,'input':prompt,'max_output_tokens':650}, {'Authorization':'Bearer '+key},timeout=timeout)
            answer=''.join(p.get('text','') for x in d.get('output',[]) for p in x.get('content',[]) if p.get('type')=='output_text')
        elif name=='Claude':
            d=post_json('https://api.anthropic.com/v1/messages',{'model':model,'system':system,'max_tokens':650,'messages':[{'role':'user','content':prompt}]},{'x-api-key':key,'anthropic-version':'2023-06-01'},timeout=timeout)
            answer=''.join(x.get('text','') for x in d.get('content',[]) if x.get('type')=='text')
        else:
            d=post_json('https://generativelanguage.googleapis.com/v1beta/models/'+urllib.parse.quote(model,safe='')+':generateContent',{'systemInstruction':{'parts':[{'text':system}]},'contents':[{'role':'user','parts':[{'text':prompt}]}],'generationConfig':{'maxOutputTokens':650}},{'x-goog-api-key':key},timeout=timeout)
            answer=''.join(p.get('text','') for c in d.get('candidates',[]) for p in c.get('content',{}).get('parts',[]))
        return {'provider':name,'available':True,'model':model,'answer':answer.strip(),'seconds':round(time.perf_counter()-t,2)} if answer.strip() else {'provider':name,'available':True,'model':model,'error':'Provider returned no answer text','seconds':round(time.perf_counter()-t,2)}
    except Exception as e:
        return {'provider':name,'available':True,'error':str(e)[:240],'seconds':round(time.perf_counter()-t,2)}

def model_batch(question,compare=False,expected=''):
    names=[n for n,v in MODELS.items() if os.getenv(v[0])]
    if not names:return {'mode':'demo','answer':'This demo needs a connected AI provider for a researched answer. Open the Deep Solve tab to create a research job, or configure an API key on the server.','results':[]}
    if not compare:
        # Try all configured providers, stopping on the first useful answer.
        # Three 12-second network attempts fit within the browser's 45-second deadline.
        # A failed call still consumes one daily AI budget unit.
        results=[]
        for name in names:
            result=ask_model(name,question,timeout=12)
            results.append(result)
            if result.get('available') and isinstance(result.get('answer'),str) and result['answer'].strip() and not result.get('error'):
                break
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(names)) as pool:
            results=list(pool.map(lambda n:ask_model(n,question),names))
    if expected.strip():
        for r in results:
            if r.get('answer'):
                r['reference_match']=score_known_answer(r['answer'],expected)
    good=[r for r in results if r.get('available') and isinstance(r.get('answer'),str) and r['answer'].strip() and not r.get('error')]
    # Only label the fastest *reference match* if the caller supplied a test reference.
    passing=[r for r in good if r.get('reference_match') is True] if expected.strip() else []
    best=min(passing if passing else good,key=lambda x:x['seconds']) if good else None
    # Fastest is only a latency measurement, not proof of accuracy.
    return {'mode':'live' if best else 'unavailable','answer':best['answer'] if best else 'The connected AI provider did not return an answer. Please try again later.','results':results,'winner':best['provider'] if passing else None,'warning':'A reference phrase match is only a basic test, not proof of accuracy. Verify independently.'}

def source_category(url):
    """Informational source-type labels, not claims of truth or endorsements."""
    try:
        host=(urllib.parse.urlsplit(url).hostname or '').lower().rstrip('.')
    except ValueError:
        return 'unknown'
    if not host: return 'unknown'
    if host.endswith('.gov') or host.endswith('.gc.ca') or host.endswith('.gov.uk') or host.endswith('.gouv.qc.ca') or host in ('ontario.ca','www.ontario.ca','canada.ca','www.canada.ca','quebec.ca','www.quebec.ca'):
        return 'government'
    if host == 'reddit.com' or host.endswith('.reddit.com') or host in ('stackoverflow.com','www.stackoverflow.com') or host.endswith('.stackexchange.com'):
        return 'community discussion'
    if host in ('youtube.com','www.youtube.com','youtu.be'):
        return 'video'
    if host.endswith('.edu') or host.endswith('.ac.uk'):
        return 'academic'
    return 'other website'

def normalized_source_url(url):
    """Deduplicate only straightforward tracking variations of public search leads."""
    try:
        s=urllib.parse.urlsplit(url)
        if s.scheme not in ('http','https') or not s.hostname:return ''
        params=urllib.parse.parse_qsl(s.query,keep_blank_values=True)
        params=[(k,v) for k,v in params if not (k.lower().startswith('utm_') or k.lower() in ('fbclid','gclid','mc_cid','mc_eid'))]
        path=s.path.rstrip('/') or '/'
        return urllib.parse.urlunsplit((s.scheme.lower(),s.netloc.lower(),path,urllib.parse.urlencode(params),'')).strip()
    except (ValueError,TypeError):return ''

def substantial_repeat(new, prior):
    """Conservative guard for almost identical research summaries; cannot prove uniqueness."""
    def words(t):return set(re.findall(r'[a-z0-9]{4,}',t.lower()))
    a=words(new)
    if len(a)<12:return False
    return any(len(a & words(old))/max(1,len(a | words(old)))>=0.78 for old in prior if old)

def brave(query):
    key=os.getenv('BRAVE_API_KEY')
    if not key:return []
    url='https://api.search.brave.com/res/v1/web/search?'+urllib.parse.urlencode({'q':query[:350],'count':8,'search_lang':'en'})
    try:
        d=get_json(url,{'X-Subscription-Token':key,'Accept':'application/json'})
        return [{'title':x.get('title','')[:200],'url':normalized_source_url(x.get('url','')),'snippet':re.sub('<[^>]+>','',x.get('description',''))[:700]} for x in d.get('web',{}).get('results',[]) if normalized_source_url(x.get('url',''))]
    except Exception:return []

def plan_queries(question,round_no):
    templates=[['{q} detailed guide specifications manuals','{q} discussions forums solved','{q} official documentation'],['{q} reddit forum problem resolved','{q} alternative compatible equivalent sources','{q} user experience troubleshooting'],['{q} prices suppliers availability','{q} parts listings marketplace','{q} original equipment manufacturer support'],['{q} common failure false diagnosis','{q} service manual bulletin','{q} repair shop advice'],['{q} recent updates sources','{q} uncommon solutions case studies','{q} comparison independent reviews'],['{q} unresolved questions contradictions','{q} primary sources technical details','{q} how to verify answer']]
    return [t.format(q=question[:180]) for t in templates[(round_no-1)%len(templates)]]

def research_one(job_id):
    with DB_LOCK:
        with connect() as c:
            row=c.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not row or row['stopped'] or row['status']=='complete' or row['round']>=MAX_ROUNDS:return
            if not os.getenv('BRAVE_API_KEY'):
                c.execute('UPDATE jobs SET status=?,summary=?,updated_at=? WHERE id=?',('needs_setup','Web search is not connected. Research has not started.',now(),job_id))
                return
            n=row['round']+1
            c.execute('UPDATE jobs SET status=?,updated_at=?,next_run=? WHERE id=?',('researching',now(),time.time()+INTERVAL,job_id))
    with connect() as c:
        excluded=[r['step'] for r in c.execute('SELECT step FROM tried_steps WHERE job_id=? ORDER BY id DESC LIMIT 30',(job_id,))]
    queries=plan_queries(row['question']+' '+row['details'],n)
    # Rejected attempts inform the synthesis, not the public search query: keep queries concise.
    excluded_text='; '.join(excluded)[:1600]

    found=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for q,res in zip(queries,pool.map(brave,queries)):
            found.extend((q,x) for x in res)
    unique=0
    with DB_LOCK:
        with connect() as c:
            for q,x in found:
                cur=c.execute('INSERT OR IGNORE INTO findings(job_id,created_at,query,source_url,title,snippet) VALUES(?,?,?,?,?,?)',(job_id,now(),q,x['url'],x['title'],x['snippet']))
                unique+=cur.rowcount
            src=c.execute('SELECT title,source_url,snippet FROM findings WHERE job_id=? ORDER BY id DESC LIMIT 18',(job_id,)).fetchall()
            prior_notes=[r['notes'] for r in c.execute('SELECT notes FROM runs WHERE job_id=? ORDER BY id DESC LIMIT 6',(job_id,))]
    source_text='\n'.join(f"- {x['title']} | {x['source_url']} | {x['snippet']}" for x in src)
    if not os.getenv('BRAVE_API_KEY'):
        notes='Search is not connected. Add BRAVE_API_KEY to enable real searches. No research has been conducted yet.'
    elif not src:
        notes='No matching search results collected in this round. Do not claim to have found evidence.'
    else:
        prompt=(f"Research question: {row['question']}. Additional details: {row['details']}\nRound {n}. Already tried / ruled out: {excluded_text or 'none reported'}. Do not repeat rejected steps. "
                "Use only the following search result snippets as leads, NOT as verified full-page evidence. "
                "Write a short preliminary finding and note uncertainties. Name best 3 source links and what to verify next. "
                "Do not invent measurements, exact prices, claims, or source visits. Previous summaries to avoid repeating: " + " | ".join(prior_notes)[:1300] + "\n"+source_text)
        models=[nm for nm,(ke,*_) in MODELS.items() if os.getenv(ke)]
        result=ask_model(models[0],prompt) if models else None
        notes=result.get('answer','') if result and result.get('answer') else ('New source leads collected: '+str(unique)+'. Review these before treating their claims as verified.')
        if substantial_repeat(notes,prior_notes):
            notes=f'No materially new explanation in research round {n}. {unique} new source leads gathered; review the new links rather than repeating earlier suggestions.'
    with DB_LOCK:
        with connect() as c:
            current=c.execute('SELECT stopped FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not current or current['stopped']:return
            status='complete' if n>=MAX_ROUNDS else 'waiting'
            c.execute('INSERT INTO runs(job_id,round,created_at,notes,urls_checked) VALUES(?,?,?,?,?)',(job_id,n,now(),notes,unique))
            c.execute('UPDATE jobs SET round=?,status=?,summary=?,next_run=?,updated_at=? WHERE id=?',(n,status,notes,time.time()+INTERVAL,now(),job_id))

def worker():
    while True:
        try:
            with connect() as c: ids=[r['id'] for r in c.execute("SELECT id FROM jobs WHERE status IN ('queued','waiting') AND stopped=0 AND next_run<=? ORDER BY next_run LIMIT 3",(time.time(),)).fetchall()]
            for jid in ids:research_one(jid)
        except Exception as e:print('worker error',str(e),flush=True)
        time.sleep(20)

def get_job(jid):
    with connect() as c:
        row=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        if not row:return None
        result=dict(row)
        result['findings']=[{**dict(x),'source_type':source_category(x['source_url']),'evidence_status':'unverified search lead'} for x in c.execute('SELECT title,source_url,snippet,created_at FROM findings WHERE job_id=? ORDER BY id DESC LIMIT 35',(jid,))]
        result['evidence_notice']='Search listings are leads, not checked source documents. No independent verification has been performed.'
        result['source_types']={}
        for item in result['findings']:
            kind=item['source_type'];result['source_types'][kind]=result['source_types'].get(kind,0)+1
        result['runs']=[dict(x) for x in c.execute('SELECT round,created_at,notes,urls_checked FROM runs WHERE job_id=? ORDER BY id DESC',(jid,))]
        result['tried_steps']=[dict(x) for x in c.execute('SELECT created_at,step FROM tried_steps WHERE job_id=? ORDER BY id DESC LIMIT 30',(jid,))]
        return result

class Handler(BaseHTTPRequestHandler):
    def response(self,status,data):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def read_body(self):
        # Reject missing, negative, or malformed lengths before reading the socket.
        # A negative length could otherwise make read() wait for the connection to close.
        raw_size=self.headers.get('Content-Length')
        if raw_size is None or not raw_size.isdecimal():
            raise ValueError('Valid Content-Length required')
        size=int(raw_size)
        if size>30000:raise ValueError('Request is too large')
        if not self.headers.get('Content-Type','').lower().startswith('application/json'):
            raise ValueError('Content-Type must be application/json')
        payload=json.loads(self.rfile.read(size) or b'{}')
        if not isinstance(payload,dict):raise ValueError('JSON object required')
        return payload
    def read_job_token(self):
        return self.headers.get('X-Job-Token','').strip()
    def do_GET(self):
        p=urllib.parse.urlparse(self.path).path
        if p in ('/','/index.html'):
            body=(ROOT/'index.html').read_bytes();self.send_response(200);self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','no-referrer');self.send_header('Cache-Control','no-store');self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        if p=='/api/health':return self.response(200,{'ok':True,'ai_providers':[n for n,v in MODELS.items() if os.getenv(v[0])],'search_connected':bool(os.getenv('BRAVE_API_KEY')),'research_rounds':MAX_ROUNDS,'interval_seconds':INTERVAL})
        if p=='/api/identify':
            args=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            try:
                with connect() as c:
                    setup_identifiers(c)
                    return self.response(200,lookup_identifier(c,args.get('number',[''])[0],args.get('maker',[''])[0],args.get('category',[''])[0]))
            except ValueError as e:return self.response(400,{'error':str(e)})
        if p=='/api/parts':
            args=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            try:
                with connect() as c:
                    setup_parts(c)
                    return self.response(200,lookup_parts(c,*(args.get(k,[''])[0] for k in ('maker','model','component','serial'))))
            except ValueError as e:return self.response(400,{'error':str(e)})
        if p.startswith('/api/jobs/'):
            jid=p.split('/')[-1]
            if not check_token(jid,self.read_job_token()):return self.response(404,{'error':'Job not found or access denied'})
            result=get_job(jid);return self.response(200,result) if result else self.response(404,{'error':'Not found'})
        self.response(404,{'error':'Not found'})
    def do_POST(self):
        try:
            p=urllib.parse.urlparse(self.path).path;d=self.read_body()
            if p in LIMITS and not permit_request(p,self.client_address[0]):
                return self.response(429,{'error':'Too many requests. Please try again later.'})
            if p in ('/api/ask','/api/benchmark'):
                q=str(d.get('question','')).strip()[:2000]
                if not q:return self.response(400,{'error':'Enter a question'})
                expected=str(d.get('expected','')).strip()[:160] if p.endswith('benchmark') else ''
                result=model_batch(q,compare=p.endswith('benchmark'),expected=expected);return self.response(200,result)
            if p=='/api/jobs':
                q=str(d.get('question','')).strip()[:1200];details=str(d.get('details','')).strip()[:2500]
                if not q:return self.response(400,{'error':'Enter a question'})
                jid=uuid.uuid4().hex[:20];token=secrets.token_urlsafe(32)
                with connect() as c:
                    c.execute('INSERT INTO jobs(id,question,details,status,created_at,updated_at,next_run) VALUES(?,?,?,?,?,?,?)',(jid,q,details,'queued',now(),now(),time.time()))
                    c.execute('INSERT INTO job_tokens(job_id,token_hash) VALUES(?,?)',(jid,token_hash(token)))
                return self.response(201,{'id':jid,'token':token,'status':'queued','note':'Research continues only while this server and background worker remain running. A hosted server is required for overnight work.'})
            if p.endswith('/feedback') and p.startswith('/api/jobs/'):
                jid=p.split('/')[-2]
                if not check_token(jid,self.read_job_token()):return self.response(404,{'error':'Job not found or access denied'})
                step=str(d.get('tried','')).strip()[:600]
                if len(step)<3:return self.response(400,{'error':'Describe what you already tried'})
                with DB_LOCK:
                    with connect() as c:
                        c.execute('INSERT OR IGNORE INTO tried_steps(job_id,created_at,step) VALUES(?,?,?)',(jid,now(),step))
                        c.execute('UPDATE jobs SET updated_at=? WHERE id=?',(now(),jid))
                return self.response(200,{'saved':True,'note':'This attempt will be considered in future research rounds.'})
            if p.endswith('/resume') and p.startswith('/api/jobs/'):
                jid=p.split('/')[-2]
                if not check_token(jid,self.read_job_token()):return self.response(404,{'error':'Job not found or access denied'})
                if not os.getenv('BRAVE_API_KEY'):return self.response(409,{'error':'Search service is not configured; cannot resume.'})
                with DB_LOCK:
                    with connect() as c:
                        c.execute("UPDATE jobs SET status='queued',stopped=0,next_run=?,updated_at=? WHERE id=? AND round<?",(time.time(),now(),jid,MAX_ROUNDS))
                return self.response(200,{'status':'queued','note':'Eligible research job queued again.'})
            if p.endswith('/stop') and p.startswith('/api/jobs/'):
                jid=p.split('/')[-2]
                if not check_token(jid,self.read_job_token()):return self.response(404,{'error':'Job not found or access denied'})
                with connect() as c:c.execute('UPDATE jobs SET stopped=1,status=? WHERE id=?',('stopped',jid))
                return self.response(200,{'status':'stopped'})
            return self.response(404,{'error':'Not found'})
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
            return self.response(400,{'error':'Invalid JSON request or request parameters.'})
        except Exception:
            # Do not expose database paths, credentials, or upstream details to clients.
            return self.response(500,{'error':'Server error. Please try again later.'})
    def log_message(self,*args):pass

if __name__=='__main__':
    check_public_launch()
    setup();threading.Thread(target=worker,daemon=True).start()
    print(f'RightPlace AI server: http://{HOST}:{PORT} | AI keys {sum(bool(os.getenv(v[0])) for v in MODELS.values())}/3 | Search {bool(os.getenv("BRAVE_API_KEY"))}',flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
