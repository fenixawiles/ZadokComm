"""ClientContextPacket — the ONLY thing a drafting engine is ever shown.

The allowlist is the privacy and compliance boundary:

- Field names are frozen. Constructing a packet with any field outside the
  allowlist raises ContaminationError, so new data cannot drift into prompts
  without a deliberate schema change here.
- Inventory is structurally excluded. There is no field that could carry a
  count; availability exists only as a coarse policy state. FORBIDDEN_KEY_RE
  additionally rejects any field name that even smells like stock data.
- A packet is built from exactly one resolved client record (see
  connectors/resolver.py), which structurally prevents cross-client leakage.
- The two untrusted fields (the inbound message and thread history) are
  client-authored text; the prompt builder places them only under the
  untrusted-content boundary in the user message, never in instructions.
"""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field

FORBIDDEN_KEY_RE = re.compile(r"inventory|stock|allocation|on_hand|quantity", re.IGNORECASE)

AVAILABILITY_POLICY_STATES = ("no_availability_discussion", "waitlist_discussion_allowed")

CLIENT_STATUSES = ("existing", "new_prospect")


class ContaminationError(ValueError):
    """A disallowed field tried to enter the drafting context."""


@dataclass(frozen=True)
class ClientContextPacket:
    client_display_name: str
    client_status: str
    assigned_advisor_name: str
    advisor_sign_off: str
    availability_policy_state: str
    inbound_message_text: str
    relationship_summary: str = ""
    purchase_history_summary: str = ""
    expressed_interests: tuple[str, ...] = ()
    last_visit_summary: str = ""
    last_contact_summary: str = ""
    appointment_slots: tuple[str, ...] = ()
    thread_history: tuple[tuple[str, str, str], ...] = ()  # (direction, sender, text)

    def __post_init__(self):
        for name in (self.client_status,):
            if name not in CLIENT_STATUSES:
                raise ContaminationError(f"client_status must be one of {CLIENT_STATUSES}, got {name!r}")
        if self.availability_policy_state not in AVAILABILITY_POLICY_STATES:
            raise ContaminationError(
                f"availability_policy_state must be one of {AVAILABILITY_POLICY_STATES}; raw availability "
                f"data must never enter the packet (got {self.availability_policy_state!r})"
            )

    @classmethod
    def build(cls, **fields) -> "ClientContextPacket":
        unknown = sorted(set(fields) - CLIENT_CONTEXT_ALLOWED_FIELDS)
        if unknown:
            raise ContaminationError(f"Disallowed context fields: {', '.join(unknown)}")
        forbidden = sorted(name for name in fields if FORBIDDEN_KEY_RE.search(name))
        if forbidden:
            raise ContaminationError(f"Forbidden context fields: {', '.join(forbidden)}")
        for key in ("expressed_interests", "appointment_slots"):
            if key in fields:
                fields[key] = tuple(fields[key])
        if "thread_history" in fields:
            fields["thread_history"] = tuple(tuple(entry) for entry in fields["thread_history"])
        return cls(**fields)

    def to_dict(self) -> dict:
        data = dataclasses.asdict(self)
        data["expressed_interests"] = list(self.expressed_interests)
        data["appointment_slots"] = list(self.appointment_slots)
        data["thread_history"] = [list(entry) for entry in self.thread_history]
        return data


CLIENT_CONTEXT_ALLOWED_FIELDS = frozenset(f.name for f in dataclasses.fields(ClientContextPacket))

# Client-authored content: data, never instructions. The prompt builder is the
# enforcement point; this set documents which fields it must quarantine.
UNTRUSTED_FIELDS = frozenset({"inbound_message_text", "thread_history"})

# Belt and braces: the allowlist itself must never grow a stock-shaped field.
_bad = [name for name in CLIENT_CONTEXT_ALLOWED_FIELDS if FORBIDDEN_KEY_RE.search(name)]
if _bad:  # pragma: no cover - import-time invariant
    raise ContaminationError(f"Packet schema contains forbidden fields: {_bad}")
