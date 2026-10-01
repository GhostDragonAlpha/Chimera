"""chimpl-v1 — the constraint-record expression language.

A small, total, side-effect-free expression language over typed quantities.
Its ONLY job is to carry a law's declarative predicate/equation inside a
record so that reads/writes can be DERIVED (amendment-1 item 2) and the
predicate can be COMPILED and evaluated bit-exactly against the shipped C++.

GRAMMAR (EBNF, whitespace-insensitive; `now:` marks a same-tick read, a bare
quantity name is a delayed (previous-tick / tick-start) read — the explicit
delayed state of amendment-1 item 4):

    expr    := 'if' expr 'then' expr 'else' expr | orexpr ;
    orexpr  := andexpr ( 'or' andexpr )* ;
    andexpr := notexpr ( 'and' notexpr )* ;
    notexpr := 'not' notexpr | cmpexpr ;
    cmpexpr := addexpr ( ( '==' | '!=' | '<=' | '>=' | '<' | '>' ) addexpr )? ;
    addexpr := mulexpr ( ( '+' | '-' ) mulexpr )* ;
    mulexpr := unary ( ( '*' | '/' ) unary )* ;
    unary   := '-' unary | primary ;
    primary := NUMBER | 'true' | 'false' | 'now' ':' qname | qname
             | IDENT '(' args ')' | '(' expr ')' ;
    qname   := seg ( '.' seg )* ;
    seg     := IDENT | '{' IDENT '}' ;          (* '{leg}' = parameter hole *)
    args    := expr ( ',' expr )* ;

Semantics:
  * float64 arithmetic and comparisons (IEEE-754, C++ `/fp:precise` order —
    the expression must mirror the source's operation order bit-for-bit);
  * comparisons/and/or/not yield booleans; `if` is total (all branches'
    reads count statically, conservative);
  * builtins: min, max, abs, ceil, floor (each mirrors the C++ std:: form);
  * `control.step` is a builtin integer quantity (the decision step index);
  * bare reads are DELAYED (value at the start of the tick), `now:` reads are
    same-tick values of earlier writers in the fragment's dependency order.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# ── tokenizer ──────────────────────────────────────────────────────────────
_OPS = ('==', '!=', '<=', '>=', '<', '>', '+', '-', '*', '/', '(', ')', ':', ',', '.', '{', '}')
_KEYWORDS = {'if', 'then', 'else', 'and', 'or', 'not', 'now', 'true', 'false'}


class Token:
    __slots__ = ('kind', 'text', 'pos')

    def __init__(self, kind, text, pos):
        self.kind, self.text, self.pos = kind, text, pos

    def __repr__(self):
        return f'{self.kind}({self.text})@{self.pos}'


def tokenize(src: str) -> list[Token]:
    toks, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or (c == '.' and i + 1 < n and src[i + 1].isdigit()):
            j = i
            while j < n and (src[j].isdigit() or src[j] in '.eE' or
                             (src[j] in '+-' and j > i and src[j - 1] in 'eE')):
                j += 1
            toks.append(Token('num', src[i:j], i))
            i = j
            continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (src[j].isalnum() or src[j] == '_'):
                j += 1
            text = src[i:j]
            toks.append(Token(text if text in _KEYWORDS else 'ident', text, i))
            i = j
            continue
        matched = False
        for op in _OPS:
            if src.startswith(op, i):
                toks.append(Token(op, op, i))
                i += len(op)
                matched = True
                break
        if not matched:
            raise SyntaxError(f'chimpl: bad character {c!r} at {i} in {src!r}')
    toks.append(Token('eof', '', n))
    return toks


# ── AST ────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Num:
    value: float


@dataclass(frozen=True)
class _BoolLit:
    value: bool


@dataclass(frozen=True)
class Qty:      # a bare (delayed) quantity read
    name: str   # concrete dotted name after parameter expansion


@dataclass(frozen=True)
class NowQty:  # a same-tick quantity read
    name: str


@dataclass(frozen=True)
class Call:
    fn: str
    args: tuple


@dataclass(frozen=True)
class Un:
    op: str
    a: object


@dataclass(frozen=True)
class Bin:
    op: str
    a: object
    b: object


@dataclass(frozen=True)
class If:
    cond: object
    then: object
    other: object


class _Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0

    def peek(self):
        return self.toks[self.i]

    def take(self, kind=None):
        t = self.toks[self.i]
        if kind is not None and t.kind != kind:
            raise SyntaxError(f'chimpl: expected {kind}, got {t.kind}({t.text}) at {t.pos}')
        self.i += 1
        return t

    def parse(self):
        e = self.expr()
        self.take('eof')
        return e

    def expr(self):
        if self.peek().kind == 'if':
            self.take('if')
            cond = self.expr()
            self.take('then')
            a = self.expr()
            self.take('else')
            b = self.expr()
            return If(cond, a, b)
        return self.or_()

    def or_(self):
        a = self.and_()
        while self.peek().kind == 'or':
            self.take('or')
            a = Bin('or', a, self.and_())
        return a

    def and_(self):
        a = self.not_()
        while self.peek().kind == 'and':
            self.take('and')
            a = Bin('and', a, self.not_())
        return a

    def not_(self):
        if self.peek().kind == 'not':
            self.take('not')
            return Un('not', self.not_())
        return self.cmp()

    def cmp(self):
        a = self.add()
        if self.peek().kind in ('==', '!=', '<=', '>=', '<', '>'):
            op = self.take().kind
            return Bin(op, a, self.add())
        return a

    def add(self):
        a = self.mul()
        while self.peek().kind in ('+', '-'):
            op = self.take().kind
            a = Bin(op, a, self.mul())
        return a

    def mul(self):
        a = self.unary()
        while self.peek().kind in ('*', '/'):
            op = self.take().kind
            a = Bin(op, a, self.unary())
        return a

    def unary(self):
        if self.peek().kind == '-':
            self.take('-')
            return Un('neg', self.unary())
        return self.primary()

    def primary(self):
        t = self.peek()
        if t.kind == 'num':
            self.take('num')
            return Num(float(t.text))
        if t.kind == 'true':
            self.take('true')
            return _BoolLit(True)
        if t.kind == 'false':
            self.take('false')
            return _BoolLit(False)
        if t.kind == '(':
            self.take('(')
            e = self.expr()
            self.take(')')
            return e
        if t.kind == 'now':
            self.take('now')
            self.take(':')
            return NowQty(self.qname())
        if t.kind == 'ident':
            name = t.text
            self.take('ident')
            if self.peek().kind == '(':
                self.take('(')
                args = []
                if self.peek().kind != ')':
                    args.append(self.expr())
                    while self.peek().kind == ',':
                        self.take(',')
                        args.append(self.expr())
                self.take(')')
                return Call(name, tuple(args))
            segs = [name]
            while self.peek().kind == '.':
                self.take('.')
                segs.append(self.seg())
            return Qty('.'.join(segs))
        raise SyntaxError(f'chimpl: unexpected {t.kind}({t.text}) at {t.pos}')

    def qname(self):
        segs = [self.seg()]
        while self.peek().kind == '.':
            self.take('.')
            segs.append(self.seg())
        return '.'.join(segs)

    def seg(self):
        t = self.peek()
        if t.kind == 'ident':
            self.take('ident')
            return t.text
        if t.kind == '{':
            self.take('{')
            name = self.take('ident').text
            self.take('}')
            return '{' + name + '}'
        raise SyntaxError(f'chimpl: bad name segment {t.kind}({t.text}) at {t.pos}')


def parse(src: str):
    """Parse a concrete (parameter-expanded) chimpl expression."""
    return _Parser(tokenize(src)).parse()


# ── static reads ───────────────────────────────────────────────────────────
def reads(ast) -> tuple[set, set]:
    """Return (delayed_reads, same_tick_reads) as name sets, conservatively
    (every branch of an `if` counts)."""
    delayed, same = set(), set()

    def walk(e):
        if isinstance(e, (Num, _BoolLit)):
            return
        if isinstance(e, Qty):
            delayed.add(e.name)
            return
        if isinstance(e, NowQty):
            same.add(e.name)
            return
        if isinstance(e, Call):
            for a in e.args:
                walk(a)
            return
        if isinstance(e, Un):
            walk(e.a)
            return
        if isinstance(e, Bin):
            walk(e.a)
            walk(e.b)
            return
        if isinstance(e, If):
            walk(e.cond)
            walk(e.then)
            walk(e.other)
            return
        raise TypeError(f'chimpl: unknown AST node {e!r}')

    walk(ast)
    return delayed, same


# ── evaluation (bit-exact float64 semantics) ───────────────────────────────
def _need_bool(v, ctx):
    if not isinstance(v, bool):
        raise TypeError(f'chimpl: boolean operand required in {ctx}, got {v!r}')
    return v


def _need_num(v, ctx):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f'chimpl: numeric operand required in {ctx}, got {v!r}')
    return float(v)


def evaluate(ast, delayed: dict, same: dict, constants: dict) -> object:
    """Evaluate with delayed/same-tick environments and named constants.
    Arithmetic is float64 (Python floats); booleans stay Python bools."""
    def ev(e):
        if isinstance(e, Num):
            return e.value
        if isinstance(e, _BoolLit):
            return e.value
        if isinstance(e, Qty):
            if e.name in delayed:
                return delayed[e.name]
            if e.name in constants:
                return constants[e.name]
            raise NameError(f'chimpl: unbound delayed quantity {e.name!r}')
        if isinstance(e, NowQty):
            if e.name in same:
                return same[e.name]
            raise NameError(f'chimpl: unbound same-tick quantity {e.name!r} '
                            f'(same-tick reads must follow the writer in the fragment order)')
        if isinstance(e, Call):
            args = [ev(a) for a in e.args]
            fn = e.fn
            if fn == 'min':
                return min(_need_num(a, 'min') for a in args)
            if fn == 'max':
                return max(_need_num(a, 'max') for a in args)
            if fn == 'abs':
                return abs(_need_num(args[0], 'abs'))
            if fn == 'ceil':
                return float(math.ceil(_need_num(args[0], 'ceil')))
            if fn == 'floor':
                return float(math.floor(_need_num(args[0], 'floor')))
            raise NameError(f'chimpl: unknown builtin {fn!r}')
        if isinstance(e, Un):
            if e.op == 'not':
                return not _need_bool(ev(e.a), 'not')
            if e.op == 'neg':
                return -_need_num(ev(e.a), 'neg')
            raise TypeError(f'chimpl: unknown unary {e.op!r}')
        if isinstance(e, Bin):
            if e.op == 'and':
                return _need_bool(ev(e.a), 'and') and _need_bool(ev(e.b), 'and')
            if e.op == 'or':
                return _need_bool(ev(e.a), 'or') or _need_bool(ev(e.b), 'or')
            a, b = ev(e.a), ev(e.b)
            if e.op in ('==', '!='):
                eq = a == b
                return eq if e.op == '==' else not eq
            a, b = _need_num(a, e.op), _need_num(b, e.op)
            if e.op == '<':
                return a < b
            if e.op == '>':
                return a > b
            if e.op == '<=':
                return a <= b
            if e.op == '>=':
                return a >= b
            if e.op == '+':
                return a + b
            if e.op == '-':
                return a - b
            if e.op == '*':
                return a * b
            if e.op == '/':
                return a / b
            raise TypeError(f'chimpl: unknown binary {e.op!r}')
        if isinstance(e, If):
            return ev(e.then) if _need_bool(ev(e.cond), 'if') else ev(e.other)
        raise TypeError(f'chimpl: unknown AST node {e!r}')

    return ev(ast)
