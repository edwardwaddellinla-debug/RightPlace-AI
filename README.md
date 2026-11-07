# RightPlace AI — Deep Solve and Multi-AI prototype

## What actually works

- Mobile-friendly, concise quick-answer interface with optional speech input on compatible HTTPS browsers.
- OpenAI, Anthropic Claude, and Google Gemini API adapters. API keys are **only read server-side**.
- Side-by-side response speed comparison, plus an optional literal *known-answer reference phrase* check. This is **not an independent correctness detector**; a model could mention a correct term but be wrong overall.
- Private-token access for newly created Deep Solve research jobs. Tokens stay in that browser's local storage; cleared browser data will lose access. There is no user account system yet.
- A SQLite research queue with multiple search angles, duplicate URL elimination, sources and round history, when the server is running **and a Brave Search API key is present**.
- If search is not configured, a job says `needs_setup`; it does **not** pretend to research or consume its research rounds.

## Start on a computer

Requires Python 3.10 or later; no third-party Python packages.

1. Copy `.env.example` values into the **server environment** (the example file is not automatically loaded). Set at least one AI key for answers and `BRAVE_API_KEY` for actual web searches.
2. Run `python server.py` in this folder.
3. Visit http://127.0.0.1:8000 from the same computer. To use a phone, deploy to a proper HTTPS host.
4. Run `python -m unittest -v test_server.py` for basic checks.

API subscriptions/credits are separate from ordinary ChatGPT/Claude/Gemini memberships. Search and model calls can incur charges.

## Deployment

The included Dockerfile runs the **application and hourly background worker** in one persistent process. It needs a hosting platform that runs continuously, HTTPS at the proxy, and persistent storage mounted at `/data`. Start with a private deployment, not an open public service. `PORT` and `HOST` are configurable.

**Not public-production ready:** The new job access tokens protect individual records but don't substitute for user accounts, abuse protections, consent and retention policies, API rate limits, spend caps, backups, secure private access, privacy audits, log scrubbing, content moderation, or source verification. Unauthenticated requests to `/api/ask` and `/api/jobs` could use paid API credits if made public. Please do not deploy openly with paid keys until these protections are added.

The research worker currently collects search **result snippets and links** as leads, and may synthesize preliminary summaries. It does not read/verify entire original pages, access private load boards, or certify an answer. Do not treat preliminary summaries as fully sourced proof. It searches over up to six rounds, at the configured interval, **only while the server is actually running**. There are no email/push notifications yet.

## Next engineering milestones

1. Secure hosting, user sign-in, per-user job ownership and spending limits.
2. Fetch approved primary sources with safe URL allowlists, robust source citations, checks for evidence quality and contradiction.
3. Add search/provider failover, source-grounded answer ranking and a realistic benchmark with graded cases.
4. Add licensed/embedded timestamped videos and opt-in progress memory.
5. Add notifications, feedback-driven ranking and the creator-request board with consent/privacy safeguards.

## Version 6 additions

- **Remember attempts:** Each research job has an "Already tried" entry. Saved attempts are included in later AI research summaries so the service can avoid recommending the same failed step. (This does not guarantee a model never repeats itself.)
- **Resume:** A job in `needs_setup` can be resumed after a web-search key is configured. In-progress research still requires an always-running process and writable persistent database.
- **Basic spend protection:** Server-side daily AI-call budget, default 100 provider calls per UTC day, configurable with `MAX_DAILY_AI_CALLS`. The limit includes each model call in a comparison. Basic per-IP hourly rate limits: 12 quick answers, 4 model comparisons, 5 new research jobs. This is not secure user authentication or a production-grade distributed rate limiter; use a gateway and stricter limits before public launch.
- **Database persistence:** SQLite stores jobs, feedback, run history, and budget counts when deployed on persistent storage; it will be lost if stored on an ephemeral host filesystem.
- **Tests:** `python -m unittest -v test_server.py` checks key safeguards. No live paid-model or web searches were executed in these tests.

For safety, do not publish this prototype publicly with billable API keys until user authentication, stronger distributed throttling, budget alerts, secret management, backups, user deletion, and a full privacy/security review are in place. Research snippets are still *unverified leads*, not confirmed factual citations.

## Version 7 — evidence honesty and non-repetition checks

