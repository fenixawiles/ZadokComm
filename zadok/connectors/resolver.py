"""Client resolution + packet assembly.

`build_packet` is the funnel between raw CRM records and the drafting engine.
It reads ONLY the keys named in RECORD_FIELD_MAP — a raw record may carry
anything (the fixtures deliberately include decoy inventory blocks) and none
of it can traverse, because unmapped keys are never read and the packet
constructor rejects out-of-allowlist fields with ContaminationError.
"""
from __future__ import annotations

from ..config import Config
from ..domain.context_packet import FORBIDDEN_KEY_RE, ClientContextPacket, ContaminationError
from ..domain.intents import APPOINTMENT_REQUEST
from .base import CrmConnector
from .mock_salesforce import MockSalesforceConnector
from .mock_woven import MockWovenConnector

CONNECTOR_FACTORIES = {
    "mock_salesforce": MockSalesforceConnector,
    "mock_woven": MockWovenConnector,
}

REF_PREFIXES = {"salesforce": "sf", "woven": "woven"}

# packet field -> raw record key. The ONLY reads build_packet performs.
RECORD_FIELD_MAP = {
    "client_display_name": "display_name",
    "client_status": "client_status",
    "relationship_summary": "relationship_summary",
    "purchase_history_summary": "purchase_history_summary",
    "expressed_interests": "expressed_interests",
    "last_visit_summary": "last_visit_summary",
    "last_contact_summary": "last_contact_summary",
    "availability_policy_state": "availability_policy_state",
    "appointment_slots": "appointment_availability",
}

_bad = [key for key in RECORD_FIELD_MAP.values() if FORBIDDEN_KEY_RE.search(key)]
if _bad:  # pragma: no cover - import-time invariant
    raise ContaminationError(f"RECORD_FIELD_MAP would read stock-shaped keys: {_bad}")


def build_connectors(cfg: Config) -> list[CrmConnector]:
    connectors = []
    for name in cfg.crm_connectors:
        factory = CONNECTOR_FACTORIES.get(name)
        if factory is None:
            raise ValueError(f"Unknown CRM connector {name!r} (known: {sorted(CONNECTOR_FACTORIES)})")
        connectors.append(factory())
    return connectors


def resolve_client(connectors: list[CrmConnector], email: str):
    """Walk connectors in configured order; first hit wins."""
    for connector in connectors:
        record = connector.lookup_client(email)
        if record is not None:
            return record, connector
    return None, None


def client_ref(connector: CrmConnector, record: dict) -> str:
    return f"{REF_PREFIXES[connector.source_name]}:{record['id']}"


def resolve_by_ref(connectors: list[CrmConnector], ref: str):
    prefix, _, ref_id = ref.partition(":")
    for connector in connectors:
        if REF_PREFIXES.get(connector.source_name) == prefix:
            record = connector.lookup_client_by_ref(ref_id)
            if record is not None:
                return record, connector
    return None, None


def build_packet(record: dict, *, advisor_row, intent: str, inbound_text: str,
                 thread_history: list[tuple[str, str, str]]) -> ClientContextPacket:
    """Assemble the drafting context from exactly ONE resolved client record."""
    fields = {}
    for packet_field, record_key in RECORD_FIELD_MAP.items():
        value = record.get(record_key)
        if value is not None:
            fields[packet_field] = value
    # Appointment slots surface only when the client is actually asking to visit.
    if intent != APPOINTMENT_REQUEST:
        fields["appointment_slots"] = ()
    fields.update(
        assigned_advisor_name=advisor_row["display_name"],
        advisor_sign_off=advisor_row["sign_off_name"],
        inbound_message_text=inbound_text,
        thread_history=thread_history,
    )
    return ClientContextPacket.build(**fields)


def build_unknown_packet(*, email: str, display_name: str, team_advisor_row, intent: str, inbound_text: str,
                         thread_history: list[tuple[str, str, str]]) -> ClientContextPacket:
    """Packet for a sender with no CRM record: minimal, new-prospect posture."""
    return ClientContextPacket.build(
        client_display_name=display_name or email,
        client_status="new_prospect",
        relationship_summary="No existing record in any CRM; first inquiry.",
        assigned_advisor_name=team_advisor_row["display_name"],
        advisor_sign_off=team_advisor_row["sign_off_name"],
        availability_policy_state="no_availability_discussion",
        inbound_message_text=inbound_text,
        thread_history=thread_history,
    )
