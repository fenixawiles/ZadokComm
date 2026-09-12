-- ZadokComm schema. SQLite dialect kept Postgres-portable:
--   * timestamps are ISO-8601 UTC TEXT (compare lexicographically; TIMESTAMPTZ later)
--   * JSON is stored as TEXT (JSONB later)
--   * INTEGER PRIMARY KEY maps to BIGSERIAL later
-- Client master data (profiles, purchase history, availability) deliberately
-- lives BEHIND the CRM connectors, never in these tables.

CREATE TABLE IF NOT EXISTS advisors (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    sign_off_name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'advisor' CHECK (role IN ('advisor', 'new_client_team')),
    voice_key TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY,
    client_ref TEXT NOT NULL,              -- opaque connector handle: sf:C-1001 / woven:W-2002 / unknown:<email>
    client_display_name TEXT NOT NULL,     -- render cache only; the CRM stays the source of truth
    channel TEXT NOT NULL DEFAULT 'email',
    subject TEXT,
    crm_source TEXT NOT NULL,              -- salesforce | woven | unknown
    assigned_advisor_id INTEGER NOT NULL REFERENCES advisors(id),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    awaiting_reply_since TEXT,             -- last inbound with no later outbound; NULL when answered
    last_inbound_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (client_ref, channel)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    source TEXT NOT NULL,                  -- simulator | salesforce | woven | shell | seed
    external_message_id TEXT NOT NULL,
    sender_display TEXT NOT NULL,
    body TEXT NOT NULL,
    triage TEXT CHECK (triage IN ('routine', 'personal')),   -- inbound only
    triage_reason TEXT,
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (source, external_message_id)   -- webhook idempotency key
);

CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    in_reply_to_message_id INTEGER NOT NULL REFERENCES messages(id),
    version INTEGER NOT NULL,
    engine TEXT NOT NULL,                  -- mock | openai
    model_id TEXT NOT NULL,
    model_registry_fingerprint TEXT NOT NULL,
    prompt_bundle_json TEXT NOT NULL,      -- hashes/versions of every prompt part
    intent TEXT NOT NULL,
    draft_text TEXT NOT NULL,              -- AI original; immutable after insert
    edited_text TEXT,
    claims_json TEXT NOT NULL,
    policy_flags_json TEXT NOT NULL,       -- model self-report
    guardrail_flags_json TEXT NOT NULL,    -- deterministic scan
    context_packet_json TEXT NOT NULL,     -- exactly what the engine was shown
    outcome TEXT NOT NULL CHECK (outcome IN ('completed', 'refusal', 'truncated', 'empty', 'error')),
    status TEXT NOT NULL CHECK (status IN ('drafted', 'needs_attention', 'edited', 'superseded', 'approved_sent', 'discarded', 'failed')),
    edited_by_advisor_id INTEGER REFERENCES advisors(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (in_reply_to_message_id, version)
);

CREATE TABLE IF NOT EXISTS profile_change_requests (
    id INTEGER PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    message_id INTEGER NOT NULL REFERENCES messages(id),
    draft_id INTEGER REFERENCES drafts(id),
    field_hint TEXT NOT NULL,              -- phone | email | address | interest | other
    requested_change TEXT NOT NULL,
    quote TEXT NOT NULL,                   -- verbatim from the client message
    source TEXT NOT NULL CHECK (source IN ('detector', 'model')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'dismissed')),
    created_at TEXT NOT NULL,
    resolved_by_advisor_id INTEGER REFERENCES advisors(id),
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS sends (
    id INTEGER PRIMARY KEY,
    draft_id INTEGER NOT NULL UNIQUE REFERENCES drafts(id),
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    outbound_message_id INTEGER NOT NULL REFERENCES messages(id),
    sent_text TEXT NOT NULL,               -- exact final bytes
    was_edited INTEGER NOT NULL DEFAULT 0,
    final_scan_flags_json TEXT NOT NULL,
    flags_acknowledged INTEGER NOT NULL DEFAULT 0,
    sender_impl TEXT NOT NULL,
    external_send_ref TEXT NOT NULL,
    sent_by_advisor_id INTEGER NOT NULL REFERENCES advisors(id),
    sent_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by_advisor_id INTEGER REFERENCES advisors(id)
);

-- Append-only: the repository layer exposes insert and read, never update or delete.
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    occurred_at TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('system', 'advisor')),
    actor_id INTEGER,
    event TEXT NOT NULL,
    thread_id INTEGER,
    message_id INTEGER,
    draft_id INTEGER,
    detail_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_drafts_message ON drafts(in_reply_to_message_id, version);
CREATE INDEX IF NOT EXISTS idx_threads_advisor ON threads(assigned_advisor_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_thread ON audit_log(thread_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_profile_changes_thread ON profile_change_requests(thread_id, status);
