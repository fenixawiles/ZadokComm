"""Strict structured-output schema for the OpenAI draft engine.

The claims `source_field` enum is generated from the packet allowlist so
there is exactly one source of truth for what the model may cite.
"""
from __future__ import annotations

from ..domain.context_packet import CLIENT_CONTEXT_ALLOWED_FIELDS
from ..domain.intents import INTENTS

PROFILE_FIELD_HINTS = ("phone", "email", "address", "interest", "other")

DRAFT_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["draft_text", "intent", "claims_used", "profile_update_requests", "policy_check"],
    "properties": {
        "draft_text": {"type": "string"},
        "intent": {"type": "string", "enum": list(INTENTS)},
        "claims_used": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["claim", "source_field"],
                "properties": {
                    "claim": {"type": "string"},
                    "source_field": {"type": "string", "enum": sorted(CLIENT_CONTEXT_ALLOWED_FIELDS)},
                },
            },
        },
        "profile_update_requests": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["field_hint", "requested_change", "quote"],
                "properties": {
                    "field_hint": {"type": "string", "enum": list(PROFILE_FIELD_HINTS)},
                    "requested_change": {"type": "string"},
                    "quote": {"type": "string"},
                },
            },
        },
        "policy_check": {
            "type": "object",
            "additionalProperties": False,
            "required": ["mentions_availability", "mentions_delivery_timing", "mentions_discount", "notes"],
            "properties": {
                "mentions_availability": {"type": "boolean"},
                "mentions_delivery_timing": {"type": "boolean"},
                "mentions_discount": {"type": "boolean"},
                "notes": {"type": "string"},
            },
        },
    },
}
