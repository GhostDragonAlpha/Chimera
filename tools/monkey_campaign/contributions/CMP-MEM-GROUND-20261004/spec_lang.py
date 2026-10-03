"""spec_lang.py -- the RESTRICTED EXPRESSION LANGUAGE of the executable
mathematical specification layer (mathspec lane wk-mathspec-core, phase 1).

LAW (Captain's implementation order, phase 1 item 2): evolution equations are
written in an EXPLICIT RESTRICTED EXPRESSION LANGUAGE, parsed into a VALIDATED
AST. Arbitrary source strings are NEVER executed: there is no eval(), exec()
or compile() anywhere in this module -- the only evaluator is a hand-written
tree walker over the closed AST node set below.

Closed AST node set (anything else is refused BY NAME at parse time):
  Num        -- a finite float literal
  Name       -- a declared identifier (resolved against an explicit scope)
  BinOp      -- + - * /            (exact Python float semantics)
  UnaryOp    -- unary - and +
  Call       -- whitelist: abs min max sqrt exp log  (fixed arity, checked)
  Compare    -- < <= > >= == !=    (two operands only; no chaining)
  BoolOp     -- and or             (two operands only)
  Not        -- unary not
  Const      -- true / false

Predicate expressions (Compare/BoolOp/Not/Const at the root) are used ONLY in
preconditions / invariants / refusal conditions. Numeric expressions
(evolution / exchange / transfer / ledger / conserved-quantity) must be
numeric-typed; the validator refuses a predicate in a numeric slot and vice
versa (E_EXPR_WRONG_EXPRESSION_CLASS).

Every refusal carries a NAMED code. Nothing is repaired, defaulted or
silently accepted.
"""
from __future__ import annotations

import math

# ---------- named refusal codes ---------------------------------------------------

E_TOKEN_UNRECOGNIZED = "expr_token_unrecognized"
E_TOKEN_UNTERMINATED_NUMBER = "expr_token_unterminated_number"
E_EXPR_EMPTY = "expr_empty"
E_EXPR_TRAILING_INPUT = "expr_trailing_input"
E_EXPR_UNEXPECTED_TOKEN = "expr_unexpected_token"
E_EXPR_UNSUPPORTED_SYNTAX = "expr_unsupported_syntax"
E_EXPR_UNKNOWN_NAME = "expr_unknown_name"
E_EXPR_NAME_NOT_IN_SCOPE = "expr_name_not_in_scope"
E_EXPR_UNKNOWN_FUNCTION = "expr_unknown_function"
E_EXPR_BAD_ARITY = "expr_bad_arity"
E_EXPR_WRONG_EXPRESSION_CLASS = "expr_wrong_expression_class"
E_EVAL_NONFINITE = "expr_eval_nonfinite"
E_EVAL_DIVISION_BY_ZERO = "expr_eval_division_by_zero"
E_EVAL_DOMAIN = "expr_eval_domain_error"
E_EVAL_TYPE = "expr_eval_type_error"

# The complete function whitelist. Anything else is refused by name.
FUNCTION_WHITELIST = {
    "abs": (1, 1),
    "min": (2, 2),
    "max": (2, 2),
    "sqrt": (1, 1),
    "exp": (1, 1),
    "log": (1, 1),
}

KEYWORD_CONSTANTS = {"true": True, "false": False}


class ExprRefusal(Exception):
    """A named refusal of the expression language. Never silenced."""

    def __init__(self, code: str, message: str, detail: dict | None = None):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.detail = dict(detail or {})


# ---------- tokens -----------------------------------------------------------------

_TWO_CHAR_OPS = ("<=", ">=", "==", "!=")
_ONE_CHAR_OPS = "+-*/()<>,"
_COMPARE_OPS = ("<", "<=", ">", ">=", "==", "!=")


def tokenize(text: str) -> list:
    tokens = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and text[i + 1].isdigit()):
            j = i
            seen_dot = False
            seen_e = False
            while j < n:
                d = text[j]
                if d.isdigit():
                    j += 1
                elif d == "." and not seen_dot and not seen_e:
                    seen_dot = True
                    j += 1
                elif d in "eE" and not seen_e and j > i:
                    seen_e = True
                    j += 1
                    if j < n and text[j] in "+-":
                        j += 1
                else:
                    break
            raw = text[i:j]
            try:
                value = float(raw)
            except ValueError:
                raise ExprRefusal(E_TOKEN_UNTERMINATED_NUMBER,
                                  f"malformed numeric literal {raw!r}",
                                  {"literal": raw, "offset": i})
            if not math.isfinite(value):
                raise ExprRefusal(E_TOKEN_UNTERMINATED_NUMBER,
                                  f"non-finite numeric literal {raw!r}",
                                  {"literal": raw, "offset": i})
            tokens.append(("num", value, i))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tokens.append(("name", text[i:j], i))
            i = j
            continue
        two = text[i:i + 2]
        if two in _TWO_CHAR_OPS:
            tokens.append(("op", two, i))
            i += 2
            continue
        if c in _ONE_CHAR_OPS:
            tokens.append(("op", c, i))
            i += 1
            continue
        raise ExprRefusal(E_TOKEN_UNRECOGNIZED,
                          f"character {c!r} is not part of the restricted "
                          f"expression language", {"offset": i, "char": c})
    return tokens