- Each collected result is explicitly **unverified search lead**. Results label broad source type (government, academic, community discussion, video, other website) for navigation, **not** quality certification. Source type and number of links do not prove correctness.
- Tracking-parameter URL normalization reduces repeat links across research rounds without erasing legitimate product/query parameters.
- Research summarization now receives the previous round's summaries, and a conservative text-overlap detector flags near-identical restatements instead of presenting them as a new answer. It does not guarantee semantic novelty.
- Research job JSON includes `evidence_notice`, `source_types`, and `findings[].evidence_status`.
- Ten local automated tests pass, including new evidence and repetition tests; **live provider calls were not performed**.

**Still required before trusting final answers:** securely fetch primary source pages, verify specific claims against them, check conflicting evidence, human review of high-risk claims, and a proper evaluation suite.

## Version 8 — Unified mobile experience (November 2026)

New single mobile interface with six sections: Quick Answer, Deep Solve, Form Helper, Ideas, Quick Record, and AI Test. The original backend remains; research only runs with a configured web-search key and a continuously running host. Existing Deep Solve private-token job links are reused from Version 7 if used in the same browser/origin.

**Working locally:** Save and export ideas and incident text notes in the browser; optional browser voice dictation; audio recording that downloads a WebM file when stopped; basic form-field explanation via AI server; Deep Solve job queue and tried-step records (when backend running); optional OpenAI/Claude/Gemini speed comparison; link to search YouTube for a topic. Form Assistant does not yet parse or fill PDFs, submit documents, or check official fields automatically. Video finder currently opens YouTube search, not ranked or verified time-stamped clips. Voice commands require browser support and a secure origin.

**Important privacy limitations:** localStorage is not encrypted and browser clearing can delete all saved notes. Avoid putting sensitive personal details in this prototype. Recordings are downloaded, not kept in the app's note database. Never rely on this as an emergency, evidentiary, or secure medical/legal record. Private user accounts, consent flows, encryption at rest, and durable backup are future work.

**To test:** From this directory, run `python -m unittest -v test_server.py`, then `python server.py`, visit http://127.0.0.1:8000 on the host computer. Configure server-side environment variables for live AI and search. Do not publish the public endpoints with billable keys until stronger access control and abuse protection exist. Publishing this package requires a user-controlled hosting account. No website was automatically deployed.

**Research scheduling:** The ChatGPT hourly RightPlace AI research automation is separate from Deep Solve's own hourly worker. It does not update this software automatically.

## Version 8.1 — reproducible local test repair (November 6, 2026)

- Fixed a **test harness lifecycle defect**: unittest sorts test classes alphabetically, so an earlier test class could attempt to use the SQLite database before the class that initialized it. Initialization now occurs in `setUpModule`, with one temporary database shared for the entire suite and cleaned up afterward.
- Added a database-schema regression check. All **11 local unit tests passed** on November 6, 2026.
- Local HTTP smoke test confirmed `/` and `/api/health` returned HTTP 200 with no API keys. `/api/health` accurately reported no connected AI or search providers.
- **No changes to the live AI integration, source verification, or deployment.** This is a test reliability improvement, not evidence that the product is ready for public users.
- This zip is a newly repackaged derivative of the saved Version 8 project, not a recovered original Version 8 download link.

### Version 8.3 voice-interface changes (November 6, 2026)
- The Ask screen features a larger purple microphone. Voice recognition automatically submits a successfully transcribed question.
- Visible listening, failure, and stopped states prevent the microphone from appearing stuck; tapping again stops recognition.
- Speech recognition depends on browser support, microphone permissions, HTTPS, and sometimes browser vendor services. A real Android device has not yet been tested.
- Run `python -m unittest discover -v` for the server and static voice UI checks. These tests do not simulate real speech recognition or prove that a live AI provider is configured.

## Version 8.4 — Evidence-first parts registry and universal how-to guidance

- Added `parts_registry.py` with SQLite schema for sourced OEM/aftermarket candidate numbers, maker/model/component, serial applicability, evidence status, and source URLs.
- Added `GET /api/parts?maker=...&model=...&component=...&serial=...`. It returns an honest empty result until licensed/authorized catalogs are imported. It never generates part numbers.
- A verified source is **not** the same as verified fitment. Serial-range rules require manufacturer-specific decoding; the API intentionally marks fitment as unverified.
- Updated assistant instructions for practical how-to requests, concise safety caveats, and factual discussion of restricted topics without directly enabling serious harm.
- Added five tests. Run `python -m unittest discover -q`.
- This is an engineering foundation only: no manufacturer catalog, VIN decoder, UI parts-search form, external AI account, or public website has been connected or deployed.

