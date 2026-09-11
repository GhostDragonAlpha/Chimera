"""gov03_reference_model.py -- independent, stdlib-only reference model of the
INTENDED law/decision record contract (catalogue card GOV-03, "Law and decision
records").

The card's contract, modeled in full (this is the INTENDED contract, not any
deployed subset):

  STATEMENT   Energy, force, flux, boundary, domain and parameter records --
              a registry of LAW records typed by those six kinds.
  PREDICTION  Each admitted law names its domain, independent oracle and
              limitations -- required admission fields, exposed on every
              stored record.
  FALSIFIER   A physical claim lacks a falsifier or a constant lacks an
              origin -- the two refusal paths every admission must pass.
  MATHEMATICS Dimensional analysis (an exponent algebra over {M, L, T, Theta},
              no eval/exec), contracts (named refusals, immutable decisions),
              versioned assumptions (append-only history, version bumps).

Design boundaries fixed in PREREG.md before implementation:
  * stdlib only; no eval, no exec; the formula parser is a small
    recursive-descent parser over declared symbols with integer powers.
  * every refusal is NAMED (`missing_falsifier`, `missing_constant_origin`,
    ...); a refused operation leaves the registry byte-identical.
  * decisions cite admitted ACTIVE laws only; superseded laws refuse.
  * the known live-path deviation (owner_instance dropped by the interceptor
    claim; PR #80 in review) is a DEPLOYED finding recorded in RESULT.md --
    deliberately NOT modeled here; this model is the intended contract.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

LAW_KINDS = ("energy", "force", "flux", "boundary", "domain", "parameter")
OUTCOMES = ("ADOPT", "REJECT", "REVISE")
BASE_DIMS = ("M", "L", "T", "Theta")

_DIM_TOKEN = re.compile(r"\s*(\(|\)|\*\*|\^|\*|-?[0-9]+|[A-Z][A-Za-z]*)")


# ------------------------------------------------------------- dimensions

def dim_parse(text: str) -> dict:
    """Parse a dimension string like 'M L^2 T^-2' or '1' (dimensionless)."""
    dims = {b: 0 for b in BASE_DIMS}
    seen_any = False
    tokens = _tokenize_dims(text)
    pos = 0
    while pos < len(tokens):
        tok = tokens[pos]
        if tok == "1" and not seen_any and pos == len(tokens) - 1:
            return dims  # explicit dimensionless
        base = _dim_symbol(tok)
        if base is None:
            raise ValueError(f"bad dimension token {tok!r} in {text!r}")
        exp = 1
        if pos + 1 < len(tokens) and tokens[pos + 1] == "**":
            if pos + 2 >= len(tokens) or not re.fullmatch(r"-?[0-9]+", tokens[pos + 2]):
                raise ValueError(f"non-integer power in {text!r}")
            exp = int(tokens[pos + 2])
            pos += 2
        dims[base] = dims.get(base, 0) + exp
        seen_any = True
        pos += 1
    if not seen_any:
        raise ValueError(f"empty dimension in {text!r}")
    return dims


def _tokenize_dims(text: str) -> list:
    out, i = [], 0
    while i < len(text):
        m = _DIM_TOKEN.match(text, i)
        if not m:
            if text[i].isspace():
                i += 1
                continue
            raise ValueError(f"bad dimension character {text[i]!r} in {text!r}")
        tok = m.group(1)
        out.append("**" if tok == "^" else tok)   # physics caret -> power op
        i = m.end()
    return out


def _dim_symbol(tok: str):
    return tok if tok in BASE_DIMS else None


def dim_mul(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) + b.get(k, 0) for k in set(a) | set(b)}


def dim_div(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) - b.get(k, 0) for k in set(a) | set(b)}


def dim_pow(a: dict, n: int) -> dict:
    return {k: v * n for k, v in a.items()}


def dim_equal(a: dict, b: dict) -> bool:
    keys = set(a) | set(b)
    return all(a.get(k, 0) == b.get(k, 0) for k in keys)


def dim_render(d: dict) -> str:
    parts = []
    for b in BASE_DIMS:
        e = d.get(b, 0)
        if e:
            parts.append(b if e == 1 else f"{b}^{e}")
    return " ".join(parts) if parts else "1"


_FORMULA_TOKEN = re.compile(r"\s*(\(|\)|\*\*|\*|/|\+|-|-?[0-9]+(?:\.[0-9]+)?"
                            r"|[A-Za-z_][A-Za-z_0-9]*)")


def _tokenize_formula(text: str, symbols: dict) -> list:
    out, i = [], 0
    while i < len(text):
        m = _FORMULA_TOKEN.match(text, i)
        if not m:
            if text[i].isspace():
                i += 1
                continue
            raise ValueError(f"bad formula character {text[i]!r} in {text!r}")
        tok = m.group(1)
        if tok not in ("(", ")", "*", "/", "**", "+", "-") \
                and tok not in symbols \
                and not re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", tok):
            raise ValueError(f"formula uses undeclared symbol {tok!r}")
        out.append(tok)
        i = m.end()
    return out


class _FormulaParser:
    """add := mul (('+' | '-') mul)*        -- same-dimension constraint
    mul  := pow (('*' | '/') pow)*          -- mul/div compose exponents
    pow  := factor ('**' int)?
    factor := number | symbol | '(' add ')'   Integer powers only.

    Dimensional analysis: '*' multiplies, '/' divides, and '+'/'-' are only
    legal between operands of the SAME dimension (else DimensionMismatch)."""

    def __init__(self, tokens, symbols):
        self.toks, self.pos, self.symbols = tokens, 0, symbols

    def peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def take(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self) -> dict:
        d = self.add()
        if self.peek() is not None:
            raise ValueError(f"trailing tokens in formula: {self.toks[self.pos:]}")
        return d

    def add(self) -> dict:
        d = self.mul()
        while self.peek() in ("+", "-"):
            op = self.take()
            rhs = self.mul()
            if not dim_equal(d, rhs):
                raise DimensionMismatch(
                    f"operands of {op} have different dimensions: "
                    f"{dim_render(d)} vs {dim_render(rhs)}")
        return d

    def mul(self) -> dict:
        d = self.pow()
        while self.peek() in ("*", "/"):
            op = self.take()
            rhs = self.pow()
            d = dim_mul(d, rhs) if op == "*" else dim_div(d, rhs)
        return d

    def pow(self) -> dict:
        d = self.factor()
        if self.peek() == "**":
            self.take()
            n = self.take()
            if n is None or not re.fullmatch(r"-?[0-9]+", n):
                raise ValueError("only integer powers are allowed in a formula")
            d = dim_pow(d, int(n))
        return d

    def factor(self) -> dict:
        tok = self.take()
        if tok == "(":
            d = self.add()
            if self.take() != ")":
                raise ValueError("unbalanced parenthesis in formula")
            return d
        if tok is None or tok in (")", "*", "/", "**", "+", "-"):
            raise ValueError(f"unexpected formula token {tok!r}")
        if re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", tok):
            return {b: 0 for b in BASE_DIMS}    # a numeric literal: dimensionless
        return dim_parse(self.symbols[tok])


def check_formula(formula: str, input_dims: dict, declared_out: str) -> dict:
    """Compose the formula's dimension from the declared input dimensions and
    compare with the declared output dimension. Returns the composed dict;
    raises ValueError on parse errors (the caller maps that to
    dimension_mismatch semantics after distinguishing name errors)."""
    symbols = {}
    for sym, dim_text in input_dims.items():
        symbols[sym] = dim_text
        dim_parse(dim_text)  # validate each input dimension text eagerly
    out = dim_parse(declared_out)
    parser = _FormulaParser(_tokenize_formula(formula, symbols), symbols)
    composed = parser.parse()
    if not dim_equal(composed, out):
        raise DimensionMismatch(
            f"formula composes {dim_render(composed)}, declared output is "
            f"{dim_render(out)}")
    return composed


class DimensionMismatch(ValueError):
    pass


# ------------------------------------------------------------- the registry

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LawRegistry:
    """LAW + DECISION records under the card's intended contract."""

    def __init__(self):
        self.laws = {}
        self.decisions = {}
        self._next_decision = 1

    # -- admission --------------------------------------------------------
    def admit_law(self, name, kind, statement, falsifier, domain, oracle,
                  limitations, constants, input_dims, formula, output_dim,
                  assumptions=()):
        rec = dict(name=name, kind=kind, statement=statement or "",
                   falsifier=falsifier or "", domain=domain or "",
                   oracle=oracle or "", limitations=limitations or "",
                   constants=[dict(c) for c in (constants or [])],
                   input_dims=dict(input_dims or {}), formula=formula or "",
                   output_dim=output_dim or "",
                   assumptions=list(assumptions) or ["v1: initial statement"],
                   version=1, status="ACTIVE", superseded_by=None,
                   created_at=_now())
        refused = self._admission_gates(rec)
        if refused:
            return {"ok": False, "error": refused, "law": None}
        self.laws[name] = rec
        return {"ok": True, "error": None, "law": self.laws[name]}

    def _admission_gates(self, rec):
        if not rec["falsifier"].strip():
            return ("REFUSED (card falsifier): a physical claim lacks a "
                    "falsifier -- missing_falsifier")
        if not rec["domain"].strip():
            return "REFUSED: missing_domain"
        if not rec["oracle"].strip():
            return "REFUSED: missing_oracle"
        if rec["oracle"] == rec["name"] or rec["oracle"] == rec["statement"]:
            return ("REFUSED: a law is not its own independent oracle -- "
                    "oracle_not_independent")
        if not rec["limitations"].strip():
            return "REFUSED: missing_limitations"
        if rec["kind"] not in LAW_KINDS:
            return f"REFUSED: bad_kind (must be one of {LAW_KINDS})"
        if rec["name"] in self.laws:
            return "REFUSED: duplicate_law"
        for c in rec["constants"]:
            if "origin" not in c or not str(c.get("origin", "")).strip():
                return (f"REFUSED (card falsifier): constant {c.get('name')!r} "
                        f"lacks an origin -- missing_constant_origin")
            if "value" not in c or "name" not in c:
                return (f"REFUSED: constant {c.get('name')!r} needs a name and "
                        f"a value -- malformed_constant")
        try:
            check_formula(rec["formula"], rec["input_dims"], rec["output_dim"])
        except DimensionMismatch as exc:
            return f"REFUSED: dimension_mismatch ({exc})"
        except ValueError as exc:
            return f"REFUSED: dimension_mismatch (malformed: {exc})"
        return None

    # -- versioned assumptions / lifecycle ---------------------------------
    def amend_law(self, name, assumption):
        rec = self.laws.get(name)
        if rec is None:
            return {"ok": False, "error": "REFUSED: law_not_admitted"}
        if not assumption or not assumption.strip():
            return {"ok": False, "error": "REFUSED: empty_assumption"}
        rec["assumptions"].append(f"v{rec['version'] + 1}: {assumption}")
        rec["version"] += 1
        return {"ok": True, "error": None, "law": rec}

    def supersede_law(self, new_spec, old_name):
        old = self.laws.get(old_name)
        if old is None:
            return {"ok": False, "error": "REFUSED: law_not_admitted"}
        if old["status"] != "ACTIVE":
            return {"ok": False, "error": "REFUSED: law_superseded"}
        res = self.admit_law(**new_spec)
        if not res["ok"]:
            return res
        old["status"] = "SUPERSEDED"
        old["superseded_by"] = new_spec["name"]
        return {"ok": True, "error": None, "law": res["law"], "old": old}

    # -- decision records ---------------------------------------------------
    def decide(self, law_name, outcome, evidence, rationale=""):
        if outcome not in OUTCOMES:
            return {"ok": False,
                    "error": f"REFUSED: bad_outcome (must be one of {OUTCOMES})"}
        if not evidence or not evidence.strip():
            return {"ok": False,
                    "error": "REFUSED: a decision needs an EVIDENCE pointer "
                             "-- missing_evidence"}
        rec = self.laws.get(law_name)
        if rec is None:
            return {"ok": False, "error": "REFUSED: law_not_admitted"}
        if rec["status"] != "ACTIVE":
            return {"ok": False, "error": "REFUSED: law_superseded"}
        n = self._next_decision
        self._next_decision += 1
        self.decisions[str(n)] = dict(number=n, law=law_name, outcome=outcome,
                                      evidence=evidence, rationale=rationale,
                                      law_version_at_decision=rec["version"],
                                      created_at=_now())
        return {"ok": True, "error": None, "decision": self.decisions[str(n)]}

    # -- readout (the card prediction lives here) ----------------------------
    def law_named_parts(self, name):
        """The five parts the card prediction requires every admitted law to
        name: domain, independent oracle, limitations, falsifier,
        constants-with-origins. Returns (parts_dict, missing_list)."""
        rec = self.laws.get(name)
        if rec is None:
            return {}, ["law_not_admitted"]
        parts = {
            "domain": rec["domain"],
            "oracle": rec["oracle"],
            "limitations": rec["limitations"],
            "falsifier": rec["falsifier"],
            "constants_with_origins": [
                (c["name"], c["origin"]) for c in rec["constants"]],
        }
        missing = [k for k, v in parts.items() if not v]
        return parts, missing
