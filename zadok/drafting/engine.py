"""DraftEngine interface — the plug point between the pipeline and any model."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.context_packet import ClientContextPacket
from ..protocols.loader import ProtocolPack

OUTCOME_COMPLETED = "completed"
OUTCOME_REFUSAL = "refusal"
OUTCOME_TRUNCATED = "truncated"
OUTCOME_EMPTY = "empty"
OUTCOME_ERROR = "error"

OUTCOMES = (OUTCOME_COMPLETED, OUTCOME_REFUSAL, OUTCOME_TRUNCATED, OUTCOME_EMPTY, OUTCOME_ERROR)


@dataclass(frozen=True)
class DraftRequest:
    packet: ClientContextPacket
    protocol_pack: ProtocolPack
    voice_profile: str
    voice_hash: str
    variant: int = 0                    # regeneration counter; lets engines vary output
    prior_draft_text: str | None = None


@dataclass(frozen=True)
class DraftResult:
    draft_text: str
    intent: str
    outcome: str
    model_id: str
    engine_name: str
    prompt_bundle: dict = field(default_factory=dict)
    claims_used: list = field(default_factory=list)          # [{claim, source_field}]
    profile_update_requests: list = field(default_factory=list)  # [{field_hint, requested_change, quote}]
    policy_check: dict = field(default_factory=dict)         # model self-report booleans
    detail: str = ""                                          # why outcome != completed


class DraftEngine:
    name = "abstract"

    def draft(self, request: DraftRequest) -> DraftResult:  # pragma: no cover - interface
        raise NotImplementedError
