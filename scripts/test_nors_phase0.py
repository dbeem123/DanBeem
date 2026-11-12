import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    ROOT / "tools/ombudsman-casework-tools.html",
    ROOT / "tools/nors-crosswalk.html",
    ROOT / "tools/drafting-assistant.html",
    ROOT / "tools/responsible-use.html",
]
REQUIRED_DEMO = "Demonstration only. Use the synthetic examples or invented facts. Do not enter information from a real case, even with names removed."
REQUIRED_AI = "This tool uses fixed rules and published sources. It does not use artificial intelligence or send your text anywhere."
REQUIRED_SCOPE = "Personal demonstration project. Not an official State of Connecticut or LTCOP tool, and not approved for real case information."
CSP = "default-src 'self'; connect-src 'self'; script-src 'self'"
BANNED_UI = ["violation", "violated", "noncompliant", "deficient practice", "substantiated", "recommend enforcement"]
PROTECTED_FIELDS = {"identity_permission", "authorization_note", "case_status", "resident_satisfaction", "status_or_outcome"}

class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.inline_scripts = 0; self.scripts = []
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs = dict(attrs)
            self.scripts.append(attrs.get("src"))
            if not attrs.get("src"): self.inline_scripts += 1

class Phase0Tests(unittest.TestCase):
    def test_required_copy_on_hub_tools_and_responsible_use(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                for required in (REQUIRED_DEMO, REQUIRED_AI, REQUIRED_SCOPE): self.assertIn(required, text)

    def test_strict_script_csp_and_no_inline_javascript(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertIn(CSP, text)
                parser=ScriptParser(); parser.feed(text)
                self.assertEqual(parser.inline_scripts, 0)
                self.assertFalse(any("://" in (src or "") for src in parser.scripts))
                self.assertNotRegex(text, r"\bon(?:click|input|change|submit)\s*=")

    def test_no_client_storage_or_cookie_api_in_page_code(self):
        files = [*PAGES, *(ROOT / "Assets" / name for name in ["nors-crosswalk-page.js", "drafting-assistant-page.js", "responsible-use-page.js", "nors-phase0-privacy.js"])]
        pattern = re.compile(r"localStorage|sessionStorage|indexedDB|document\.cookie", re.I)
        for path in files:
            with self.subTest(path=path.name): self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")))

    def test_synthetic_examples_are_labeled_and_protected_fields_absent(self):
        examples=json.loads((ROOT / "data/nors_synthetic_scenarios.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(examples),3); self.assertLessEqual(len(examples),5)
        self.assertEqual(len({e["id"] for e in examples}),len(examples))
        for example in examples:
            self.assertTrue(example["label"])
            self.assertTrue(example["notes"].startswith("Synthetic example:"))
            self.assertTrue(PROTECTED_FIELDS.isdisjoint(example["fields"]))
            self.assertNotRegex(example["notes"], r"\b(?:\d{1,2}[/-]){1,2}\d{2,4}\b|\b(?:room|rm\.?)\s*#?\s*\w+|\b\d{3}[ .-]\d{3}[ .-]\d{4}\b")
        loader=(ROOT / "Assets/drafting-assistant-page.js").read_text(encoding="utf-8")
        self.assertIn("(synthetic)",loader)

    def test_sensitive_fields_start_empty_and_extraction_never_populates_them(self):
        page=(ROOT / "tools/drafting-assistant.html").read_text(encoding="utf-8")
        for field_id in ["identity-permission","case-status","resident-satisfaction"]:
            self.assertRegex(page, rf'<select id="{field_id}">\s*<option value="">Select one</option>')
        for field_id in ["authorization-note","resident-perspective","resident-desired-outcome","status-or-outcome"]:
            match=re.search(rf'<textarea id="{field_id}"([^>]*)>(.*?)</textarea>',page,re.S)
            self.assertIsNotNone(match,field_id)
            self.assertNotRegex(match.group(1),r'\bvalue\s*=')
            self.assertEqual(match.group(2).strip(),"")
        script=(ROOT / "Assets/drafting-assistant-page.js").read_text(encoding="utf-8")
        extraction=script.split("function extractScenarioFields()",1)[1].split("function buildCrosswalkKeywordText",1)[0]
        for field in PROTECTED_FIELDS: self.assertNotIn(f"setFieldIfEmpty('{field}'",extraction)

    def test_draft_templates_only_emit_fully_populated_field_sentences(self):
        template=json.loads((ROOT / "data/case_note_templates.json").read_text(encoding="utf-8"))
        script=(ROOT / "Assets/drafting-assistant-page.js").read_text(encoding="utf-8")
        self.assertIn("values.every(value => String(value || '').trim())",script)
        self.assertIn("if (output.length > sectionStart) output.splice(sectionStart, 0, section.header)",script)
        for section in template["templates"].values():
            for sentence in section["sentences"]:
                fields=re.findall(r"\{([^}]+)\}",sentence["template"])
                self.assertTrue(fields, sentence)
                self.assertRegex(script, r"return String\(formData\[field\] \|\| ''\)\.trim\(\)")

    def test_banned_decision_phrases_absent_from_owned_ui_and_templates(self):
        files=[*PAGES, ROOT/"Assets/nors-crosswalk-page.js",ROOT/"Assets/drafting-assistant-page.js",ROOT/"Assets/responsible-use-page.js",ROOT/"data/case_note_templates.json"]
        for path in files:
            text=path.read_text(encoding="utf-8")
            for phrase in BANNED_UI:
                with self.subTest(path=path.name,phrase=phrase): self.assertNotIn(phrase,text.lower())
        self.assertNotRegex((ROOT/"tools/drafting-assistant.html").read_text(encoding="utf-8").lower(),r"final\s+nors\s+code")
        for path in files:
            self.assertNotRegex(path.read_text(encoding="utf-8"),r"(?i)\bverified\b.{0,45}\b(?:result|match|finding|case|conclusion)\b")

    def test_dark_theme_link_colors_are_aa_against_site_background(self):
        css=(ROOT/"Assets/nors-phase0.css").read_text(encoding="utf-8")
        self.assertIn("color:#91d8ff",css); self.assertIn("color:#d0b7ff",css); self.assertIn("color:#e6f0fb",css)
        def luminance(rgb):
            vals=[int(rgb[i:i+2],16)/255 for i in (1,3,5)]
            vals=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in vals]
            return sum(v*w for v,w in zip(vals,(0.2126,0.7152,0.0722)))
        bg=luminance("#07101a")
        for color in ("#91d8ff","#d0b7ff","#e6f0fb"):
            ratio=(luminance(color)+0.05)/(bg+0.05)
            self.assertGreaterEqual(ratio,4.5,(color,ratio))

if __name__ == "__main__": unittest.main(verbosity=2)
