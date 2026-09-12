"""Deterministic triage: intent classification + profile-change detection.

This is where the owner-validated scope lives. The classifier is deliberately
rule-based so the shell behaves identically with no API key and its decisions
are explainable ("matched 'any update'"). In live mode the model's structured
intent refines the *label* on a draft; it never overrides the triage decision.

Triage policy (from the owner/sister): simple inquiries are handled by the
system, advisors answer the tougher stuff personally. Order matters below —
complaint cues are checked first so "I've checked in three times and still
haven't heard anything" reads as a complaint, not a status check-in.

availability_inquiry is triaged routine on purpose: the deflection reply is
the single most scripted message in the building (see the protocol pack), and
the guardrail bank exists precisely to police it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

STATUS_CHECKIN = "status_checkin"
PLEASANTRY = "pleasantry"
APPOINTMENT_REQUEST = "appointment_request"
AVAILABILITY_INQUIRY = "availability_inquiry"
COMPLAINT_OR_ESCALATION = "complaint_or_escalation"
NEW_PROSPECT_INQUIRY = "new_prospect_inquiry"
GENERAL = "general"

INTENTS = (
    STATUS_CHECKIN,
    PLEASANTRY,
    APPOINTMENT_REQUEST,
    AVAILABILITY_INQUIRY,
    COMPLAINT_OR_ESCALATION,
    NEW_PROSPECT_INQUIRY,
    GENERAL,
)

ROUTINE = "routine"
PERSONAL = "personal"

ROUTINE_INTENTS = frozenset({
    STATUS_CHECKIN,
    PLEASANTRY,
    APPOINTMENT_REQUEST,
    AVAILABILITY_INQUIRY,
    NEW_PROSPECT_INQUIRY,
})


@dataclass(frozen=True)
class Classification:
    intent: str
    triage: str
    reason: str


_COMPLAINT = re.compile(
    r"frustrat|disappoint|unacceptable|complaint|poor (service|communication)|speak (to|with) (a |the )?manager"
    r"|am i (actually|even|really)|still haven'?t heard|no one (has )?(responded|replied|answered)"
    r"|checked in (twice|three|four|several|multiple|\d+ times)|(second|third|fourth) time (i'?ve|asking)"
    r"|waste of|fed up|not (good|okay) enough",
    re.IGNORECASE,
)
_STATUS = re.compile(
    r"any (update|updates|news|luck|movement|word|progress)|how long|how much longer|still waiting"
    r"|any chance yet|heard anything|status (of|on)|where (are we|do i stand)",
    re.IGNORECASE,
)
_APPOINTMENT = re.compile(
    r"appointment|stop by|come (by|in)|swing by|visit|drop in|in person|see you (this|next)|schedule"
    r"|book (a )?time|available (to meet|for a visit)",
    re.IGNORECASE,
)
_AVAILABILITY = re.compile(
    r"do you have|in stock|availab|any chance (of|at)|can you (get|source|find)|looking for a|waitlist"
    r"|allocation|interested in (buying|purchasing)",
    re.IGNORECASE,
)
_PLEASANTRY = re.compile(
    r"^\W*(hey|hi|hello|good (morning|afternoon|evening))?[^.!?]{0,80}"
    r"(hope you('| a)re|thank(s| you)|thanks again|congratulations|happy holidays)",
    re.IGNORECASE,
)
_SUBSTANTIVE = re.compile(r"\?|please|could you|can you|need|issue|problem|help", re.IGNORECASE)


def classify(text: str, *, client_known: bool = True) -> Classification:
    body = (text or "").strip()

    match = _COMPLAINT.search(body)
    if match:
        return Classification(COMPLAINT_OR_ESCALATION, PERSONAL, f"matched {match.group(0)!r}")

    match = _STATUS.search(body)
    if match:
        return Classification(STATUS_CHECKIN, ROUTINE, f"matched {match.group(0)!r}")

    match = _APPOINTMENT.search(body)
    if match:
        return Classification(APPOINTMENT_REQUEST, ROUTINE, f"matched {match.group(0)!r}")

    match = _AVAILABILITY.search(body)
    if match:
        if not client_known:
            return Classification(NEW_PROSPECT_INQUIRY, ROUTINE, "unknown sender with a product inquiry")
        return Classification(AVAILABILITY_INQUIRY, ROUTINE, f"matched {match.group(0)!r}")

    if len(body) <= 220 and _PLEASANTRY.search(body) and not _SUBSTANTIVE.search(body):
        return Classification(PLEASANTRY, ROUTINE, "short greeting or thanks with no ask")

    if not client_known:
        return Classification(NEW_PROSPECT_INQUIRY, ROUTINE, "unknown sender, first inquiry")

    # Substantive or ambiguous messages stay with the advisor by default.
    return Classification(GENERAL, PERSONAL, "no routine pattern matched; advisor answers personally")


# --- profile-change detection -------------------------------------------------

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

_PROFILE_PATTERNS: tuple[tuple[str, str, re.Pattern], ...] = (
    ("phone", "Phone number update",
     re.compile(r"new (cell|mobile|phone|number)|number (is now|changed|has changed)|reach me at\s*\+?\(?\d", re.I)),
    ("email", "Email address update",
     re.compile(r"new email|email (me )?(at|is now)\s*\S+@|switch(ed)? (my )?email", re.I)),
    ("address", "Mailing address update",
     re.compile(r"new address|moved to|relocat(ed|ing)|address (is now|changed)", re.I)),
    ("interest", "Model interest update",
     re.compile(r"(now|instead|actually)[^.!?]{0,40}(interested in|looking at|prefer|want)|switched to"
                r"|changed my mind|rather than the|no longer (interested|looking)", re.I)),
)


def detect_profile_changes(text: str) -> list[dict]:
    """Return advisor-facing notes about profile data the client wants changed."""
    findings: list[dict] = []
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text or "") if s.strip()]
    for field_hint, label, pattern in _PROFILE_PATTERNS:
        for sentence in sentences:
            if pattern.search(sentence):
                findings.append({
                    "field_hint": field_hint,
                    "requested_change": label,
                    "quote": sentence[:300],
                })
                break
    return findings