# ---------- AST nodes (a CLOSED dataclass set) ---------------------------------------

class Node:
    kind = "node"


class Num(Node):
    kind = "num"

    def __init__(self, value: float):
        self.value = float(value)


class Const(Node):
    kind = "const"

    def __init__(self, value: bool):
        self.value = bool(value)


class Name(Node):
    kind = "name"

    def __init__(self, ident: str):
        self.ident = ident


class BinOp(Node):
    kind = "binop"

    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right


class UnaryOp(Node):
    kind = "unaryop"

    def __init__(self, op: str, operand: Node):
        self.op = op
        self.operand = operand


class Call(Node):
    kind = "call"

    def __init__(self, func: str, args: list):
        self.func = func
        self.args = list(args)


class Compare(Node):
    kind = "compare"

    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right


class BoolOp(Node):
    kind = "boolop"

    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right


class Not(Node):
    kind = "not"

    def __init__(self, operand: Node):
        self.operand = operand


NUMERIC_KINDS = {"num", "name", "binop", "unaryop", "call"}
PREDICATE_KINDS = {"compare", "boolop", "not", "const"}


def expression_class(node: Node) -> str:
    """The declared class of an expression: 'numeric' or 'predicate'.
    A bare Name is undecided until scope resolution; it is classified by the
    validator against the declared role of the named quantity."""
    if node.kind in NUMERIC_KINDS:
        return "numeric"
    if node.kind in PREDICATE_KINDS:
        return "predicate"
    if node.kind == "name":
        return "name"
    raise ExprRefusal(E_EXPR_UNSUPPORTED_SYNTAX,
                      f"unknown AST node kind {node.kind!r}")


# ---------- recursive-descent parser (NO eval/exec/compile anywhere) ---------------

