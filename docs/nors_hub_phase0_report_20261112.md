# NORS Hub Phase 0 — Revision 3 report (2026-11-12)

## Outcome

Phase 0 was built on a local branch from the verified live `main` commit `fd9db9d40d1c9c9b9647afb3d89789d0c17f8c5c`:

- Branch: `codex/nors-phase0-20261112`
- Checkout: `C:\Users\Dan\Documents\Codex\nors-phase0-20261112-byte`
- Checkout line endings: `core.autocrlf=false` to preserve the source files and keep the data-size audit accurate.
- This report was prepared on the Phase 0 branch; publication is recorded separately in the handoff report.
- Phase 1 and its source-pack work were not started.

## Phase 0 changes

- Added `tools/ombudsman-casework-tools.html` as a small, non-official hub linking the Crosswalk, Drafting Assistant, and Responsible Use pages.
- Replaced case-note invitations with the required synthetic/invented-facts warning on the hub, both tools, and Responsible Use. The required fixed-rules/no-AI and personal-demonstration statements appear in all four places.
- Added three invented, clearly marked synthetic examples, loaded with one click from `data/nors_synthetic_scenarios.json`.
- Added a local, nonblocking input reminder for name-shaped text, dates, room numbers, phone numbers, and ID-like numbers. It does not send or log the input and states that it cannot catch everything.
- Added a self-only CSP to the hub and three NORS pages. Extracted the pages' inline scripts into local `Assets` files and removed inline event handlers. The policy keeps existing inline styles working while restricting script and connection sources to self.
- Kept permission, status, satisfaction, resident-preference and related decision fields blank at startup; extraction cannot fill permission, status, satisfaction, outcome or preference fields. The draft builder now omits any sentence whose source field is blank, instead of writing a missing-field placeholder. Every generated narrative sentence comes from a populated field template.
- Added high-contrast link and chip colors for the dark interface. The static contrast test confirms the configured colors exceed 4.5:1 against the page background.

## Checks

- Phase 0 offline suite: **8 passed**.
- Full Python suite (`unittest discover -s scripts -p 'test_*.py'`): **195 passed**. Temp files were redirected to a scratch directory inside this checkout; no packages were installed.
- Survey/enforcement release audit: **12/12 sections passed**.
- Data freshness: **17/17 sources current**.
- JavaScript syntax checks and `git diff --check`: **passed**.
- Local Edge presentation/privacy attempt: Edge exited before rendering with `0xC0000005` (3221225477); Playwright is not installed in this checkout, and no packages were installed.
- Accepted browser gate: Claude ran the full presentation suite and Phase 0 harness twice in Playwright Chromium, with all checks passing, no browser errors, and no external requests. Per the publish handoff, Chromium is accepted as the Edge gate stand-in for this release. The two existing root-path fallback 404s were harmless and pre-existing.

Browser gate: run by Claude in Playwright Chromium on 2026-11-12 (presentation suite all PASS; Phase 0 harness PASS x2; no external requests); Edge unavailable on this PC (0xC0000005).

The release gate is green using the accepted browser stand-in. Publication status is recorded in the separate handoff report.

## Backups

Exact-byte backups of the three pre-existing HTML pages are under:
`C:\Users\Dan\Documents\Codex\nors-phase0-20261112-backup\`

| File | SHA-256 |
| --- | --- |
| `tools/nors-crosswalk.html` | `59dd58acc8c3e0c826353d27500d9444c5d22f2283d0a05f6467e62b6225a929` |
| `tools/drafting-assistant.html` | `f34804a967d54a94468ddac57204e6818a440265023cfc7cef45893679d38a6c` |
| `tools/responsible-use.html` | `ecfb2fe72da3ab74b1a99c93ee8df05958375b53da68c9d88fe36642e1b706b7` |

## Phase 0 file hashes

| File | SHA-256 |
| --- | --- |
| `Assets/drafting-assistant-page.js` | `df03d02488c83d782d0dc6004067132d6e4d0de3cda7a86104e70b8a86ea12a6` |
| `Assets/nors-crosswalk-page.js` | `8c88833a7477264bce62bd3189460ba9c727bf5aff7f24ed32e5f85e6577dacb` |
| `Assets/nors-phase0-privacy.js` | `5635726c9345179de1cc7a1cbc2ecb1815951f9903f46c27dc06ae260b21d9f9` |
| `Assets/nors-phase0.css` | `d4a4cc19df35f61a74198b2e4233a8d9fb7bb561e51e582b0f11cfb04afd08c9` |
| `Assets/responsible-use-page.js` | `14722d8c4eb52983d3bae61120c795ddd83819a7202ed96443670d6a671a0352` |
| `data/nors_synthetic_scenarios.json` | `9ff7d5535555e13a5d0ffc40d8feebec7dc7e3df88fb8f5704ed237b76cfb813` |
| `scripts/test_nors_phase0.py` | `a76147e22663bef2e2fa0742129bcc90561742b41a427df9e1b56841886c54fd` |
| `scripts/test_nors_phase0_browser.js` | `fc76f98bef774e70365030196a55d1d37cf0af8b3d161ffde86b47b99f75fab7` |
| `scripts/test_nors_phase0_harness.html` | `5d9302db998bc6a01886486b3a6058483140185aaec779016809e84b37d41964` |
| `tools/ombudsman-casework-tools.html` | `ea7a28d1a717b5e9bb7acdc06eba68c4d01142370c3bbedb3442836dd165030a` |
| `tools/nors-crosswalk.html` | `f6eb9b0a3d365d0ccbfdc34c356efd83ea3fdb444abb18381ee35ca7a447c98b` |
| `tools/drafting-assistant.html` | `fd531b6d48b294277c16842392e9b5cf19c8b7ca0222f3f4e6514e4555ed1a5b` |
| `tools/responsible-use.html` | `e0126940a55cd8129980190c8c819ee9976ec3877bb6e9e27b743cf8fbbf80af` |


## Review status

Claude reviewed the exact Phase 0 files and completed the accepted Chromium browser gate. Phase 1 and its source-pack work were not started.
