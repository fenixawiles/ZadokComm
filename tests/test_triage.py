import pytest

from zadok.domain import intents

# The sister's three examples of "simple", verbatim, must be routine.
SISTER_EXAMPLES = [
    "any updates?",
    "How long?",
    "Hey hope you're doing well thanks!",
]


@pytest.mark.parametrize("text", SISTER_EXAMPLES)
def test_sister_examples_are_routine(text):
    result = intents.classify(text)
    assert result.triage == intents.ROUTINE


@pytest.mark.parametrize("text,intent", [
    ("Hey Sarah — any luck with the GMT we talked about? If you've got one, I can come by this afternoon.",
     intents.STATUS_CHECKIN),
    ("Could I stop by Saturday to look at Datejust options?", intents.APPOINTMENT_REQUEST),
    ("Do you have a Submariner in the case?", intents.AVAILABILITY_INQUIRY),
    ("Hey Sarah, hope you're doing well — thanks again for everything!", intents.PLEASANTRY),
])
def test_routine_intents(text, intent):
    result = intents.classify(text, client_known=True)
    assert result.intent == intent
    assert result.triage == intents.ROUTINE


def test_complaint_wins_over_checkin_phrasing():
    text = ("I've checked in three times about the Submariner and still haven't heard anything useful. "
            "Am I actually being considered or not?")
    result = intents.classify(text, client_known=True)
    assert result.intent == intents.COMPLAINT_OR_ESCALATION
    assert result.triage == intents.PERSONAL


def test_unknown_sender_product_inquiry_is_new_prospect():
    result = intents.classify("I'm looking for a steel Daytona. Do you have one available?", client_known=False)
    assert result.intent == intents.NEW_PROSPECT_INQUIRY
    assert result.triage == intents.ROUTINE


def test_unknown_sender_complaint_stays_personal():
    result = intents.classify("This is unacceptable, I want to speak with a manager.", client_known=False)
    assert result.triage == intents.PERSONAL


def test_substantive_general_message_is_personal():
    result = intents.classify("My bracelet clasp broke while traveling, what should I do about the warranty?",
                              client_known=True)
    assert result.intent == intents.GENERAL
    assert result.triage == intents.PERSONAL


def test_reason_is_explainable():
    result = intents.classify("any updates?")
    assert "any update" in result.reason