## v8.5 Universal Identifier Lookup (foundation)
`GET /api/identify?number=ABC-123&maker=Acme` returns evidence-backed exact identifier matches for any product category (serial/model/VIN/SKU/barcode/part/IMEI/other). Optional `maker` disambiguates reused identifiers. Unknown identifiers return no invented matches. Records are currently empty; this does not query live catalogs, decode VINs, scan images, or verify ownership. Avoid collecting sensitive identifiers without opt-in and access controls. The UI and catalog connectors are not implemented yet.

## Voice reliability update (v8.7)

The purple Ask microphone now has a 15-second recognition timeout, preserves actionable permission/network error messages, checks for HTTPS, and submits a captured question at most once. `node test_voice_runtime.cjs` exercises five mocked browser scenarios; these are **not** real microphone tests. SpeechRecognition support varies by browser and can depend on a remote recognition service. A real Android/Chrome HTTPS test remains required. This release does not add a public deployment or manufacturer-catalog integrations.

## Version 8.8 — speech result reconciliation

Browser speech recognizers can send revised results before the `end` event. Previously, each event was appended, causing repeated or contradictory words in a spoken question. The microphone now holds the most recent full transcript and appends it **once**, after successful completion. Results received after a timeout/error are ignored. Added tests for corrected interim-like result events and late callbacks. This is a simulated browser test, not a physical phone test. No hosting or AI provider integration was performed in this update.

### v8.9 — Answer-request timeout (2026-11-06)
The question API now aborts after 30 seconds and displays a clear retry message instead of leaving users indefinitely waiting on an unresponsive network/server. Automated test: `node test_api_timeout.cjs`. This is not proof of real phone/browser compatibility. Remaining: live HTTPS testing, provider key configuration, user-facing cancel action, and reliable hosting.

### v9.0 — honest readiness status
The header now distinguishes offline preview, a running server without an AI provider, and a configured provider (not verified live). Demo responses no longer appear as successful answers or unlock feedback. Run `node test_readiness.cjs`. No deployment or live AI request was performed.

### v9.1 — voice-first screen layout
The purple microphone is now the first control on the Ask screen, 116px wide, with an explicit instruction. Typing remains available immediately below it. One new layout regression test confirms the order. No live microphone or AI-provider test was performed; public hosting remains unconfigured.

### v9.5: Safe external research links
Research findings are unverified leads. The browser now refuses to make clickable links
for non-HTTP(S), malformed, or relative URLs, even if old database records contain them.
This is defense in depth alongside server-side URL normalization. The guard does **not**
validate the factual accuracy, trustworthiness, or safety of a normal HTTPS website.
Run `node test_safe_external_links.cjs` to check URL protocol handling.

Remaining release blockers: provider integration test with a real key, HTTPS hosting,
Pixel microphone end-to-end testing, explicit opt-in and retention controls for server
research-job history, and a video vetting process beyond a YouTube search link.

### Version 9.6: truthful provider-failure status (2026-11-07)
A configured API key is not proof that the provider is responding. If all configured providers fail, `/api/ask` now reports `mode: unavailable` instead of `mode: live`; the Ask UI shows the failure rather than treating it as a successful answer. This is a local simulated regression test, **not** a verified live API integration.

### Version 9.8: provider fallback (2026-11-07)
When multiple AI providers have API keys configured, a normal question tries the first provider and, only if that call fails or returns empty text, tries one backup provider. Each attempt has an 18-second network timeout, keeping the two-attempt path under the browser's 45-second deadline in ordinary conditions. The fallback can incur a second paid API request; the daily AI budget applies to both. The benchmark endpoint still compares configured providers independently. This is locally simulated/tested, not verified with live provider credentials or on a phone. Public hosting still requires authentication and privacy/security review.

### Version 9.9 — three-provider recovery (2026-11-07)
If three providers are configured, the normal answer route now attempts the third provider after the first two fail. Each attempt uses a 12-second network timeout to keep the maximum sequential network waiting time at approximately 36 seconds, below the browser's 45-second deadline (excluding local processing). Provider calls still count against the daily budget. The new three-provider test uses simulated responses, not real API credentials. Real mobile and hosted testing remain necessary.


