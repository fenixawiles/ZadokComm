"""OpenAI drafting engine — Responses API with strict structured outputs.

Call policy (ported from hard-won production behavior in the author's other
project and simplified for single-shot email drafting):

- Transport/API errors: up to 3 attempts with exponential backoff (1s/2s/4s),
  then outcome "error". Nothing partial is ever accepted.
- Truncation is checked BEFORE content is accepted: a response can look
  non-empty and still be cut mid-email. One retry with a doubled output
  budget; if still truncated, outcome "truncated" with NO text — a cut-off
  client email is worse than none.
- A refusal is returned immediately as outcome "refusal", never retried.
- A parse failure on a nominally completed strict response is outcome
  "error" (belt and braces; strict schema should prevent it).

The OpenAI SDK is imported lazily and only for live construction, so the
entire test suite and mock mode run without the package doing any work.
The client is injected for testability and duck-typed: it only needs
`client.responses.create(...)` returning an object with `status`,
`incomplete_details.reason`, `output_text`, and `output`.
"""
from __future__ import annotations

import json
import time

from ..domain.intents import INTENTS
from .engine import (
    OUTCOME_COMPLETED,
    OUTCOME_EMPTY,
    OUTCOME_ERROR,
    OUTCOME_REFUSAL,
    OUTCOME_TRUNCATED,
    DraftEngine,
    DraftRequest,
    DraftResult,
)
from .output_schema import DRAFT_OUTPUT_SCHEMA
from .prompt_builder import build_system_prompt, build_user_message

_BACKOFF_SECONDS = (1, 2, 4)


def _find_refusal(response) -> str | None:
    for item in getattr(response, "output", None) or []:
        if getattr(item, "type", None) == "message":
            for part in getattr(item, "content", None) or []:
                if getattr(part, "type", None) == "refusal":
                    return getattr(part, "refusal", "refused")
    return None


def _is_truncated(response) -> bool:
    if getattr(response, "status", None) != "incomplete":
        return False
    details = getattr(response, "incomplete_details", None)
    return getattr(details, "reason", None) == "max_output_tokens"


class OpenAIDraftEngine(DraftEngine):
    name = "openai"

    def __init__(self, client, model_id: str, max_output_tokens: int, sleep=time.sleep):
        self._client = client
        self._model_id = model_id
        self._max_output_tokens = max_output_tokens
        self._sleep = sleep

    def draft(self, request: DraftRequest) -> DraftResult:
        system_prompt, bundle = build_system_prompt(
            request.protocol_pack, request.voice_profile, request.voice_hash
        )
        user_message = build_user_message(request.packet, request.prior_draft_text)

        def _failure(outcome: str, detail: str) -> DraftResult:
            return DraftResult(
                draft_text="", intent=request.protocol_pack.intent, outcome=outcome,
                model_id=self._model_id, engine_name=self.name, prompt_bundle=bundle, detail=detail,
            )

        budget = self._max_output_tokens
        budget_raised = False
        response = None
        for attempt, backoff in enumerate(_BACKOFF_SECONDS, start=1):
            try:
                response = self._client.responses.create(
                    model=self._model_id,
                    instructions=system_prompt,
                    input=[{"role": "user", "content": user_message}],
                    max_output_tokens=budget,
                    text={"format": {"type": "json_schema", "name": "zadok_draft",
                                     "strict": True, "schema": DRAFT_OUTPUT_SCHEMA}},
                )
            except Exception as exc:  # transport/API errors — the SDK is duck-typed here
                if attempt == len(_BACKOFF_SECONDS):
                    return _failure(OUTCOME_ERROR, f"transport failure after {attempt} attempts: {exc}")
                self._sleep(backoff)
                continue

            # Order matters: truncation before any content is trusted.
            if _is_truncated(response):
                if budget_raised:
                    return _failure(OUTCOME_TRUNCATED, "still truncated after doubling the output budget")
                budget_raised = True
                budget *= 2
                continue
            break

        refusal = _find_refusal(response)
        if refusal is not None:
            return _failure(OUTCOME_REFUSAL, refusal)

        raw = (getattr(response, "output_text", "") or "").strip()
        if not raw:
            return _failure(OUTCOME_EMPTY, "no output text on a non-truncated response")

        try:
            payload = json.loads(raw)
            draft_text = payload["draft_text"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            return _failure(OUTCOME_ERROR, f"unparseable structured output: {exc}")

        intent = payload.get("intent")
        return DraftResult(
            draft_text=draft_text,
            intent=intent if intent in INTENTS else request.protocol_pack.intent,
            outcome=OUTCOME_COMPLETED,
            model_id=self._model_id,
            engine_name=self.name,
            prompt_bundle=bundle,
            claims_used=payload.get("claims_used", []),
            profile_update_requests=payload.get("profile_update_requests", []),
            policy_check=payload.get("policy_check", {}),
        )


def build_live_engine(cfg, model_artifact) -> OpenAIDraftEngine:
    """Construct the real client. Reaches the network only when called, which
    the engine factory allows only with the spend gate on and a key present."""
    from openai import OpenAI  # lazy: mock mode and tests never import the SDK

    client = OpenAI(api_key=cfg.effective_openai_api_key)
    return OpenAIDraftEngine(client, model_artifact.model_id, cfg.max_draft_output_tokens)
