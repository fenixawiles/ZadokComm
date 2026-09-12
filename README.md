# ZadokComm — advisor draft-assist & triage shell

A working communication layer for a luxury jeweler (Rolex authorized dealer):
inbound client messages are triaged, enriched with tightly-bounded CRM
context, and — for routine inquiries — arrive with a protocol-compliant reply
already drafted in the assigned advisor's voice. The advisor reviews inside
the conversation thread and **a human approves every send**. The owner's own
framing drives the scope: *"anything that ensures the team follows up in a
timely manner … use AI to help us answer some of the basic questions such as
any update on my watch."*

This is the real system running end-to-end on synthetic data behind five
pluggable boundaries. Nothing in this phase contacts an external service:
the drafting engine is deterministic by default, the sender is a mock, and
live model calls / live sending sit behind fail-closed environment gates.
**The only thing missing is credentials.**

## The loop

```
                      ┌──────────────────────────────────────────────────────┐
 inbound email        │                    ZadokComm shell                   │
 (Salesforce / Woven  │                                                      │
  webhook — mocked)   │  validate ─ idempotency ─ resolve client             │
 ────────────────────▶│      │                        │                      │
                      │      ▼                        ▼                      │
                      │  triage (deterministic)   ClientContextPacket        │
                      │  routine │ personal       (allowlist; NO inventory)  │
                      │      │        │               │                      │
                      │      ▼        ▼               ▼                      │
                      │  auto-draft  "answer      DraftEngine                │
                      │  (or toggle:  personally"  mock │ OpenAI (gated)     │
                      │   all)        + Draft anyway    │                    │
                      │      └──────┬───────────────────┘                    │
                      │             ▼                                        │
                      │  deterministic guardrails ─▶ drafted│needs_attention │
                      │             ▼                                        │
                      │  advisor inbox: Send / Edit / Regenerate             │
                      │  (final text re-scanned; flags need acknowledgment)  │
                      │             ▼                                        │
 outbound via the ◀───│  OutboundSender (mock; real = the CRM's send API)    │
 CRM of record        │  + append-only audit log of every step               │
                      └──────────────────────────────────────────────────────┘
```

**Plug points** (each is one interface + one config value):
`connectors/` (CRM lookups), `drafting/` (engines), `protocols/` (the actual
Zadok scripts), `outbound/` (the send path), `inbound/` (the webhook source).

## Quickstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/flask init-db
.venv/bin/flask seed          # synthetic demo state through the real pipeline
.venv/bin/flask run           # http://127.0.0.1:5000
```

Sign in with any advisor and the dev passcode (`zadok-dev` unless you set
`DEV_PASSCODE`). Run the tests with `.venv/bin/python -m pytest -q` — the
whole suite passes with no network and no API key.

## Demo script (10 minutes)

1. **Elena's inbox — Mia Chen.** An appointment request arrived with a draft
   already waiting, her two real Saturday openings offered, and a card:
   *"Client asked to update: Phone number update."* Acknowledge it, edit a
   word, Send. Open **History**: every step is in the audit trail.
2. **Sarah's inbox — Alex Morgan.** The owner's canonical case ("any luck
   with the GMT?"), drafted in the approved register — and the thread shows
   a red **overdue** chip because it waited past the SLA.
3. **Michael's inbox — Daniel Ruiz.** A complaint. No draft: *"This looks
   like one to answer personally."* That's the triage doing its job. Click
   **Draft anyway** to see the complaint-protocol draft on demand.
4. **The toggle.** In the sidebar, expand assist scope to *all inquiries*,
   inject a new complaint from the Simulator, and it arrives drafted and
   badged *Complex — review carefully*. Range is a switch, not a rebuild.
5. **The safety net.** Inject *policy stress*: the draft claims stock, a
   delivery window, and a discount — the scan flags each phrase, and Send
   refuses until the advisor explicitly acknowledges (which is audited).
   Edit a good draft to say "it's in stock" and Send catches that too.
6. **`/healthz`** shows: mock engine, both live gates off, the protocol-pack
   hash, and the pinned model fingerprint.

## Safety model

- **Two fail-closed gates.** `ZADOK_ALLOW_LIVE_MODEL_CALLS=0` strips the
  OpenAI key at the config chokepoint (a stray key cannot spend);
  `ZADOK_ALLOW_LIVE_SEND=0` makes any non-mock sender refuse to boot.
- **Human approval on every send, in both assist modes.** Nothing sends
  itself; flagged text additionally requires an explicit, audited
  acknowledgment.
- **The context packet is the privacy boundary.** Drafting engines see ONLY
  an allowlisted `ClientContextPacket`; unknown fields raise, and inventory
  is structurally excluded — availability exists solely as a coarse policy
  state. The mock fixtures plant decoy stock blocks and the tests prove they
  can never traverse.
- **Untrusted-content boundary.** Client-written text is data, never
  instructions — it appears only inside delimited user-message sections,
  under an explicit boundary rule.
- **Everything is auditable.** Append-only log of who did what; every draft
  records the exact model id, registry fingerprint, prompt-part hashes,
  protocol-pack hash, and the exact packet the engine saw. The AI original
  is immutable; the advisor's edit and the sent bytes are stored separately.
- **Unknown APP_ENV fails safe to production**, and production refuses to
  boot while auth is the dev shell (real deployment needs SSO).

## Plugging in the real things

| Boundary | Today | Real implementation |
|---|---|---|
| Salesforce | `MockSalesforceConnector` (fixtures) | `simple-salesforce`: Connected App + OAuth, SOQL lookup by email; set `CRM_CONNECTORS=salesforce` |
| Woven | `MockWovenConnector` (fixtures) | Pending API discovery (see `docs/DISCOVERY.md`); fallback: export sync feeding the same interface |
| Drafting | `MockDraftEngine` | `DRAFT_ENGINE=openai` + `ZADOK_ALLOW_LIVE_MODEL_CALLS=1` + `OPENAI_API_KEY` — already implemented |
| Protocols | `protocols/examples/` | Drop the real Zadok scripts into gitignored `protocols/local/` — they override by filename and never enter git |
| Sending | `MockOutboundSender` | Implement `OutboundSender` against the CRM's send API (the CRM stays the record of communications) + `ZADOK_ALLOW_LIVE_SEND=1` |
| Inbound | `/dev/simulator`, `flask inject` | Point the CRM's outbound webhook / email intake at `POST /webhooks/inbound` with the shared secret |

## Honest scope

Draft-assist + triage only. No booking automation (slots are surfaced, not
booked). No CRM write-back yet — profile changes are advisor-visible cards
queued for a future `propose_profile_update` connector method. No inventory
features beyond the coarse policy enum, by design. Dev auth is not SSO.
Assist-scope changes affect new inbound only and are audited; gating the
toggle to a manager role arrives with real auth. SQLite is the dev database;
the SQL is kept Postgres-portable for a later migration.
