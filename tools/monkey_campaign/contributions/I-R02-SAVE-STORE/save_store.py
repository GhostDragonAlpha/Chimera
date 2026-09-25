"""save_store.py -- I-R02-SAVE-STORE: an atomic user-save envelope store.

OBJECTIVE (bounded implementation claim I-R02-SAVE-STORE): wrap opaque existing
engine snapshot bytes in a durable, self-verifying *envelope* and expose save /
load / list over named slots -- WITHOUT inventing any physics serialization. The
payload is treated as opaque bytes; this store records WHAT was saved (identities
+ payload hash) and guarantees the bytes return byte-exact. The engine owns how
snapshot bytes are produced/consumed; this module owns durability and identity
refusal.

THE ENVELOPE (one self-contained JSON document, so a single atomic replace is the
whole unit of durability):

    {
      "schema": "chimera.monkey_save_envelope.v1",
      "format_version": <positive int>,          # caller supplied
      "build_id": "<non-empty str>",             # caller supplied
      "scene_id": "<non-empty str>",             # caller supplied
      "policy_id": "<non-empty str>",            # caller supplied
      "payload_sha256": "<hex of the raw payload>",
      "payload_size": <int byte length of payload>,
      "payload_b64": "<base64(raw payload)>"
    }

The document is serialized deterministically (sorted keys, fixed separators, one
trailing newline) so two saves of equal inputs are byte-identical. The payload is
base64 *inside* the document: there is no separate header+body file to truncate
across, and nothing stored is ever executed or unpickled -- only decoded.

THE ATOMIC WRITE LAW (reused verbatim from input_settings.py at base revision,
not duplicated): canonical UTF-8 bytes -> temp file in the DESTINATION directory
-> flush + fsync -> os.replace; the temp file is removed on any failure so no
partial document is ever observable under a real slot name. An interrupted write
therefore leaves the previous valid save intact (falsifier 1).

THE REFUSING READ (shape reused from input_settings.load): absent file ->
"first_run" and nothing created; corrupt UTF-8 / duplicate JSON keys / NaN or
Infinity literals / unknown schema / wrong types each refuse by NAME. The payload
hash is recomputed on load and must match the stored hash, so a truncated or
tampered payload refuses (falsifier 3). Identities are matched against any caller
supplied expected values; a mismatch, or a missing expected identity that was not
stored, refuses -- no silent default, no inferred compatibility.

THE SLOT NAME LAW: a slot is FLAT -- its name carries no path separator and no
".." component, so it resolves to exactly one file under the explicitly supplied
user directory. A name that would escape the caller directory (absolute path,
drive letter, "..", or any separator) refuses (falsifier 2).

STANDALONE: stdlib only (base64, hashlib, json, os, pathlib, dataclasses). No
engine import, no pickle module, no eval/exec -- so tests are CPU-only and bounded.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Optional

SCHEMA_ID = "chimera.monkey_save_envelope.v1"
SUFFIX = ".save.json"                       # real on-disk slot files end with this
DEFAULT_MAX_PAYLOAD_BYTES = 8 * 1024 * 1024  # 8 MiB default; bounded, overridable
_HEADER_BUDGET_BYTES = 512                  # slack for header text + b64 rounding

__all__ = [
    "SaveStore", "Refusal", "LoadResult", "SaveResult", "SlotInfo",
    "SaveError", "SlotNameError", "EnvelopeError",
    "SCHEMA_ID", "SUFFIX", "DEFAULT_MAX_PAYLOAD_BYTES",
]


# ── refusals: machine code + human detail, refuse BY NAME never silently ─────
@dataclass(frozen=True)
class Refusal:
    code: str
    detail: str


# ── caller-input errors at save time (the store refuses, never defaults) ─────
class SaveError(Exception):
    """A required save input was missing, wrong-typed, or out of bound.

    Carries the named Refusal so a caller can branch on refusal.code."""

    def __init__(self, refusal: Refusal):
        super().__init__(refusal.detail)
        self.refusal = refusal


class SlotNameError(SaveError):
    """A slot name could resolve outside the caller's user directory."""


