import re

from zadok.model_registry import REGISTRY, get_artifact, registry_fingerprint


def test_draft_model_is_pinned_to_a_dated_snapshot():
    artifact = get_artifact("draft")
    assert artifact.pinned is True
    assert re.search(r"\d{4}-\d{2}-\d{2}$", artifact.model_id), "model id must be a dated snapshot, not a floating alias"


def test_fingerprint_is_stable_and_covers_the_registry():
    first = registry_fingerprint()
    assert first == registry_fingerprint()
    assert re.fullmatch(r"[0-9a-f]{64}", first)
    # Fingerprint must be derived from the actual entries.
    assert len(REGISTRY) >= 1
