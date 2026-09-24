from __future__ import annotations
import hashlib, json, mimetypes, os, secrets, sqlite3, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import PurePosixPath
from urllib.parse import unquote
from access_auth import AccessAuthError, AccessJWTValidator

MAX_BYTES = 10_000_000
MAGIC = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
DEFAULT_CORS_ORIGIN = "https://danbeem.xyz"

class Store:
    def __init__(self, db_path, artifact_root, clock=None, max_bytes=MAX_BYTES, access_validator=None):
        self.db_path, self.root, self.clock, self.max_bytes, self.access_validator = db_path, os.path.abspath(artifact_root), clock or time.time, max_bytes, access_validator
        os.makedirs(self.root, exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS results(result_id TEXT PRIMARY KEY, owner TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, sha256 TEXT NOT NULL, storage_path TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL, revoked_at REAL);
        CREATE TABLE IF NOT EXISTS invitations(token_hash TEXT PRIMARY KEY, result_id TEXT NOT NULL, principal TEXT NOT NULL, expires_at REAL, redeemed_at REAL);
        CREATE TABLE IF NOT EXISTS access(result_id TEXT NOT NULL, principal TEXT NOT NULL, PRIMARY KEY(result_id,principal));
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, result_id TEXT, principal TEXT, detail TEXT, created_at REAL NOT NULL);
        '''); self.db.commit()
    def audit(self,event,rid,principal,detail=""):
        self.db.execute("INSERT INTO audit(event,result_id,principal,detail,created_at) VALUES(?,?,?,?,?)",(event,rid,principal,detail,self.clock())); self.db.commit()
    def auth(self,h):
        token = h.get('CF-Access-JWT-Assertion')
        if not self.access_validator or not token: return None
        try: return self.access_validator.principal(token)
        except AccessAuthError: return None
    def row(self,rid): return self.db.execute('SELECT * FROM results WHERE result_id=?',(rid,)).fetchone()
    def status(self,row,p):
        if not p: return 401
        if not row: return 404
        if row['revoked_at'] is not None or (row['expires_at'] is not None and self.clock() >= row['expires_at']): return 410
        if p == row['owner'] or self.db.execute('SELECT 1 FROM access WHERE result_id=? AND principal=?',(row['result_id'],p)).fetchone(): return 200
        return 403
    def valid_id(self,rid): return bool(rid and PurePosixPath(unquote(rid)).name == unquote(rid) and '/' not in unquote(rid) and '\\' not in unquote(rid) and '..' not in PurePosixPath(unquote(rid)).parts)
    def publish(self,rid,p,data,mime,expires):
        if not p: return 401,None
        if not self.valid_id(rid): return 400,None
        digest=hashlib.sha256(data).hexdigest(); old=self.row(rid)
        if old:
            if old['owner']==p and old['sha256']==digest: return 200,old
            return 409,None
        if len(data)>self.max_bytes: return 413,None
        if mime not in MAGIC or not data.startswith(MAGIC[mime]): return 415,None
        path=os.path.abspath(os.path.join(self.root,p.replace(':','_'),rid+'.bin'))
        if os.path.commonpath([self.root,path]) != self.root: return 400,None
        os.makedirs(os.path.dirname(path),exist_ok=True)
        with open(path,'xb') as f: f.write(data)
        self.db.execute('INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?)',(rid,p,mime,len(data),digest,path,self.clock(),expires,None)); self.db.commit(); self.audit('publish',rid,p,digest)
        return 201,self.row(rid)
    def invite(self,rid,p,invitee,expires):
        row=self.row(rid); code=self.status(row,p)
        if code != 200: return code,None
        if p != row['owner']: return 403,None
        if not isinstance(invitee,str) or not invitee.strip(): return 400,None
        token=secrets.token_urlsafe(24); self.db.execute('INSERT INTO invitations VALUES(?,?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),rid,invitee.strip(),expires,None)); self.db.commit(); self.audit('invite',rid,p,invitee.strip()); return 201,token
    def redeem(self,token,p):
        if not p: return 401
        row=self.db.execute('SELECT * FROM invitations WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if not row or row['principal'] != p or row['redeemed_at'] is not None or (row['expires_at'] is not None and self.clock() >= row['expires_at']): return 410
        self.db.execute('UPDATE invitations SET redeemed_at=? WHERE token_hash=?',(self.clock(),row['token_hash'])); self.db.execute('INSERT OR IGNORE INTO access VALUES(?,?)',(row['result_id'],p)); self.db.commit(); self.audit('redeem',row['result_id'],p); return 200
    def revoke(self,rid,p):
        row=self.row(rid); code=self.status(row,p)
        if code != 200: return code
        if p != row['owner']: return 403
        self.db.execute('UPDATE results SET revoked_at=? WHERE result_id=?',(self.clock(),rid)); self.db.commit(); self.audit('revoke',rid,p); return 204
    def metadata(self,row): return {"schema_version":1,"result_id":row['result_id'],"owner":row['owner'],"mime":row['mime'],"size":row['size'],"sha256":row['sha256'],"storage_path":os.path.relpath(row['storage_path'],self.root).replace(os.sep,'/'),"expires_at":row['expires_at'],"revoked_at":row['revoked_at']}

class Handler(BaseHTTPRequestHandler):
    server_version='DanBotStudioLocal/1.0'
    def hdr(self,status,extra=None):
        self.send_response(status); self.send_header('Cache-Control','private, no-store'); self.send_header('Pragma','no-cache'); self.send_header('X-Robots-Tag','noindex, nofollow, noarchive')
        if self._cors_get():
            self.send_header('Vary', 'Origin')
            if self.headers.get('Origin') == self.server.cors_origin:
                self.send_header('Access-Control-Allow-Origin', self.server.cors_origin)
                self.send_header('Access-Control-Allow-Credentials', 'true')
        for k,v in (extra or {}).items(): self.send_header(k,str(v))
    def _cors_get(self):
        return self.command == 'GET' and self.route()[:1] == ['v1']
    def _reject_origin(self):
        return self._cors_get() and self.headers.get('Origin') not in (None, self.server.cors_origin)
    def json(self,status,obj):
        b=json.dumps(obj,sort_keys=True).encode(); self.hdr(status,{'Content-Type':'application/json','Content-Length':len(b)}); self.end_headers(); self.wfile.write(b)
    def body(self):
        n=int(self.headers.get('Content-Length','0')); return self.rfile.read(min(n,self.server.store.max_bytes+1000))
    def route(self): return [x for x in self.path.split('?')[0].split('/') if x]
    def do_POST(self):
        s=self.server.store; p=s.auth(self.headers); q=self.route()
        try: payload=json.loads(self.body() or b'{}')
        except Exception: return self.json(400,{'error':'invalid_json'})
        if len(q)==3 and q[:2]==['v1','results']:
            try: data=bytes.fromhex(payload['data_hex']); mime=payload['mime']; exp=payload.get('expires_at')
            except (KeyError,TypeError,ValueError): return self.json(400,{'error':'invalid_payload'})
            code,row=s.publish(q[2],p,data,mime,exp); return self.json(code,s.metadata(row) if row else {'error':'rejected'})
        if len(q)==4 and q[:2]==['v1','results'] and q[3]=='invite':
            code,t=s.invite(q[2],p,payload.get('principal'),payload.get('expires_at')); return self.json(code,{'token':t} if t else {'error':'forbidden'})
        if len(q)==4 and q[:2]==['v1','results'] and q[3]=='revoke':
            code=s.revoke(q[2],p); self.hdr(code,{'Content-Length':0}); self.end_headers(); return
        if q==['v1','invitations','redeem']:
            code=s.redeem(payload.get('token',''),p); return self.json(code,{'redeemed':code==200} if code==200 else {'error':'unavailable'})
        return self.json(404,{'error':'not_found'})
    def do_GET(self):
        if self._reject_origin(): return self.json(403, {'error':'origin_not_allowed'})
        s=self.server.store; p=s.auth(self.headers); q=self.route()
        if len(q)==4 and q[:2]==['v1','results'] and q[3] in ('metadata','media','download'):
            row=s.row(q[2]); code=s.status(row,p)
            if code != 200: return self.json(code,{'error':'unavailable'})
            if q[3]=='metadata': return self.json(200,s.metadata(row))
            if not os.path.isfile(row['storage_path']): return self.json(410,{'error':'integrity_failure'})
            try:
                with open(row['storage_path'],'rb') as f: data=f.read()
            except (OSError,): return self.json(410,{'error':'unavailable'})
            if len(data)!=row['size'] or hashlib.sha256(data).hexdigest()!=row['sha256']: return self.json(410,{'error':'integrity_failure'})
            extra={'Content-Type':row['mime'],'Content-Length':len(data)}
            if q[3]=='download': extra['Content-Disposition']='attachment; filename="'+row['result_id']+'.bin"'
            self.hdr(200,extra); self.end_headers(); self.wfile.write(data); return
        return self.json(404,{'error':'not_found'})
    def log_message(self,*args): pass

def serve(db_path='danbot_studio.sqlite3',artifact_root='artifacts',port=8765,access_validator=None,cors_origin=None):
    if port != 0 and port < 1024: raise ValueError('use an unprivileged local port')
    origin = cors_origin or os.environ.get('DANBOT_CORS_ORIGIN', DEFAULT_CORS_ORIGIN)
    if origin != DEFAULT_CORS_ORIGIN: raise ValueError('cors_origin must be https://danbeem.xyz')
    httpd=ThreadingHTTPServer(('127.0.0.1',port),Handler); httpd.store=Store(db_path,artifact_root,access_validator=access_validator); httpd.cors_origin=origin; return httpd
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser(); a.add_argument('--port',type=int,default=8765); a.add_argument('--db',default='danbot_studio.sqlite3'); a.add_argument('--artifacts',default='artifacts'); x=a.parse_args(); validator=AccessJWTValidator.from_env(); h=serve(x.db,x.artifacts,x.port,access_validator=validator); print(f'STAGING ONLY: http://127.0.0.1:{x.port}',flush=True); h.serve_forever()
