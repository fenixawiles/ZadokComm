"""OutboundSender — the send plug point.

The shell ships ONLY the mock sender; it records the send and nothing leaves
the machine. The real implementation must send through the CRM that is the
system of record (e.g. Salesforce EmailMessage / the Woven equivalent) so
every client communication stays logged where compliance expects it —
never through a side channel. Wiring a real sender requires
ZADOK_ALLOW_LIVE_SEND=1; the factory below refuses anything else at boot.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from ..config import Config, ConfigError


class OutboundSender(ABC):
    name = "abstract"

    @abstractmethod
    def send(self, thread, text: str, advisor) -> str:
        """Send `text` to the thread's client as the advisor; return an external ref."""


class MockOutboundSender(OutboundSender):
    name = "mock"

    def send(self, thread, text: str, advisor) -> str:
        return f"mock-{uuid.uuid4().hex[:12]}"


def resolve_sender(cfg: Config) -> OutboundSender:
    if cfg.outbound_sender == "mock":
        return MockOutboundSender()
    if not cfg.allow_live_send:
        raise ConfigError(
            f"Outbound sender {cfg.outbound_sender!r} requires ZADOK_ALLOW_LIVE_SEND=1."
        )
    raise ConfigError(f"No implementation for outbound sender {cfg.outbound_sender!r} in the shell.")
