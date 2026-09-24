import hashlib, hmac, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dispatcher import Dispatcher, InboundRequest, LINK_BASE, PNG, DispatchError

class FakeComfy:
    provider = "comfyui"
    def __init__(self, data=PNG+b"fixture"): self.data, self.prompts = data, []
    def generate(self, prompt): self.prompts.append(prompt); return self.data

class Publisher:
    def __init__(self): self.calls = []
    def publish_private(self, result_id, owner, data, mime):
        self.calls.append((result_id, owner, data, mime))
        return LINK_BASE + result_id

class BadProvider(FakeComfy): provider = "invokeai"

def request(d, sid="SM1", **kw):
    r = InboundRequest("+15551234567", "image a blue bee", sid, "", **kw)
    return InboundRequest(r.from_phone, r.body, r.message_sid, d.sign(r), r.raw_url,
                          r.keyword_state, r.consent, r.a2p_approved)

class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.comfy, self.pub = FakeComfy(), Publisher()
        self.d = Dispatcher(owner_phone="+15551234567", signing_secret=b"secret", adapter=self.comfy, publisher=self.pub)
    def test_success_publishes_png_and_truthful_link(self):
        out = self.d.handle(request(self.d))
        self.assertEqual(out.status, "success"); self.assertEqual(out.link, LINK_BASE + "sms-" + hashlib.sha256(b"SM1").hexdigest()[:20])
        self.assertEqual(self.pub.calls[0][3], "image/png")
    def test_signed_owner_consent_stop_and_a2p_gates(self):
        for sid, kw in [("s1", {"signature":"bad"}), ("s2", {"from_phone":"+1999"}), ("s3", {"keyword_state":"stop"}), ("s4", {"consent":False}), ("s5", {"a2p_approved":False})]:
            r = InboundRequest(kw.pop("from_phone", "+15551234567"), "image x", sid, kw.pop("signature", ""), keyword_state=kw.pop("keyword_state", "normal"), consent=kw.pop("consent", True), a2p_approved=kw.pop("a2p_approved", True))
            if sid != "s1": r = InboundRequest(r.from_phone,r.body,r.message_sid,self.d.sign(r),r.raw_url,r.keyword_state,r.consent,r.a2p_approved)
            self.assertEqual(self.d.handle(r).status, "blocked")
    def test_duplicate_sid_rejected_and_no_second_call(self):
        self.assertEqual(self.d.handle(request(self.d)).status, "success")
        second = self.d.handle(request(self.d))
        self.assertEqual(second.detail, "duplicate_message_sid"); self.assertEqual(len(self.pub.calls), 1)
    def test_rejects_arbitrary_recipient_and_non_image(self):
        r = request(self.d, "nonimage")
        r = InboundRequest(r.from_phone, "image", r.message_sid, self.d.sign(InboundRequest(r.from_phone, "image", r.message_sid, "", r.raw_url, r.keyword_state, r.consent, r.a2p_approved)), r.raw_url, r.keyword_state, r.consent, r.a2p_approved)
        self.assertEqual(self.d.handle(r).detail, "image_intent_required")
        r = request(self.d, "recipient")
        r = InboundRequest(r.from_phone, "image send to +1999", r.message_sid, self.d.sign(InboundRequest(r.from_phone, "image send to +1999", r.message_sid, "", r.raw_url, r.keyword_state, r.consent, r.a2p_approved)), r.raw_url, r.keyword_state, r.consent, r.a2p_approved)
        self.assertEqual(self.d.handle(r).detail, "image_intent_required")
    def test_rejects_invokeai_and_bad_png(self):
        with self.assertRaises(DispatchError): Dispatcher(owner_phone="x", signing_secret=b"x", adapter=BadProvider(), publisher=self.pub)
        bad = Dispatcher(owner_phone="+15551234567", signing_secret=b"x", adapter=FakeComfy(b"not png"), publisher=self.pub)
        self.assertEqual(bad.handle(request(bad, "badpng")).detail, "dispatch_failed")

if __name__ == "__main__": unittest.main(verbosity=2)
