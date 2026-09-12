"""Deterministic guardrails.

Engine-agnostic and cheap, so they run on EVERY draft (mock included) and run
again on the final text at approve time — an advisor's edit can violate
protocol just as easily as a model's. A flag never blocks outright; it forces
the draft into needs_attention and makes Send require explicit, audited
acknowledgment.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.context_packet import CLIENT_CONTEXT_ALLOWED_FIELDS, ClientContextPacket


@dataclass(frozen=True)
class Flag:
    id: str
    label: str
    matched_span: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "matched_span": self.matched_span}


def _bank(pairs):
    return tuple((flag_id, label, re.compile(pattern, re.IGNORECASE)) for flag_id, label, pattern in pairs)


# Inflection-aware, tuned against the compliant register as a negative corpus:
# "I don't have an availability update I can confirm for you today" must pass.
_FORBIDDEN = _bank([
    ("availability_confirmed", "Confirms availability or inventory",
     r"\bin[\s-]stock\b|\bavailable\s+(now|today|immediately|for you)\b|\bjust\s+(arrived|came in|received)\b"
     r"|\bwe\s+(?:do\s+)?(?:have|hold)\s+(?:one|it|a|an|your)\b|\breserved?\s+(?:one|it|yours)\b"
     r"|\bset\s+aside\s+for\s+you\b"),
    ("allocation_language", "Discusses allocation or waitlist position",
     r"\byour\s+allocation\b|\bwaitlist\s+position\b|\byou'?re\s+next\b|\btop\s+of\s+the\s+(?:list|waitlist)\b"
     r"|\bmoved?\s+up\s+the\s+list\b"),
    ("delivery_promise", "Promises or estimates delivery timing",
     r"\bwill\s+(?:arrive|be\s+here|come\s+in|be\s+in|land)\s+(?:by|within|in|this|next)\b|\beta\b"
     r"|\bship(?:ping|ped)?\s+(?:by|within|out)\b|\bexpect(?:ed)?\s+(?:it|delivery|arrival)\s+(?:by|within|in)\b"
     r"|\b(?:a\s+few\s+|\d+\s*)(?:days|weeks|months)\s+out\b|\bshould\s+arrive\b"),
    ("discount_talk", "Mentions discounts or special pricing",
     r"\bdiscount(?:s|ed)?\b|%\s*off\b|\bspecial\s+pricing\b|\bprice\s+match\b|\bmarkdown\b"
     r"|\bbest\s+price\b|\bdeal\s+for\s+you\b"),
])

_LEAK = _bank([
    ("ai_leak", "References AI or internal systems",
     r"\bas\s+an\s+ai\b|\blanguage\s+model\b|\bthis\s+draft\b|\bautomatically\s+generated\b|\bCRM\b"),
    ("template_residue", "Unfilled template placeholder", r"\{\{|\{[a-z_]+\}|\[(?:INSERT|TODO|NAME)\b"),
])


def scan_text(text: str) -> list[Flag]:
    flags = []
    for flag_id, label, pattern in _FORBIDDEN:
        match = pattern.search(text)
        if match:
            flags.append(Flag(flag_id, label, match.group(0)))
    return flags


def leak_flags(text: str) -> list[Flag]:
    flags = []
    for flag_id, label, pattern in _LEAK:
        match = pattern.search(text)
        if match:
            flags.append(Flag(flag_id, label, match.group(0)))
    return flags


def verify_claims(claims: list, packet: ClientContextPacket) -> list[Flag]:
    """Every claim must cite an allowlisted field that is non-empty in THIS packet."""
    flags = []
    data = packet.to_dict()
    for entry in claims or []:
        source = (entry or {}).get("source_field", "")
        claim = (entry or {}).get("claim", "")
        if source not in CLIENT_CONTEXT_ALLOWED_FIELDS:
            flags.append(Flag("unsupported_claim", f"Claim cites unknown field {source!r}", claim[:80]))
            continue
        value = data.get(source)
        if value in ("", [], None):
            flags.append(Flag("unsupported_claim", f"Claim cites empty field {source!r}", claim[:80]))
    return flags


def policy_self_report_flags(policy_check: dict) -> list[Flag]:
    labels = {
        "mentions_availability": "Model self-reported availability talk",
        "mentions_delivery_timing": "Model self-reported delivery timing",
        "mentions_discount": "Model self-reported discount talk",
    }
    return [Flag(f"self_report:{key}", label) for key, label in labels.items() if (policy_check or {}).get(key)]


def signoff_flag(text: str, sign_off: str) -> list[Flag]:
    lines = [line.strip() for line in (text or "").strip().splitlines() if line.strip()]
    if not lines or lines[-1].rstrip(",.") != sign_off:
        return [Flag("wrong_signoff", f"Draft must end with the advisor sign-off {sign_off!r}",
                     lines[-1] if lines else "")]
    return []


def evaluate_draft(text: str, *, claims: list, policy_check: dict, packet: ClientContextPacket,
                   sign_off: str) -> list[Flag]:
    """Full evaluation at draft time."""
    return (
        scan_text(text)
        + verify_claims(claims, packet)
        + policy_self_report_flags(policy_check)
        + signoff_flag(text, sign_off)
        + leak_flags(text)
    )


def final_scan(text: str) -> list[Flag]:
    """Re-scan of the final (possibly advisor-edited) text at approve time."""
    return scan_text(text) + leak_flags(text)
