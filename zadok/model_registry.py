"""Pinned model registry.

Every draft row records the exact model id and a fingerprint of this registry,
so the answer to "which model wrote the email we sent that client?" is always
one query away. Model ids are dated snapshots, pinned on purpose — a floating
alias would silently change what clients receive.
"""
from __future__ import annotations

from dataclasses import dataclass

from .utils import sha256_hex


@dataclass(frozen=True)
class ModelArtifact:
    key: str
    provider: str
    model_id: str
    pinned: bool
    notes: str


REGISTRY: dict[str, ModelArtifact] = {
    "draft": ModelArtifact(
        key="draft",
        provider="OpenAI",
        model_id="gpt-5.1-2025-11-13",
        pinned=True,
        notes="Client-facing reply drafting via the Responses API with strict structured outputs.",
    ),
}


def get_artifact(key: str = "draft") -> ModelArtifact:
    return REGISTRY[key]


def registry_fingerprint() -> str:
    canonical = "|".join(
        f"{a.key}:{a.provider}:{a.model_id}:{int(a.pinned)}" for a in sorted(REGISTRY.values(), key=lambda a: a.key)
    )
    return sha256_hex(canonical)
