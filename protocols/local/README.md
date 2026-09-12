# protocols/local/ — real Zadok materials live here (never in git)

Everything in this directory except this README is gitignored.

Drop the real, confidential materials here and they load at runtime,
overriding the shipped examples by filename:

- `local/scripts/<name>.md` replaces `examples/scripts/<name>.md`
  (e.g. the actual new-client welcome template → `scripts/new_prospect_inquiry.md`,
  the actual Rolex AD communication guidance → `scripts/core.md`).
- `local/voices/<voice_key>.md` replaces the synthetic advisor voice profiles
  with real writing samples (collect these with each advisor's permission).

Files that exist only here (no example counterpart) are added to the pack.
Every draft records a content hash of the protocol pack it was built with,
so which script version produced which email is always auditable.
