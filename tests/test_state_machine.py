import pytest

from zadok.domain import states


@pytest.mark.parametrize("action,status", [
    (states.EDIT, states.DRAFTED),
    (states.EDIT, states.NEEDS_ATTENTION),
    (states.EDIT, states.EDITED),
    (states.APPROVE, states.DRAFTED),
    (states.APPROVE, states.NEEDS_ATTENTION),
    (states.APPROVE, states.EDITED),
    (states.DISCARD, states.DRAFTED),
    (states.REGENERATE, states.DRAFTED),
    (states.REGENERATE, states.FAILED),
    (states.REGENERATE, states.DISCARDED),
])
def test_legal_transitions(action, status):
    states.check(action, status)  # must not raise


@pytest.mark.parametrize("action,status", [
    (states.EDIT, states.SUPERSEDED),
    (states.EDIT, states.APPROVED_SENT),
    (states.EDIT, states.FAILED),
    (states.EDIT, states.DISCARDED),
    (states.APPROVE, states.SUPERSEDED),
    (states.APPROVE, states.APPROVED_SENT),
    (states.APPROVE, states.FAILED),
    (states.APPROVE, states.DISCARDED),
    (states.DISCARD, states.APPROVED_SENT),
    (states.DISCARD, states.FAILED),
    (states.REGENERATE, states.SUPERSEDED),
    (states.REGENERATE, states.APPROVED_SENT),
])
def test_illegal_transitions(action, status):
    with pytest.raises(states.InvalidTransition):
        states.check(action, status)


def test_unknown_action_rejected():
    with pytest.raises(ValueError):
        states.check("promote", states.DRAFTED)


def test_every_status_named_in_transitions_is_known():
    for allowed in states.TRANSITIONS.values():
        assert allowed <= set(states.ALL_STATUSES)
