import pytest

from zadok.protocols.loader import current_pack_hash, load_pack, load_voice


@pytest.fixture
def proto_dir(tmp_path):
    (tmp_path / "examples" / "scripts").mkdir(parents=True)
    (tmp_path / "examples" / "voices").mkdir(parents=True)
    (tmp_path / "local" / "scripts").mkdir(parents=True)
    (tmp_path / "examples" / "scripts" / "core.md").write_text("core rules v1", encoding="utf-8")
    (tmp_path / "examples" / "scripts" / "status_checkin.md").write_text("checkin script", encoding="utf-8")
    (tmp_path / "examples" / "voices" / "sarah-kline.md").write_text("sarah voice", encoding="utf-8")
    return tmp_path


def test_pack_selects_core_plus_intent(proto_dir):
    pack = load_pack("status_checkin", base_dir=proto_dir)
    assert [name for name, _ in pack.files] == ["core", "status_checkin"]
    other = load_pack("pleasantry", base_dir=proto_dir)
    assert [name for name, _ in other.files] == ["core"]


def test_local_overlay_wins(proto_dir):
    baseline = load_pack("status_checkin", base_dir=proto_dir)
    (proto_dir / "local" / "scripts" / "status_checkin.md").write_text("THE REAL ZADOK SCRIPT", encoding="utf-8")
    overlaid = load_pack("status_checkin", base_dir=proto_dir)
    assert dict(overlaid.files)["status_checkin"] == "THE REAL ZADOK SCRIPT"
    assert overlaid.pack_hash != baseline.pack_hash, "pack hash must move with content"


def test_local_only_file_is_added(proto_dir):
    (proto_dir / "local" / "scripts" / "vip.md").write_text("vip handling", encoding="utf-8")
    pack = load_pack("vip", base_dir=proto_dir)
    assert dict(pack.files)["vip"] == "vip handling"
    assert current_pack_hash(base_dir=proto_dir) != ""


def test_missing_core_raises(tmp_path):
    (tmp_path / "examples" / "scripts").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        load_pack("status_checkin", base_dir=tmp_path)


def test_voice_lookup_and_missing_voice(proto_dir):
    text, digest = load_voice("sarah-kline", base_dir=proto_dir)
    assert text == "sarah voice" and len(digest) == 64
    missing, _ = load_voice("nobody", base_dir=proto_dir)
    assert missing == ""


def test_shipped_examples_load():
    pack = load_pack("status_checkin")
    names = [name for name, _ in pack.files]
    assert names[0] == "core"
    assert "status_checkin" in names
