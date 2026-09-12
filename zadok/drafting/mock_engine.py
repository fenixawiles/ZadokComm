"""Deterministic template engine — the zero-key path.

Everything the real engine does, minus the model: intent-matched templates
filled ONLY from packet fields, deterministic claims, detector-mirrored
profile extraction, and a deliberate `policy_stress` template that violates
protocol so the needs_attention flow can be demonstrated live and offline.
"""
from __future__ import annotations

from pathlib import Path

from ..domain.intents import detect_profile_changes
from .engine import OUTCOME_COMPLETED, DraftEngine, DraftRequest, DraftResult

TEMPLATES_DIR = Path(__file__).resolve().parent / "mock_templates"
MODEL_ID = "mock-templates-v1"


class _Blank(dict):
    def __missing__(self, key):  # unfilled placeholders render as nothing, never as residue
        return ""


def _load(name: str) -> tuple[list[str], list[str]]:
    path = TEMPLATES_DIR / f"{name}.txt"
    header, _, body = path.read_text(encoding="utf-8").partition("\n---\n")
    fields = [f.strip() for f in header.replace("fields:", "").split(",") if f.strip()]
    variants = [v.strip() + "\n" for v in body.split("\n===\n")]
    return fields, variants


class MockDraftEngine(DraftEngine):
    name = "mock"

    def draft(self, request: DraftRequest) -> DraftResult:
        packet = request.packet
        stress = "policy stress" in packet.inbound_message_text.lower()
        template_name = "policy_stress" if stress else request.protocol_pack.intent
        try:
            declared_fields, variants = _load(template_name)
        except FileNotFoundError:
            declared_fields, variants = _load("general")

        data = packet.to_dict()
        first_name = (packet.client_display_name or "there").split(" ")[0]
        values = _Blank({
            **{k: v for k, v in data.items() if isinstance(v, str)},
            "client_first_name": first_name,
            "advisor_sign_off": packet.advisor_sign_off,
            "primary_interest": (packet.expressed_interests or ("timepiece you have in mind",))[0],
            "slots_list": " and ".join(packet.appointment_slots) or "at a time that suits you",
        })
        text = variants[request.variant % len(variants)].format_map(values)

        claims = [
            {"claim": f"Drew on {field} from the CRM context", "source_field": field}
            for field in declared_fields
            if data.get(field) not in ("", [], None)
        ]
        return DraftResult(
            draft_text=text,
            intent=request.protocol_pack.intent,
            outcome=OUTCOME_COMPLETED,
            model_id=MODEL_ID,
            engine_name=self.name,
            claims_used=claims,
            profile_update_requests=detect_profile_changes(packet.inbound_message_text),
            policy_check={
                "mentions_availability": stress,
                "mentions_delivery_timing": stress,
                "mentions_discount": stress,
                "notes": "deterministic mock self-report",
            },
        )
