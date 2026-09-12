# Discovery questions for the Zadok meeting

The shell runs today on synthetic data. These are the questions whose answers
turn mocks into real connectors — ordered by how much each answer changes.

## 1. Where does email actually live? (the system-of-record question)
- When a client emails an advisor today, where does that message land first:
  Salesforce, Woven, or an advisor's own mailbox (Outlook/Gmail)?
- Which system is treated as the record of client communications — where
  does compliance expect to find every sent message?
- How do replies go out today: from inside a CRM, or from the advisor's
  mailbox? What from-address do clients see?
  (This decides what `OutboundSender` must call, and whether DKIM/SPF for a
  send-on-behalf setup matters.)

## 2. Salesforce specifics
- Which edition (Professional / Enterprise / Unlimited)? API access differs —
  Professional historically gates the REST API.
- Is there an existing integration user, Connected App, or middleware?
- Is a **sandbox org** available to build against before touching production?
- How does inbound email reach Salesforce today (Email-to-Case, Einstein
  Activity Capture, Outlook/Gmail integration, manual logging)?
- Can workflow rules / Flows fire an outbound webhook on new inbound
  messages, or would we poll?

## 3. Woven — the biggest unknown
- Does Woven expose an API at all? (Vendor contact? Docs? Webhooks?)
- If not: what export paths exist (CSV, scheduled reports, database access)?
  A periodic export sync can feed the same connector interface.
- What does Zadok keep in Woven vs Salesforce? Which one owns client
  profiles, purchase history, appointment books?
- Where do advisors apply a client's profile update today (new phone number,
  changed interest)? That's the target for the future write-back method.

## 4. Volume, staffing, and the owner's SLA
- Inbound client messages per day, roughly, and per advisor?
- What share are the "basic questions" (status check-ins, appointment
  requests, thank-yous) vs complex/high-touch messages? Which categories
  should be automated **first**?
- What does the owner consider "timely"? (That number becomes
  `RESPONSE_SLA_HOURS`.) What's the current typical response time?
- Who is on the new-client team today (the welcome-template role), and who
  should own that inbox in the tool?

## 5. Protocols and voice
- Can we get the actual Rolex AD communication guidance / approved language,
  and the current reply scripts? (They load from gitignored
  `protocols/local/` and never enter the repo.)
- Will advisors share a few sent emails each (with permission) to build real
  voice profiles?
- Who approves changes to scripts — the owner, a manager, Rolex?

## 6. Authorization and data governance
- Who signs off on granting a third party API access to client data? Is a
  written data-access agreement / NDA process in place? (Nothing touches
  real client data before that exists.)
- Any retention or privacy constraints on client purchase history?
  (High-value purchase data is theft-targeting sensitive; the shell's
  allowlisted-packet design exists for this.)
- For live drafting: is an OpenAI account with appropriate data-handling
  terms (no training on business data / zero-retention options) acceptable,
  and who owns the key and the bill? (At the volumes above, model spend is
  a few dollars a month — bring the estimate.)

## 7. Pilot shape
- Which advisors pilot first? (Suggest: one advisor + the new-client inbox.)
- Success metrics to agree on up front: time-to-first-response, share of
  routine messages handled from a draft, edit distance (how much advisors
  change drafts), adoption, and **zero protocol incidents**.
- What does Rolex need to see to bless it? (Proposed answer: the protocol is
  centrally encoded, a human approves every send, and the audit trail shows
  who approved what and exactly what the system was shown — a stronger
  compliance posture than freehand email.)