# ── parse errors on stored bytes (surfaced as LoadResult refusals, not raised)
class EnvelopeError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


# ── results ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SaveResult:
    slot_name: str
    path: str
    bytes_written: int
    atomic: bool


@dataclass(frozen=True)
class LoadResult:
    """Outcome of a load. status is exactly one of "loaded" | "first_run" |
    "refused"; on "refused", payload is b"" and refusals names every offense."""

    slot_name: str
    status: str
    payload: bytes = b""
    refusals: tuple = ()
    format_version: object = None
    build_id: object = None
    scene_id: object = None
    policy_id: object = None
    payload_size: int = 0
    payload_sha256: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "loaded"


@dataclass(frozen=True)
class SlotInfo:
    """Metadata for one stored slot, as reported by SaveStore.list(). Payload
    bytes are NOT returned -- only the header's identities and hash/size. status
    is "ok" when the envelope parsed and validated, else "unreadable"."""

    slot_name: str
    status: str
    format_version: object = None
    build_id: object = None
    scene_id: object = None
    policy_id: object = None
    payload_size: int = 0
    payload_sha256: str = ""
    detail: str = ""


# ── refusing JSON hooks (reuse input_settings' parser law) ───────────────────
def _pairs_refusing_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise EnvelopeError("key_duplicate",
                                f"duplicate JSON key {key!r} -- JSON would "
                                f"silently last-win; the envelope is refused")
        seen[key] = value
    return seen


def _refuse_non_finite(token):
    raise EnvelopeError("not_finite_json",
                        f"non-finite JSON literal {token!r} (NaN/Infinity are "
                        f"not numbers this schema accepts)")


