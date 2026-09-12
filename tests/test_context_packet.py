import json

import pytest

from zadok.connectors import resolver
from zadok.connectors.mock_salesforce import MockSalesforceConnector
from zadok.connectors.mock_woven import MockWovenConnector
from zadok.domain.context_packet import (
    CLIENT_CONTEXT_ALLOWED_FIELDS,
    ClientContextPacket,
    ContaminationError,
)
from zadok.domain.intents import APPOINTMENT_REQUEST, STATUS_CHECKIN
from zadok.drafting.output_schema import DRAFT_OUTPUT_SCHEMA

ADVISOR = {"display_name": "Sarah Kline", "sign_off_name": "Sarah"}


def base_fields(**extra):
    fields = dict(
        client_display_name="Alex Morgan",
        client_status="existing",
        assigned_advisor_name="Sarah Kline",
        advisor_sign_off="Sarah",
        availability_policy_state="no_availability_discussion",
        inbound_message_text="any updates?",
    )
    fields.update(extra)
    return fields


def test_disallowed_field_raises():
    with pytest.raises(ContaminationError, match="loyalty_tier"):
        ClientContextPacket.build(**base_fields(loyalty_tier="platinum"))


def test_forbidden_stock_shaped_field_raises():
    with pytest.raises(ContaminationError):
        ClientContextPacket.build(**base_fields(inventory_count=3))


def test_raw_availability_value_rejected():
    with pytest.raises(ContaminationError):
        ClientContextPacket.build(**base_fields(availability_policy_state="2 in stock"))


def test_decoy_inventory_never_reaches_the_packet():
    """The fixtures deliberately plant inventory blocks; prove they can't traverse."""
    for connector, email in ((MockSalesforceConnector(), "alex.morgan@example.com"),
                             (MockWovenConnector(), "mia.chen@example.com")):
        record = connector.lookup_client(email)
        assert any("inventory" in k or "stock" in k for k in record), "fixture must carry a decoy"
        packet = resolver.build_packet(record, advisor_row=ADVISOR, intent=STATUS_CHECKIN,
                                       inbound_text="any updates?", thread_history=[])
        blob = json.dumps(packet.to_dict()).lower()
        assert "inventory" not in blob
        assert "stock" not in blob
        assert "on_hand" not in blob


def test_slots_only_for_appointment_intent():
    record = MockWovenConnector().lookup_client("mia.chen@example.com")
    quiet = resolver.build_packet(record, advisor_row=ADVISOR, intent=STATUS_CHECKIN,
                                  inbound_text="any updates?", thread_history=[])
    assert quiet.appointment_slots == ()
    asking = resolver.build_packet(record, advisor_row=ADVISOR, intent=APPOINTMENT_REQUEST,
                                   inbound_text="can I stop by Saturday?", thread_history=[])
    assert asking.appointment_slots == ("Saturday 10:30 AM", "Saturday 11:45 AM")


def test_allowlist_drives_output_schema_enum():
    schema_enum = set(
        DRAFT_OUTPUT_SCHEMA["properties"]["claims_used"]["items"]["properties"]["source_field"]["enum"]
    )
    assert schema_enum == set(CLIENT_CONTEXT_ALLOWED_FIELDS)


def test_unknown_packet_is_minimal_new_prospect():
    packet = resolver.build_unknown_packet(
        email="jordan.lee@example.com", display_name="Jordan Lee",
        team_advisor_row={"display_name": "New-Client Team", "sign_off_name": "Maya"},
        intent="new_prospect_inquiry", inbound_text="Do you have a Daytona?", thread_history=[],
    )
    assert packet.client_status == "new_prospect"
    assert packet.availability_policy_state == "no_availability_discussion"
    assert packet.purchase_history_summary == ""
