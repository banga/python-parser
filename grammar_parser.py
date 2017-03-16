import enum
import string
from collections import deque
from parser import Grammar, Parser, Rule, Symbol
from typing import List


class TokenType(enum.Enum):
    STRING = 1
    IDENTIFIER = 2
    OPERATOR = 3
    NEWLINE = 4
    ENDMARKER = 5


class Token(object):
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Token(%r, %s)" % (self.value, self.type)


def tokenize(input):
    idx = 0
    end = len(input)
    id_chars = set(string.ascii_letters + string.digits + "_")
    op_chars = set("()[]|*+:")
    nesting_level = 0

    while idx < end:
        c = input[idx]
        if c == "#":
            while input[idx] != "\n" and idx < end:
                idx += 1
            if input[idx] == "\n":
                idx += 1
        elif c == "'" or c == "\"":
            idx2 = idx + 1
            while idx2 < end and input[idx2] != c:
                idx2 += 1
            yield Token(input[idx + 1:idx2], TokenType.STRING)
            idx = idx2 + 1
        elif c == " ":
            idx += 1
            continue
        elif c in id_chars:
            idx2 = idx + 1
            while idx2 < end and input[idx2] in id_chars:
                idx2 += 1
            yield Token(input[idx:idx2], TokenType.IDENTIFIER)
            idx = idx2
        elif c in op_chars:
            if c in "([":
                nesting_level += 1
            elif c in ")]":
                nesting_level -= 1
            yield Token(c, TokenType.OPERATOR)
            idx += 1
        elif c == "\n":
            if nesting_level == 0:
                yield Token(c, TokenType.NEWLINE)
            idx += 1
        else:
            assert False, "Unknown character %s(%d)" % (c, idx)

    yield Token("", TokenType.ENDMARKER)


class GrammarParser(object):
    def __init__(self, terminal_cls):
        self.rules = []
        self.tokens = []
        self.terminal_cls = terminal_cls

    def __str__(self):
        lines = []
        for rule in self.rules:
            s = str(rule.symbol.token)
            s += " -> "
            for symbol in rule.expansion:
                s += str(symbol.token) + " "
            lines.append(s)
        return "\n".join(sorted(lines))

    def add_rule(self, symbol, expansion):
        assert isinstance(symbol, Symbol)
        for s in expansion:
            assert isinstance(s, Symbol)
        self.rules.append(Rule(symbol, expansion))
        # print("Parsed: %s -> %s" % (symbol, expansion))

    def _create_internal_symbol(self):
        self._internal_symbol_counter += 1
        return Symbol(
            "__INTERNAL__%d" % self._internal_symbol_counter, False)

    def parse(self, input):
        self.tokens = tokenize(input)
        self.token = next(self.tokens)
        self._internal_symbol_counter = 0
        self.start_symbol = None
        while self.token.type != TokenType.ENDMARKER:
            self.parse_rule()
        return Grammar(self.rules, self.start_symbol)

    def parse_rule(self):
        while self.token.type == TokenType.NEWLINE:
            self.consume()
        token = self.expect(TokenType.IDENTIFIER)
        lhs = Symbol(token.value, False)
        self.expect(TokenType.OPERATOR, ":")
        self.parse_rhs(lhs)
        self.expect(TokenType.NEWLINE)

        if self.start_symbol is None:
            self.start_symbol = lhs

    def parse_rhs(self, lhs: Symbol) -> None:
        # RHS: ALT ('|' ALT)*
        self.parse_alt(lhs)
        while self.token.type == TokenType.OPERATOR and self.token.value == "|":
            self.consume()
            self.parse_alt(lhs)

    def parse_alt(self, lhs: Symbol) -> List[Symbol]:
        # ALT: ITEM+
        items = []
        items.extend(self.parse_item())
        while ((self.token.type == TokenType.OPERATOR and
                self.token.value in ("[", "(")) or
                self.token.type in (TokenType.IDENTIFIER, TokenType.STRING)):
            items.extend(self.parse_item())
        self.add_rule(lhs, items)
        return items

    def parse_item(self) -> List[Symbol]:
        # ITEM: '[' RHS ']' | ATOM ['+' | '*']
        if self.token.type == TokenType.OPERATOR and self.token.value == "[":
            self.consume()
            new_symbol = self._create_internal_symbol()
            self.parse_rhs(new_symbol)
            self.add_rule(new_symbol, [])
            self.expect(TokenType.OPERATOR, "]")
            item = [new_symbol]
        else:
            item = self.parse_atom()
            if (self.token.type == TokenType.OPERATOR and
                    self.token.value in ("+", "*")):
                new_symbol = self._create_internal_symbol()
                self.add_rule(new_symbol, item)
                self.add_rule(new_symbol, [new_symbol] + item)
                if self.token.value == "*":
                    self.add_rule(new_symbol, [])
                self.consume()
                item = [new_symbol]
        return item

    def parse_atom(self) -> List[Symbol]:
        # ATOM: '(' RHS ')' | NAME | STRING
        token = self.token
        atom = []  # type: List[Symbol]
        if token.type == TokenType.OPERATOR and token.value == "(":
            self.consume()
            new_symbol = self._create_internal_symbol()
            self.parse_rhs(new_symbol)
            atom.append(new_symbol)
            self.expect(TokenType.OPERATOR, ")")
        elif token.type == TokenType.IDENTIFIER:
            token = self.consume()
            if token.value.isupper():
                atom.append(Symbol(self.terminal_cls(token.value), True))
            else:
                atom.append(Symbol(token.value, False))
        elif token.type == TokenType.STRING:
            token = self.consume()
            atom.append(Symbol(self.terminal_cls(token.value), True))
        else:
            assert False, "Expected (...), identifier or string: %s" % token
        return atom

    def expect(self, type, value=None):
        msg = "%s(%s) != %s(%s)" % (
            self.token.type, self.token.value, type, value)
        if type is not None:
            assert self.token.type == type, msg
        if value is not None:
            assert self.token.value == value, msg
        return self.consume()

    def consume(self):
        token = self.token
        self.token = next(self.tokens)
        return token
