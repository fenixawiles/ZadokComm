import pytest

from zadok.domain.context_packet import ClientContextPacket
from zadok.drafting import guardrails

# The concept demo's own compliant drafts are the negative corpus: the
# approved register must never flag.
COMPLIANT = [
    "I don't have an availability update I can confirm for you today, but your interest remains noted "
    "and I'll reach out personally when I have a meaningful update.",
    "I don't have a new allocation update to give you today. Your interest in the Submariner remains noted.",
    "The steel Daytona receives significant interest, and I'm not able to confirm availability by email.",
    "I'd be happy to see you Saturday and help you explore Datejust options.",
]

VIOLATIONS = [
    ("we have one in stock", "availability_confirmed"),
    ("The watch is in-stock and waiting", "availability_confirmed"),
    ("It's available today if you hurry", "availability_confirmed"),
    ("I reserved one for you", "availability_confirmed"),
    ("A shipment just arrived this morning", "availability_confirmed"),
    ("You're next in line", "allocation_language"),
    ("Your allocation has been approved", "allocation_language"),
    ("It should arrive within a few days", "delivery_promise"),
    ("It will be here by Friday", "delivery_promise"),
    ("We're two weeks out at most", "delivery_promise"),
    ("I can offer a discount", "discount_talk"),
    ("Happy to take 10% off for you", "discount_talk"),
    ("We discounted it this weekend", "discount_talk"),
]


@pytest.mark.parametrize("text", COMPLIANT)
def test_compliant_register_never_flags(text):
    assert guardrails.scan_text(text) == []


@pytest.mark.parametrize("text,expected_flag", VIOLATIONS)
def test_violations_flag(text, expected_flag):
    flags = guardrails.scan_text(text)
    assert expected_flag in [f.id for f in flags]
    assert all(f.matched_span for f in flags)


def _packet(**extra):
    return ClientContextPacket.build(
        client_display_name="Alex Morgan",
        client_status="existing",
        assigned_advisor_name="Sarah Kline",
        advisor_sign_off="Sarah",
        availability_policy_state="no_availability_discussion",
        inbound_message_text="any updates?",
        **extra,
    )


def test_claims_must_cite_nonempty_allowlisted_fields():
    packet = _packet(expressed_interests=["GMT-Master II"])
    good = [{"claim": "interest", "source_field": "expressed_interests"}]
    assert guardrails.verify_claims(good, packet) == []

    unknown = [{"claim": "x", "source_field": "inventory_count"}]
    assert [f.id for f in guardrails.verify_claims(unknown, packet)] == ["unsupported_claim"]

    empty = [{"claim": "visited", "source_field": "last_visit_summary"}]
    assert [f.id for f in guardrails.verify_claims(empty, packet)] == ["unsupported_claim"]


def test_signoff_and_leak_checks():
    assert guardrails.signoff_flag("Hi Alex,\n\nAll noted.\n\nSarah", "Sarah") == []
    assert [f.id for f in guardrails.signoff_flag("Hi,\n\nBest regards,\nSarah Kline Team", "Sarah")] == ["wrong_signoff"]
    assert "ai_leak" in [f.id for f in guardrails.leak_flags("As an AI, I cannot")]
    assert "template_residue" in [f.id for f in guardrails.leak_flags("Dear {client_name}")]


def test_self_report_flags():
    flags = guardrails.policy_self_report_flags(
        {"mentions_availability": True, "mentions_delivery_timing": False, "mentions_discount": True}
    )
    assert {f.id for f in flags} == {"self_report:mentions_availability", "self_report:mentions_discount"}


def test_final_scan_covers_content_and_leaks():
    flags = guardrails.final_scan("Good news, it's in stock! As an AI I checked.")
    assert {"availability_confirmed", "ai_leak"} <= {f.id for f in flags}