class _Parser:
    def __init__(self, text: str, tokens: list):
        self.text = text
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _next(self):
        tok = self._peek()
        if tok is None:
            raise ExprRefusal(E_EXPR_UNEXPECTED_TOKEN,
                              "unexpected end of expression", {
                                  "expr": self.text})
        self.pos += 1
        return tok

    def _expect_op(self, op: str):
        tok = self._next()
        if tok[0] != "op" or tok[1] != op:
            raise ExprRefusal(E_EXPR_UNEXPECTED_TOKEN,
                              f"expected {op!r}, found {tok[1]!r}", {
                                  "expr": self.text, "offset": tok[2]})

    # grammar: or_expr := and_expr ('or' and_expr)*
    #          and_expr := not_expr ('and' not_expr)*
    #          not_expr := 'not' not_expr | comparison
    #          comparison := additive (COMPOP additive)?     (no chaining)
    #          additive := term (('+'|'-') term)*
    #          term := unary (('*'|'/') unary)*
    #          unary := ('-'|'+') unary | primary
    #          primary := NUM | true | false | NAME | NAME '(' args ')'
    #                     | '(' or_expr ')'
    def parse(self) -> Node:
        if not self.tokens:
            raise ExprRefusal(E_EXPR_EMPTY, "empty expression",
                              {"expr": self.text})
        node = self._or_expr()
        tok = self._peek()
        if tok is not None:
            raise ExprRefusal(E_EXPR_TRAILING_INPUT,
                              f"unexpected trailing input at {tok[1]!r}", {
                                  "expr": self.text, "offset": tok[2]})
        return node

    def _or_expr(self) -> Node:
        node = self._and_expr()
        while self._at_name("or"):
            self._next()
            node = BoolOp("or", node, self._and_expr())
        return node

    def _and_expr(self) -> Node:
        node = self._not_expr()
        while self._at_name("and"):
            self._next()
            node = BoolOp("and", node, self._not_expr())
        return node

    def _not_expr(self) -> Node:
        if self._at_name("not"):
            self._next()
            return Not(self._not_expr())
        return self._comparison()

    def _comparison(self) -> Node:
        node = self._additive()
        tok = self._peek()
        if tok is not None and tok[0] == "op" and tok[1] in _COMPARE_OPS:
            self._next()
            rhs = self._additive()
            node = Compare(tok[1], node, rhs)
            nxt = self._peek()
            if nxt is not None and nxt[0] == "op" \
                    and nxt[1] in _COMPARE_OPS:
                raise ExprRefusal(
                    E_EXPR_UNSUPPORTED_SYNTAX,
                    "chained comparisons are outside the restricted "
                    "language; parenthesize one comparison", {
                        "expr": self.text, "offset": nxt[2]})
        return node

    def _additive(self) -> Node:
        node = self._term()
        while True:
            tok = self._peek()
            if tok is not None and tok[0] == "op" and tok[1] in "+-":
                self._next()
                node = BinOp(tok[1], node, self._term())
            else:
                return node

    def _term(self) -> Node:
        node = self._unary()
        while True:
            tok = self._peek()
            if tok is not None and tok[0] == "op" and tok[1] in "*/":
                self._next()
                node = BinOp(tok[1], node, self._unary())
            else:
                return node

    def _unary(self) -> Node:
        tok = self._peek()
        if tok is not None and tok[0] == "op" and tok[1] in "+-":
            self._next()
            operand = self._unary()
            return operand if tok[1] == "+" else UnaryOp("-", operand)
        return self._primary()

    def _primary(self) -> Node:
        tok = self._next()
        if tok[0] == "num":
            return Num(tok[1])
        if tok[0] == "name":
            word = tok[1]
            if word in KEYWORD_CONSTANTS:
                return Const(KEYWORD_CONSTANTS[word])
            nxt = self._peek()
            if nxt is not None and nxt[0] == "op" and nxt[1] == "(":
                self._next()
                args = []
                if not (self._peek() and self._peek()[0] == "op"
                        and self._peek()[1] == ")"):
                    args.append(self._or_expr())
                    while self._peek() and self._peek()[0] == "op" \
                            and self._peek()[1] == ",":
                        self._next()
                        args.append(self._or_expr())
                self._expect_op(")")
                if word not in FUNCTION_WHITELIST:
                    raise ExprRefusal(
                        E_EXPR_UNKNOWN_FUNCTION,
                        f"function {word!r} is outside the whitelist "
                        f"{sorted(FUNCTION_WHITELIST)}", {
                            "expr": self.text, "function": word,
                            "whitelist": sorted(FUNCTION_WHITELIST)})
                lo, hi = FUNCTION_WHITELIST[word]
                if not (lo <= len(args) <= hi):
                    raise ExprRefusal(
                        E_EXPR_BAD_ARITY,
                        f"{word} takes {lo}..{hi} argument(s), got "
                        f"{len(args)}", {"expr": self.text,
                                         "function": word,
                                         "arity": len(args)})
                return Call(word, args)
            return Name(word)
        if tok[0] == "op" and tok[1] == "(":
            node = self._or_expr()
            self._expect_op(")")
            return node
        raise ExprRefusal(E_EXPR_UNEXPECTED_TOKEN,
                          f"unexpected token {tok[1]!r}", {
                              "expr": self.text, "offset": tok[2]})

    def _at_name(self, word: str) -> bool:
        tok = self._peek()
        return (tok is not None and tok[0] == "name" and tok[1] == word
                and word not in FUNCTION_WHITELIST)


def parse(text: str) -> Node:
    """Parse one restricted-language expression into a validated AST.
    Raises ExprRefusal with a named code on ANY unsupported construct."""
    if not isinstance(text, str):
        raise ExprRefusal(E_EXPR_UNSUPPORTED_SYNTAX,
                          "an expression must be a string", {"type":
                                                             type(text).__name__})
    return _Parser(text, tokenize(text)).parse()


# ---------- tree-walking evaluator (the ONLY evaluator) ------------------------------