# ── the envelope document builder + canonical bytes ─────────────────────────
def _canonical_envelope_bytes(doc: dict) -> bytes:
    """Deterministic v1 envelope bytes (sorted keys, fixed separators, one
    trailing newline). Equal inputs -> byte-identical output."""
    return (json.dumps(doc, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _build_envelope(format_version, build_id, scene_id, policy_id, payload: bytes):
    return {
        "schema": SCHEMA_ID,
        "format_version": int(format_version),
        "build_id": str(build_id),
        "scene_id": str(scene_id),
        "policy_id": str(policy_id),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_size": len(payload),
        "payload_b64": base64.b64encode(payload).decode("ascii"),
    }


# ── slot-name validation (FLAT: no separator, no "..", cannot escape) ────────
def _validate_slot_name(user_dir: str, slot_name):
    """Return the absolute real path of the slot file, or raise SlotNameError.

    A flat name with no path separator and no '..' component can only resolve to
    one file under user_dir; the realpath containment check is defense in depth."""
    if not isinstance(slot_name, str) or slot_name == "":
        raise SlotNameError(Refusal("slot_empty",
                                    "slot name must be a non-empty string"))
    if "\\" in slot_name or "/" in slot_name:
        raise SlotNameError(Refusal(
            "slot_traversal",
            f"slot name {slot_name!r} carries a path separator; slot names are "
            f"flat filenames, so they cannot escape the user directory"))
    parts = slot_name.split(os.sep)
    for part in parts:
        if part == "..":
            raise SlotNameError(Refusal(
                "slot_traversal",
                f"slot name {slot_name!r} contains '..' and could escape the "
                f"user directory"))
    candidate = os.path.join(user_dir, slot_name + SUFFIX)
    real_candidate = os.path.realpath(candidate)
    real_root = os.path.realpath(user_dir)
    if real_candidate != real_root and not real_candidate.startswith(real_root + os.sep):
        raise SlotNameError(Refusal(
            "slot_outside_user_dir",
            f"slot {slot_name!r} resolves to {real_candidate}, outside the user "
            f"directory {real_root}"))
    return candidate


# ── bounded read of stored bytes ─────────────────────────────────────────────
def _read_bounded(path: str, limit: int):
    """Return (raw_bytes) or None if absent. Raise EnvelopeError if too large;
    raise OSError on IO failure (caller converts to a refused LoadResult)."""
    try:
        size = os.path.getsize(path)
    except FileNotFoundError:
        return None
    if size > limit:
        raise EnvelopeError("envelope_too_large",
                            f"envelope is {size} bytes, over the bound of "
                            f"{limit} bytes")
    with open(path, "rb") as handle:
        data = handle.read(limit)
    if len(data) < size:            # shorthead: truncated file
        raise EnvelopeError("envelope_truncated",
                            f"envelope read {len(data)} of {size} bytes before "
                            f"EOF (truncated or mid-write)")
    return data


# ── parse + validate a stored envelope -> fields dict, else EnvelopeError ────
def _parse_and_validate(raw: bytes):
    """Decode and validate one stored envelope. Raise EnvelopeError with the
    SPECIFIC refusal code on the FIRST offense (fail-fast), so load() can report
    exactly which law was broken rather than a generic 'invalid' bucket."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EnvelopeError("not_utf8", f"envelope is not valid UTF-8: {exc}")
    try:
        document = json.loads(text, object_pairs_hook=_pairs_refusing_duplicates,
                              parse_constant=_refuse_non_finite)
    except EnvelopeError:
        raise
    except json.JSONDecodeError as exc:
        raise EnvelopeError("json_corrupt", f"envelope is not valid JSON: {exc}")

    if not isinstance(document, dict):
        raise EnvelopeError("root_not_object", "the envelope must be a JSON object")

    fields = {}

    schema = document.get("schema")
    if schema != SCHEMA_ID:
        raise EnvelopeError("schema_unknown",
                            f"unknown schema {schema!r}; opens exactly "
                            f"{SCHEMA_ID!r}")

    fv = document.get("format_version")
    if isinstance(fv, bool) or not isinstance(fv, int) or fv <= 0:
        raise EnvelopeError("format_version_type",
                            f"format_version must be a positive integer, found "
                            f"{fv!r}")
    fields["format_version"] = fv

    for ident in ("build_id", "scene_id", "policy_id"):
        value = document.get(ident)
        if not isinstance(value, str) or value == "":
            raise EnvelopeError(
                f"{ident}_missing",
                f"envelope identity {ident!r} is missing or empty -- a save "
                f"without an identity cannot be reliably loaded")
        fields[ident] = value

    psize = document.get("payload_size")
    if isinstance(psize, bool) or not isinstance(psize, int) or psize < 0:
        raise EnvelopeError("payload_size_type",
                            f"payload_size must be a non-negative integer, found "
                            f"{psize!r}")

    phash = document.get("payload_sha256")
    if not isinstance(phash, str) or len(phash) != 64:
        raise EnvelopeError("payload_hash_type",
                            f"payload_sha256 must be a 64-char hex string, found "
                            f"{phash!r}")

    b64 = document.get("payload_b64")
    if not isinstance(b64, str):
        raise EnvelopeError("payload_b64_type",
                            f"payload_b64 must be a base64 string, found "
                            f"{type(b64).__name__}")

    # Decode + verify the opaque payload against its recorded hash.
    try:
        payload = base64.b64decode(b64, validate=True)
    except (ValueError, TypeError):
        raise EnvelopeError("payload_b64_invalid",
                            "payload_b64 is not valid standard base64")
    if len(payload) != psize:
        raise EnvelopeError("payload_size_mismatch",
                            f"decoded payload is {len(payload)} bytes but "
                            f"payload_size declares {psize}")
    actual = hashlib.sha256(payload).hexdigest()
    if actual != phash:
        raise EnvelopeError("payload_hash_mismatch",
                            f"payload sha256 {actual!r} does not match the "
                            f"recorded hash {phash!r} (truncated or tampered)")

    fields.update({
        "payload": payload,
        "payload_size": psize,
        "payload_sha256": phash,
    })
    return fields


# ── the store ────────────────────────────────────────────────────────────────
class SaveStore:
    """An atomic user-save envelope store over named flat slots.

        store = SaveStore(user_directory="E:/saves")
        store.save("clearing_1", format_version=3, build_id="b-8630",
                   scene_id="forest-one", policy_id="gait-v2", payload=snap)
        result = store.load("clearing_1", expected_build_id="b-8630")
        assert result.ok and result.payload == snap
        meta = store.list()                       # metadata only, no payloads

    All slots live directly under user_directory as "<slot>.save.json". The user
    directory is supplied by the caller; this store never writes outside it."""

    def __init__(self, user_directory, *,
                 max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES):
        if not isinstance(max_payload_bytes, int) or isinstance(max_payload_bytes, bool) \
                or max_payload_bytes <= 0:
            raise SaveError(Refusal(
                "max_payload_bytes_type",
                f"max_payload_bytes must be a positive integer, found "
                f"{max_payload_bytes!r}"))
        self.user_directory = str(user_directory)
        self.max_payload_bytes = max_payload_bytes
        # b64 inflates ~4/3; add header slack. Bounded on both save and load.
        self.max_envelope_bytes = int(max_payload_bytes * 4 / 3) + 4 + _HEADER_BUDGET_BYTES

    # ── save: atomic temp+fsync+replace, refuse bad input before writing ────
    def save(self, slot_name, *, format_version, build_id, scene_id, policy_id,
             payload):
        """Atomically write an envelope for `payload` under `slot_name`.

        Required identities (format_version int>0; build/scene/policy non-empty
        str) must all be present -- a missing identity raises SaveError rather
        than being defaulted. payload is bytes, bounded by max_payload_bytes.
        Returns SaveResult(slot_name, path, bytes_written, atomic=True)."""
        # identities: refuse-by-name, never default (falsifier 3 precondition)
        if isinstance(format_version, bool) or not isinstance(format_version, int) \
                or format_version <= 0:
            raise SaveError(Refusal(
                "format_version_type",
                f"format_version must be a positive integer, found "
                f"{format_version!r}"))
        for ident, value in (("build_id", build_id), ("scene_id", scene_id),
                             ("policy_id", policy_id)):
            if not isinstance(value, str) or value == "":
                raise SaveError(Refusal(
                    f"{ident}_missing",
                    f"identity {ident!r} is required and must be a non-empty "
                    f"string; refusing to store an envelope that cannot be "
                    f"reliably loaded"))
        # payload: bytes only, bounded, never executed/unpickled
        if isinstance(payload, bool) or not isinstance(payload, (bytes, bytearray, memoryview)):
            raise SaveError(Refusal(
                "payload_type",
                f"payload must be bytes-like, found {type(payload).__name__}"))
        payload = bytes(payload)
        if len(payload) > self.max_payload_bytes:
            raise SaveError(Refusal(
                "payload_too_large",
                f"payload is {len(payload)} bytes, over the bound of "
                f"{self.max_payload_bytes}"))

        path = _validate_slot_name(self.user_directory, slot_name)
        document = _build_envelope(format_version, build_id, scene_id, policy_id,
                                   payload)
        blob = _canonical_envelope_bytes(document)

        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)          # explicit save: create dir
        tmp = os.path.join(directory, f".{slot_name}.tmp-{os.getpid()}")
        try:
            with open(tmp, "wb") as handle:
                handle.write(blob)
                handle.flush()
                os.fsync(handle.fileno())              # durability before rename
            os.replace(tmp, path)                      # atomic on POSIX + Windows
        except BaseException:
            try:
                os.unlink(tmp)                         # no partial file survives
            except OSError:
                pass
            raise
        return SaveResult(slot_name=slot_name, path=path,
                          bytes_written=len(blob), atomic=True)

    # ── load: total + refusing; returns LoadResult, never raises on bad data ─
    def load(self, slot_name, *, expected_format_version=None,
             expected_build_id=None, expected_scene_id=None,
             expected_policy_id=None):
        """Load a slot's opaque payload. Absent file -> "first_run" (nothing
        created). Any content/identity problem -> "refused" with named refusals.
        Returns LoadResult(payload=..., status="loaded", identities, hash) only
        when the envelope is well-formed AND every supplied expected identity
        matches the stored one."""
        try:
            path = _validate_slot_name(self.user_directory, slot_name)
        except SlotNameError as exc:
            return LoadResult(slot_name, "refused", refusals=(exc.refusal,))

        def refused(refusals):
            return LoadResult(slot_name, "refused", payload=b"",
                              refusals=tuple(refusals))

        try:
            raw = _read_bounded(path, self.max_envelope_bytes)
        except OSError as exc:
            return refused((Refusal("io_error",
                                    f"envelope could not be read: {exc}"),))
        if raw is None:                                  # nothing saved yet
            return LoadResult(slot_name, "first_run")

        try:
            fields = _parse_and_validate(raw)
        except EnvelopeError as exc:
            return refused((Refusal(exc.code, exc.detail),))

        refusals = []
        if expected_format_version is not None and \
                fields["format_version"] != expected_format_version:
            refusals.append(Refusal("format_version_mismatch",
                f"expected format_version {expected_format_version!r}, stored "
                f"{fields['format_version']!r}"))
        if expected_build_id is not None and fields["build_id"] != expected_build_id:
            refusals.append(Refusal("build_id_mismatch",
                f"expected build_id {expected_build_id!r}, stored "
                f"{fields['build_id']!r}"))
        if expected_scene_id is not None and fields["scene_id"] != expected_scene_id:
            refusals.append(Refusal("scene_id_mismatch",
                f"expected scene_id {expected_scene_id!r}, stored "
                f"{fields['scene_id']!r}"))
        if expected_policy_id is not None and fields["policy_id"] != expected_policy_id:
            refusals.append(Refusal("policy_id_mismatch",
                f"expected policy_id {expected_policy_id!r}, stored "
                f"{fields['policy_id']!r}"))
        if refusals:
            return refused(refusals)

        return LoadResult(
            slot_name=slot_name, status="loaded", payload=fields["payload"],
            format_version=fields["format_version"], build_id=fields["build_id"],
            scene_id=fields["scene_id"], policy_id=fields["policy_id"],
            payload_size=fields["payload_size"],
            payload_sha256=fields["payload_sha256"])

    # ── list: metadata only, bounded one-level scan, never raises on bad data ─
    def list(self):
        """Return SlotInfo for every stored slot (metadata only; no payloads).
        A corrupt/unreadable envelope is reported as status="unreadable", not
        raised. Returns [] when the user directory does not exist yet."""
        out = []
        try:
            entries = list(os.scandir(self.user_directory))
        except FileNotFoundError:
            return out
        except OSError as exc:
            raise SaveError(Refusal("io_error",
                                    f"user directory could not be scanned: {exc}"))
        for entry in entries:
            if not entry.name.endswith(SUFFIX) or not entry.is_file():
                continue
            info = self._slot_info(entry.path)
            out.append(info)
        out.sort(key=lambda s: s.slot_name)
        return out

    def _slot_info(self, path: str) -> SlotInfo:
        slot_name = os.path.basename(path)[: -len(SUFFIX)] or os.path.basename(path)
        try:
            raw = _read_bounded(path, self.max_envelope_bytes)
            if raw is None:
                return SlotInfo(slot_name, "unreadable", detail="disappeared")
            fields = _parse_and_validate(raw)
        except EnvelopeError as exc:
            return SlotInfo(slot_name, "unreadable", detail=exc.detail)
        except OSError as exc:
            return SlotInfo(slot_name, "unreadable", detail=f"io error: {exc}")
        return SlotInfo(
            slot_name=slot_name, status="ok",
            format_version=fields["format_version"], build_id=fields["build_id"],
            scene_id=fields["scene_id"], policy_id=fields["policy_id"],
            payload_size=fields["payload_size"],
            payload_sha256=fields["payload_sha256"])
