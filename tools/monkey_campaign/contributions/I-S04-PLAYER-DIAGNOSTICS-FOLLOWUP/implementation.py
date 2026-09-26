"""implementation.py -- I-S04-PLAYER-DIAGNOSTICS-FOLLOWUP: the narrow adapter
from ACTUAL product error paths to the accepted player diagnostics
(parent I-S04-PLAYER-DIAGNOSTICS, merged PR #125; module identity pinned).

CORRECTION (lead finding on publication-e7eeb8677a2b400aaded97c27d66e95d):
the prior request resolved the seam's CommandRecord import from the LIVE play
worktree, whose HEAD 8d16d3c1 reorg deleted the sources (as-specified tests:
4/9 ModuleNotFoundError). The seam is now VENDORED byte-identically from the
pinned revision 9afbddcd (the same revision the accepted parent ledger cites)
under ``reference/`` with ``EXTRACTION_LEDGER.json``, and is materialized
HASH-ASSERTED at bind into a fresh OS temp directory in canonical repo layout
-- the campaign's established I-U07-TRACE-FOLLOWUP / I-R05 ``reference/``
pattern. Any byte drift refuses by name BEFORE import. No live worktree path
and no parent-reference directory remains on the seam import path.

The adapter adds NO vocabulary: every message/action comes from the accepted
module's explain* functions. It only routes real shapes to them:

  input_settings.Refusal           -> explain_settings_refusal(code, detail)
  session_flow.last_trace drops    -> explain_flow_drop(kind, detail, state)
  arbitrary exceptions             -> explain_exception(exc)
  LoadResult loaded/first_run      -> None (the module's own law: not failures)
  anything else / future codes     -> explain()'s honest unknown fallback

render() produces the one-line player-facing string for the samples table
(for later HUMAN review -- no player-validation is claimed here).
"""
from __future__ import annotations

import hashlib
import importlib
import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ACCEPTED_DIR = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/kanban-attempts/"
    "I-S04-PLAYER-DIAGNOSTICS/d24bd30d38234a4cae33288048cce14f")
ACCEPTED_SHA256 = \
    "53e34c62850ff222e2ecd92d20498baf88e9f8f0189b8c215d0cc79b06a7a339"
SEAM_REVISION = "9afbddcd90164b5544a16fd0bc72278d985eb6e3"
SCHEMA = "i-s04-followup.feedback_adapter.v1"

# ── the vendored seam pins (asserted at bind, loudly; details in the ledger) ──
SEAM_PINS = {
    "tools/monkey_campaign/product/input_settings.py":
        "8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1",
    "tools/monkey_campaign/product/session_flow.py":
        "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf",
    "tools/monkey_campaign/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "tools/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
}

_bound = {}


class AdapterIdentityFailure(RuntimeError):
    pass


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_pinned_seam(pins: dict | None = None,
                            root: pathlib.Path | None = None) -> pathlib.Path:
    """Copy the vendored ``reference/`` bytes into a fresh OS temp directory in
    the canonical repo layout, asserting every pin hash, so the UNMODIFIED
    files import exactly as they do at the pinned revision (their internal
    ``from tools.science_funnel...`` / flat ``import input_mapper`` resolve
    against the same layout).

    The only seam I/O this adapter performs; the directory is OS-disposable
    and nothing outside it is written. Fails closed by name.
    """
    pins = SEAM_PINS if pins is None else pins
    owns_root = root is None
    root = pathlib.Path(tempfile.mkdtemp(prefix="i_s04_followup_seam_")) \
        if root is None else pathlib.Path(root)
    try:
        for repo_path, want in pins.items():
            src = HERE / "reference" / repo_path
            if not src.is_file():
                raise AdapterIdentityFailure(
                    f"pinned_source_missing: {{'expected': '{src}'}}")
            got = _sha256_file(src)
            if got != want:
                raise AdapterIdentityFailure(
                    f"pinned_source_hash_mismatch: {{'path': '{repo_path}', "
                    f"'sha256': '{got}', 'expected': '{want}'}}")
            dst = root / repo_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    except Exception:
        if owns_root:
            shutil.rmtree(root, ignore_errors=True)
        raise
    return root


