"""CrmConnector — the plug point for real CRM integrations.

The shell ships fixture-backed mocks. A real implementation replaces one class
and one config value, nothing else:

- Salesforce: implement with `simple-salesforce` (Connected App + OAuth,
  SOQL lookup by email, EmailMessage for outbound so Salesforce remains the
  record of communications). Set CRM_CONNECTORS=salesforce.
- Woven: pending API discovery (see docs/DISCOVERY.md). If Woven exposes no
  API, the fallback is a periodic export sync feeding the same interface.

Planned extension (deliberately NOT implemented in the shell):
    propose_profile_update(client_ref, field_hint, requested_change) -> ref
so acknowledged profile-change cards can write back to the CRM later.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class CrmConnector(ABC):
    #: short identifier used in client_ref prefixes and thread.crm_source
    source_name: str = "abstract"

    @abstractmethod
    def lookup_client(self, email: str) -> dict | None:
        """Return the raw client record for this email, or None."""

    @abstractmethod
    def lookup_client_by_ref(self, ref_id: str) -> dict | None:
        """Return the raw client record for this connector-local id, or None."""
