"""Protocol & voice loading with the local overlay.

`protocols/examples/**` ships in the repo; `protocols/local/**` is gitignored
and holds the real Zadok materials. A local file with the same relative path
replaces its example; local-only files are added. Content hashes flow into
every draft's prompt bundle so output is traceable to script versions.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..utils import sha256_hex

PROTOCOLS_DIR = Path(__file__).resolve().parents[2] / "protocols"


@dataclass(frozen=True)
class ProtocolPack:
    intent: str
    files: tuple[tuple[str, str], ...]  # (name, content), core first
    pack_hash: str


def _overlaid_dir(subdir: str, base_dir: Path) -> dict[str, str]:
    merged: dict[str, str] = {}
    for root in (base_dir / "examples" / subdir, base_dir / "local" / subdir):
        if root.is_dir():
            for path in sorted(root.glob("*.md")):
                merged[path.stem] = path.read_text(encoding="utf-8")
    return merged


def load_pack(intent: str, base_dir: Path | None = None) -> ProtocolPack:
    scripts = _overlaid_dir("scripts", base_dir or PROTOCOLS_DIR)
    if "core" not in scripts:
        raise FileNotFoundError("protocols: scripts/core.md is required")
    ordered = [("core", scripts["core"])]
    if intent in scripts:
        ordered.append((intent, scripts[intent]))
    pack_hash = sha256_hex("\n".join(f"[{name}]\n{content}" for name, content in ordered))
    return ProtocolPack(intent=intent, files=tuple(ordered), pack_hash=pack_hash)


def load_voice(voice_key: str, base_dir: Path | None = None) -> tuple[str, str]:
    """Return (voice profile text, content hash). Missing voice -> empty profile."""
    voices = _overlaid_dir("voices", base_dir or PROTOCOLS_DIR)
    text = voices.get(voice_key, "")
    return text, sha256_hex(text)


def current_pack_hash(base_dir: Path | None = None) -> str:
    """Hash of the full script set — surfaced on /healthz."""
    scripts = _overlaid_dir("scripts", base_dir or PROTOCOLS_DIR)
    return sha256_hex("\n".join(f"[{name}]\n{scripts[name]}" for name in sorted(scripts)))
