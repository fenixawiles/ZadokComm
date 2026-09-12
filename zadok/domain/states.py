"""Draft lifecycle state machine.

A draft row is created directly in DRAFTED, NEEDS_ATTENTION (guardrail flags)
or FAILED (engine outcome other than completed). Regeneration never mutates a
draft's text: the active row becomes SUPERSEDED and a new row is inserted at
version + 1. APPROVED_SENT and SUPERSEDED are terminal for the row; FAILED and
DISCARDED are terminal except that the inbound message stays redraftable.
"""
from __future__ import annotations

DRAFTED = "drafted"
NEEDS_ATTENTION = "needs_attention"
EDITED = "edited"
SUPERSEDED = "superseded"
APPROVED_SENT = "approved_sent"
DISCARDED = "discarded"
FAILED = "failed"

ALL_STATUSES = (DRAFTED, NEEDS_ATTENTION, EDITED, SUPERSEDED, APPROVED_SENT, DISCARDED, FAILED)

EDIT = "edit"
REGENERATE = "regenerate"
APPROVE = "approve"
DISCARD = "discard"

# Statuses from which each advisor action is legal.
TRANSITIONS: dict[str, frozenset[str]] = {
    EDIT: frozenset({DRAFTED, NEEDS_ATTENTION, EDITED}),
    APPROVE: frozenset({DRAFTED, NEEDS_ATTENTION, EDITED}),
    DISCARD: frozenset({DRAFTED, NEEDS_ATTENTION, EDITED}),
    REGENERATE: frozenset({DRAFTED, NEEDS_ATTENTION, EDITED, FAILED, DISCARDED}),
}


class InvalidTransition(Exception):
    def __init__(self, action: str, current: str):
        super().__init__(f"Cannot {action} a draft in status {current!r}")
        self.action = action
        self.current = current


def check(action: str, current: str) -> None:
    allowed = TRANSITIONS.get(action)
    if allowed is None:
        raise ValueError(f"Unknown draft action: {action!r}")
    if current not in allowed:
        raise InvalidTransition(action, current)