def evaluate(node: Node, scope: dict) -> object:
    """Evaluate a validated AST against an explicit scope dict
    (name -> value). Unknown names are refused by name; they are never
    silently None. All numeric arithmetic is Python float arithmetic on the
    AST nodes themselves."""
    kind = node.kind
    if kind == "num":
        return node.value
    if kind == "const":
        return node.value
    if kind == "name":
        if node.ident not in scope:
            raise ExprRefusal(E_EXPR_NAME_NOT_IN_SCOPE,
                              f"name {node.ident!r} is not in the "
                              f"evaluation scope", {
                                  "name": node.ident,
                                  "scope": sorted(str(k) for k in scope)})
        return scope[node.ident]
    if kind == "unaryop":
        value = evaluate(node.operand, scope)
        _require_number(value, node)
        return -value if node.op == "-" else +value
    if kind == "binop":
        left = evaluate(node.left, scope)
        right = evaluate(node.right, scope)
        _require_number(left, node)
        _require_number(right, node)
        if node.op == "+":
            out = left + right
        elif node.op == "-":
            out = left - right
        elif node.op == "*":
            out = left * right
        elif node.op == "/":
            if right == 0.0:
                raise ExprRefusal(E_EVAL_DIVISION_BY_ZERO,
                                  "division by zero at evaluation", {})
            out = left / right
        else:
            raise ExprRefusal(E_EXPR_UNSUPPORTED_SYNTAX,
                              f"operator {node.op!r} not in the closed set",
                              {"op": node.op})
        if not math.isfinite(out):
            raise ExprRefusal(E_EVAL_NONFINITE,
                              "expression evaluated to a non-finite value",
                              {"op": node.op})
        return out
    if kind == "call":
        args = [evaluate(a, scope) for a in node.args]
        for a in args:
            _require_number(a, node)
        fn = node.func
        if fn == "abs":
            return abs(args[0])
        if fn == "min":
            return min(args[0], args[1])
        if fn == "max":
            return max(args[0], args[1])
        try:
            if fn == "sqrt":
                if args[0] < 0.0:
                    raise ExprRefusal(E_EVAL_DOMAIN,
                                      "sqrt of a negative value", {})
                return math.sqrt(args[0])
            if fn == "exp":
                return math.exp(args[0])
            if fn == "log":
                if args[0] <= 0.0:
                    raise ExprRefusal(E_EVAL_DOMAIN,
                                      "log of a non-positive value", {})
                return math.log(args[0])
        except OverflowError:
            raise ExprRefusal(E_EVAL_NONFINITE,
                              f"{fn} overflowed to a non-finite value", {})
        raise ExprRefusal(E_EXPR_UNKNOWN_FUNCTION,
                          f"function {fn!r} outside the whitelist", {})
    if kind == "compare":
        left = evaluate(node.left, scope)
        right = evaluate(node.right, scope)
        if isinstance(left, bool) or isinstance(right, bool):
            if node.op not in ("==", "!="):
                raise ExprRefusal(E_EVAL_TYPE,
                                  "ordering comparison over a boolean", {})
        elif not (isinstance(left, (int, float))
                  and isinstance(right, (int, float))):
            raise ExprRefusal(E_EVAL_TYPE,
                              "comparison over a non-numeric operand", {})
        return {"<": left < right, "<=": left <= right, ">": left > right,
                ">=": left >= right, "==": left == right,
                "!=": left != right}[node.op]
    if kind == "boolop":
        left = evaluate(node.left, scope)
        right = evaluate(node.right, scope)
        _require_bool(left, node)
        _require_bool(right, node)
        return (left and right) if node.op == "and" else (left or right)
    if kind == "not":
        value = evaluate(node.operand, scope)
        _require_bool(value, node)
        return not value
    raise ExprRefusal(E_EXPR_UNSUPPORTED_SYNTAX,
                      f"unknown AST node kind {kind!r}", {"kind": kind})


def _require_number(value, node):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExprRefusal(E_EVAL_TYPE,
                          f"numeric operator applied to a non-numeric "
                          f"value ({type(value).__name__})", {
                              "node": node.kind})
    if not math.isfinite(float(value)):
        raise ExprRefusal(E_EVAL_NONFINITE, "non-finite operand", {})


def _require_bool(value, node):
    if not isinstance(value, bool):
        raise ExprRefusal(E_EVAL_TYPE,
                          f"boolean operator applied to a non-boolean "
                          f"value ({type(value).__name__})", {
                              "node": node.kind})


# ---------- scope-name walk ----------------------------------------------------------

def free_names(node: Node, out: set | None = None) -> set:
    """Every Name in the AST (functions and keywords excluded). The validator
    checks this set against the DECLARED scope of each expression slot."""
    out = set() if out is None else out
    kind = node.kind
    if kind == "name":
        out.add(node.ident)
    elif kind == "unaryop":
        free_names(node.operand, out)
    elif kind == "not":
        free_names(node.operand, out)
    elif kind == "binop":
        free_names(node.left, out)
        free_names(node.right, out)
    elif kind == "compare":
        free_names(node.left, out)
        free_names(node.right, out)
    elif kind == "boolop":
        free_names(node.left, out)
        free_names(node.right, out)
    elif kind == "call":
        for a in node.args:
            free_names(a, out)
    return out