## Version 10.0 — cancellable voice capture (November 7, 2026)
- Tapping the microphone a second time now aborts the current recognition session rather than waiting for an `onend` event. It clears the watchdog immediately, restores the purple idle state, and ignores late callbacks from the cancelled session. This prevents a cancelled question from being submitted accidentally.
- Displays `Starting microphone…` while waiting for browser permission or recognition start; prior behaviour could appear unresponsive before `onstart`.
- Added a simulated cancellation regression test. These are browser-event mocks, **not** a real Android/Pixel microphone test.
- Three design questions assessed: cancellation versus stop semantics; permission/start latency; callback races from cancelled recognition sessions. The app still requires HTTPS, compatible browser speech support, and a real configured AI provider.

### Version 10.1 — voice draft protection (2026-11-07)
When the question box already contains typed text, dictation appends its transcript but does **not** automatically submit the combined text. The user reviews and explicitly taps **Get the answer**. When the box is empty, successful dictation still submits automatically. This prevents unintended combined questions. Tested with an additional simulated speech scenario; physical Android microphone behavior is not yet verified.

Open questions: browser speech permission/recognition reliability on actual Android Chrome; whether optional tutorial video search can be replaced by verified, non-promotional recommendations; live AI provider and HTTPS deployment with appropriate server-side secrets and cost limits.

### Version 10.2: Prevent duplicate live answer requests
- The Ask button now uses an in-flight guard in addition to its disabled state, so repeated taps or programmatic clicks do not create overlapping billable requests.
- Starting another question microphone session while an answer is in progress displays a wait message rather than recording a new question.
- The guard is cleared in a `finally` block, including on errors.
- Added `test_duplicate_answer.cjs` to verify duplicate requests are suppressed and subsequent requests are allowed.
- Remaining: live provider and Android microphone testing, HTTPS deployment, vetted video retrieval, and consent-driven memory.

### Local HTTP smoke test (v10.3)

Run `python smoke_test.py` to start a temporary server on localhost with a disposable database and no API keys. It checks that the homepage and health endpoint load and that asking a question **without** an AI key returns `mode: demo` rather than a fabricated live answer. This is a real local HTTP integration test, **not** a test of phone microphone permissions, a real AI provider, or public HTTPS hosting.

## v10.5 — Free-hosting readiness audit (November 7, 2026)

Run `python deploy_check.py` before hosting. It reports whether a provider is configured, whether web search is configured, and whether storage is *declared* persistent, without exposing API keys. `RIGHTPLACE_PERSISTENT_DISK=yes` is an operator assertion, **not** an independent check of a mounted disk. The tool always marks public paid deployment unapproved because account access, durable abuse limits and spending controls are not implemented. Free services that sleep cannot guarantee an hourly research worker. The current application is suitable for local/private evaluation, not an unprotected public paid launch. No live service or provider was tested by this audit.

### v10.6 public-launch safety gate (2026-11-07)
The server now refuses to start on a public network interface with any configured billable AI provider unless `RIGHTPLACE_ALLOW_PUBLIC_PAID=yes` is explicitly set. **This override is not authentication or a spending cap**; do not set it until gateway authentication, abuse controls, and external billing limits are in place. Local loopback testing remains available with configured keys. Public preview without AI keys remains available. Run `python -m unittest discover -p 'test_*.py'` and `python deploy_check.py` before launch.


## Version 10.7 — Free Render preview packaging

The prior Dockerfile omitted three Python modules imported by `server.py`, causing a container startup failure. Dockerfile now includes `parts_registry.py`, `identifiers.py`, and `public_launch_guard.py`. Added `render.yaml` for a **free preview only**, without billable AI keys or unsafe override. SQLite is explicitly ephemeral, not a pretend persistent `/data` disk.

On Render choose **New → Blueprint**, connect a GitHub repository containing these files, and select the blueprint. This ZIP itself cannot be selected as a GitHub repository. The free preview will show the interface and health endpoint, **not live AI answers**. Never add paid API keys to this public preview without authentication and external spending controls. The blueprint has not been deployed or tested on Render.

Run `python -m unittest discover -p 'test_*.py'` to validate packaging declarations. This does not replace building and running a Docker image on a real host.
