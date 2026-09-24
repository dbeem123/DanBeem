import base64, json, os, tempfile, threading, time, unittest
from http.client import HTTPConnection
from backend import serve
from access_auth import AccessAuthError, AccessJWTValidator

PNG = b'\x89PNG\r\n\x1a\nsynthetic'

class FakeAccess:
    def principal(self, token):
        if token and token.startswith('access:'):
            return token.split(':', 1)[1]
        raise AccessAuthError('bad')

class API(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.h = serve(os.path.join(self.d.name, 'db.sqlite'), os.path.join(self.d.name, 'art'), 0, access_validator=FakeAccess())
        self.port = self.h.server_address[1]
        self.t = threading.Thread(target=self.h.serve_forever, daemon=True); self.t.start()
    def tearDown(self):
        self.h.shutdown(); self.h.server_close(); self.h.store.db.close(); self.d.cleanup()
    def req(self, method, path, obj=None, p='owner'):
        c = HTTPConnection('127.0.0.1', self.port); body = json.dumps(obj).encode() if obj is not None else None
        headers = {'CF-Access-JWT-Assertion': (p if p == 'invalid' or p.startswith('access:') else 'access:' + p)} if p else {}
        c.request(method, path, body, headers); r = c.getresponse(); return r.status, r.getheaders(), r.read()
    def publish(self, rid='r1', p='owner', data=PNG, **kw):
        return self.req('POST', '/v1/results/'+rid, {'data_hex': data.hex(), 'mime': 'image/png', **kw}, p)
    def test_auth_private_and_no_listing(self):
        self.assertEqual(self.publish()[0], 201); self.assertEqual(self.req('GET','/v1/results/r1/metadata',p=None)[0],401); self.assertEqual(self.req('GET','/v1/results/r1/metadata',p='other')[0],403); self.assertEqual(self.req('GET','/v1/results/r1/metadata')[0],200); self.assertEqual(self.req('GET','/v1/results')[0],404)
    def test_media_download_invite_revoke(self):
        self.publish(); code,_,body=self.req('POST','/v1/results/r1/invite',{'principal':'mobile'}); self.assertEqual(code,201); token=json.loads(body)['token']; self.assertEqual(self.req('GET','/v1/results/r1/media',p='mobile')[0],403); self.assertEqual(self.req('POST','/v1/invitations/redeem',{'token':token},'mobile')[0],200); self.assertEqual(self.req('POST','/v1/invitations/redeem',{'token':token},'mobile')[0],410); self.assertEqual(self.req('GET','/v1/results/r1/media',p='mobile')[0],200); self.assertEqual(self.req('GET','/v1/results/r1/download',p='mobile')[0],200); self.assertEqual(self.req('POST','/v1/results/r1/revoke',p='owner')[0],204); self.assertEqual(self.req('GET','/v1/results/r1/media',p='mobile')[0],410)
    def test_expiry_and_idempotency(self):
        self.publish(expires_at=time.time()-1); self.assertEqual(self.req('GET','/v1/results/r1/metadata')[0],410); self.assertEqual(self.publish()[0],200); self.assertEqual(self.publish(data=b'other')[0],409)
    def test_validation(self):
        self.assertEqual(self.publish('%2e%2e')[0],400); self.assertEqual(self.publish('bad',data=b'notpng')[0],415); self.h.store.max_bytes=1; self.assertEqual(self.publish('big',data=PNG+b'x'*100)[0],413)
    def test_missing_and_invalid_access_are_401(self):
        self.assertEqual(self.req('GET','/v1/results/nope/metadata',p=None)[0],401); self.assertEqual(self.req('GET','/v1/results/nope/metadata',p='invalid')[0],401)

    def test_private_headers_and_file_integrity(self):
        self.publish(); status,headers,_=self.req('GET','/v1/results/r1/media'); h=dict(headers); self.assertEqual(status,200); self.assertEqual(h['Cache-Control'],'private, no-store'); self.assertIn('noindex',h['X-Robots-Tag'])
        os.remove(os.path.join(self.d.name,'art','owner','r1.bin')); self.assertEqual(self.req('GET','/v1/results/r1/media')[0],410)

    def test_cors_allows_only_configured_credentialed_get_origin(self):
        self.publish()
        # HTTPConnection helper has no Origin parameter; exercise through a direct request.
        c = HTTPConnection('127.0.0.1', self.port)
        c.request('GET', '/v1/results/r1/media', headers={'Origin':'https://danbeem.xyz','CF-Access-JWT-Assertion':'access:owner'})
        r = c.getresponse(); allowed = dict(r.getheaders()); r.read()
        self.assertEqual(r.status, 200); self.assertEqual(allowed['Access-Control-Allow-Origin'], 'https://danbeem.xyz')
        self.assertEqual(allowed['Access-Control-Allow-Credentials'], 'true'); self.assertEqual(allowed['Vary'], 'Origin')
        c = HTTPConnection('127.0.0.1', self.port)
        c.request('GET', '/v1/results/r1/media', headers={'Origin':'https://evil.example','CF-Access-JWT-Assertion':'access:owner'})
        r = c.getresponse(); self.assertEqual(r.status, 403); r.read()

    def test_sqlite_restart_recovers_metadata_and_media(self):
        self.publish(); self.h.shutdown(); self.h.server_close(); self.h.store.db.close()
        self.h=serve(os.path.join(self.d.name,'db.sqlite'), os.path.join(self.d.name,'art'), 0, access_validator=FakeAccess()); self.port=self.h.server_address[1]
        self.t=threading.Thread(target=self.h.serve_forever,daemon=True); self.t.start(); self.assertEqual(self.req('GET','/v1/results/r1/metadata')[0],200); self.assertEqual(self.req('GET','/v1/results/r1/media')[0],200)

class AccessJWTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cryptography.hazmat.primitives.asymmetric import rsa
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub = cls.private.public_key().public_numbers()
        enc = lambda n: base64.urlsafe_b64encode(n.to_bytes((n.bit_length()+7)//8, 'big')).decode().rstrip('=')
        cls.jwk = {'kty':'RSA','kid':'test-key','alg':'RS256','use':'sig','n':enc(pub.n),'e':enc(pub.e)}
    def token(self, claims, header=None):
        import jwt
        return jwt.encode(claims, self.private, algorithm='RS256', headers=header or {'kid':'test-key'})
    def validator(self, now=100):
        return AccessJWTValidator('https://team.example.cloudflareaccess.com', 'app-aud', lambda kid: {'keys':[self.jwk]} if kid == 'test-key' else {'keys':[]}, clock=lambda: now)
    def test_claims_and_deterministic_fake_jwks_resolver(self):
        t=self.token({'iss':'https://team.example.cloudflareaccess.com/','aud':'app-aud','exp':200,'nbf':90,'email':'owner@example.com'}); self.assertEqual(self.validator().principal(t),'owner@example.com')
    def test_fail_closed_for_missing_expired_bad_signature_and_unknown_kid(self):
        v=self.validator()
        for t in (None, 'bad', self.token({'iss':v.issuer,'aud':v.audience,'exp':99,'sub':'x'})):
            with self.assertRaises(AccessAuthError): v.principal(t)
        with self.assertRaises(AccessAuthError): v.principal(self.token({'iss':v.issuer,'aud':v.audience,'exp':200,'sub':'x'}, {'kid':'unknown'}))
        with self.assertRaises(AccessAuthError): v.principal(self.token({'iss':v.issuer,'aud':v.audience,'exp':200,'sub':'x'})[:-1]+'x')
    def test_issuer_audience_nbf_and_algorithm_are_enforced(self):
        v=self.validator()
        for claims in ({'iss':'wrong','aud':v.audience,'exp':200,'sub':'x'}, {'iss':v.issuer,'aud':'wrong','exp':200,'sub':'x'}, {'iss':v.issuer,'aud':v.audience,'exp':200,'nbf':101,'sub':'x'}):
            with self.assertRaises(AccessAuthError): v.principal(self.token(claims))

    def test_valid_synthetic_token_is_accepted_by_http_handler(self):
        import tempfile
        from backend import serve
        with tempfile.TemporaryDirectory() as d:
            token = self.token({'iss': self.validator().issuer, 'aud': 'app-aud', 'exp': 200, 'sub': 'owner'})
            h = serve(os.path.join(d, 'db.sqlite'), os.path.join(d, 'art'), 0, access_validator=self.validator())
            thread = threading.Thread(target=h.serve_forever, daemon=True); thread.start()
            try:
                c = HTTPConnection('127.0.0.1', h.server_address[1])
                c.request('GET', '/v1/results/missing/metadata', headers={'CF-Access-JWT-Assertion': token})
                r = c.getresponse(); r.read()
                self.assertEqual(r.status, 404)
            finally:
                h.shutdown(); h.server_close(); h.store.db.close(); thread.join(timeout=2)


if __name__=='__main__': unittest.main()