def bind():
    """Import the accepted module + the VENDORED pinned seam (identity
    checked at every layer). Cached; fails closed on mismatch."""
    if _bound:
        return _bound
    # 1) the ACCEPTED diagnostics module: imported, never copied; tamper refused
    module_path = ACCEPTED_DIR / "player_diagnostics.py"
    if not module_path.is_file():
        raise AdapterIdentityFailure("accepted module missing")
    actual = hashlib.sha256(module_path.read_bytes()).hexdigest()
    if actual != ACCEPTED_SHA256:
        raise AdapterIdentityFailure(f"accepted module drifted: {actual}")
    sys.path.insert(0, str(ACCEPTED_DIR))
    import player_diagnostics as pd  # noqa: PLC0415
    # 2) the vendored seam: cross-check the ledger against the code pins, then
    #    materialize hash-asserted and import from the canonical layout
    ref = HERE / "reference"
    ledger = json.loads((ref / "EXTRACTION_LEDGER.json").read_text("utf-8"))
    ledger_pins = {f["repo_path"]: f["sha256"] for f in ledger["files"]}
    if ledger_pins != SEAM_PINS:
        raise AdapterIdentityFailure("ledger/pin divergence")
    if ledger["provenance"]["seam_revision"] != SEAM_REVISION:
        raise AdapterIdentityFailure("seam revision drift")
    root = materialize_pinned_seam()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    iset = importlib.import_module("tools.monkey_campaign.product.input_settings")
    sf = importlib.import_module("tools.monkey_campaign.product.session_flow")
    # NOTE: input_settings additionally flat-imports input_mapper from its own
    # directory; both module instances come from the SAME hash-asserted bytes
    # with frozen constants, so no divergence is possible (nothing in the
    # adapter or tests compares identities across the two names).
    _bound.update(pd=pd, iset=iset, sf=sf, ref=ref, ledger=ledger,
                  seam_root=root)
    return _bound


# ── the adapter surface (narrow; no vocabulary of its own) ──────────────────
def translate_refusal(refusal) -> dict:
    """input_settings.Refusal -> accepted settings translation."""
    pd = bind()["pd"]
    diag = pd.explain_settings_refusal(refusal.code, refusal.detail)
    return diag.to_record()


def translate_flow_drop(kind: str, detail: str, state: str | None = None) -> dict:
    """session_flow.last_trace['dropped'] entry -> accepted flow translation."""
    pd = bind()["pd"]
    return pd.explain_flow_drop(kind, detail, state=state).to_record()


def translate_exception(exc: BaseException) -> dict:
    pd = bind()["pd"]
    return pd.explain_exception(exc).to_record()


def translate_load_result(result) -> dict | None:
    """input_settings.LoadResult -> diagnostic or None.

    'refused' translates its named refusals (first one, the player-facing
    law: one message, correlation preserved); 'loaded'/'first_run' are NOT
    failures and produce NOTHING (the accepted module's own law)."""
    status = getattr(result, "status", None)
    if status in ("loaded", "first_run"):
        return None
    if status == "refused":
        refusals = getattr(result, "refusals", ()) or ()
        if refusals:
            return translate_refusal(refusals[0])
    return None


def translate_unknown_name(name: str, detail: str = "") -> dict:
    """Anything not a pinned shape -> the accepted honest unknown fallback."""
    pd = bind()["pd"]
    return pd.explain(name, detail).to_record()


def render(record: dict) -> str:
    """One-line player-facing rendering of a diagnostic record (samples)."""
    actions = " / ".join(record.get("actions") or ())
    crid = record.get("correlation_id") or ""
    suffix = f" [ref {crid}]" if crid else ""
    if actions:
        return f"{record['message']} — try: {actions}{suffix}"
    return f"{record['message']}{suffix}"


def sample_table() -> list[dict]:
    """Deterministic user-visible samples for later HUMAN review."""
    bound = bind()
    iset = bound["iset"]
    samples = []
    with tempfile.TemporaryDirectory() as tmp:
        corrupt = pathlib.Path(tmp) / "corrupt.json"
        corrupt.write_bytes(b'{"bindings": [not json')
        result = iset.load_settings(str(corrupt))
        diag = translate_load_result(result)
        samples.append({"case": "settings: corrupt json (real refusal)",
                        "record": diag, "player_line": render(diag)})
        bad = pathlib.Path(tmp) / "bad_action.json"
        defaults = iset.default_settings()
        bad.write_text(json.dumps({
            "schema": iset.SCHEMA_ID,
            "bindings": {**defaults.bindings, "P9": "teleport"},
            "sensitivity": {"yaw": defaults.sensitivity},
            "invert": {"yaw": defaults.invert_yaw}}), encoding="utf-8")
        result2 = iset.load_settings(str(bad))
        diag2 = translate_load_result(result2)
        samples.append({"case": "settings: unknown action 'teleport' (real)",
                        "record": diag2, "player_line": render(diag2)})
    samples.append({
        "case": "future code (fabricated, must be unknown)",
        "record": translate_unknown_name("future_code_2030",
                                         "at C:/Users/x/save.json"),
        "player_line": render(translate_unknown_name("future_code_2030",
                                                     "at C:/Users/x/save.json"))})
    try:
        raise OSError("cannot read E:/saves/slot1.save.json")
    except OSError as exc:
        rec = translate_exception(exc)
        samples.append({"case": "path-bearing exception (must scrub message)",
                        "record": rec, "player_line": render(rec)})
    return samples


def main() -> int:
    samples = sample_table()
    out = HERE / "samples.json"
    out.write_text(json.dumps({"schema": SCHEMA, "samples": samples},
                              indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    for s in samples:
        print(s["case"], "->", s["player_line"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
