from io import BytesIO
from parser import Parser, Symbol
from grammar_parser import GrammarParser
import sys
import tokenize


TOKEN_MAP = {
    name: getattr(tokenize, name) for name in
    {"ASYNC", "AWAIT", "ENDMARKER", "INDENT", "DEDENT", "NAME", "NEWLINE",
     "NUMBER", "STRING"}
}


class Terminal(object):
    def __init__(self, value):
        self.is_token_type = False
        if value.isupper():
            self.is_token_type = True
            self.token_type = TOKEN_MAP[value]
        self.value = value

    def match(self, token):
        if self.is_token_type:
            return token.type == self.token_type
        return token.string == self.value

    def __str__(self):
        return self.value


def main():
    grammar = open("Grammar.txt").read()
    gp = GrammarParser(Terminal)
    grammar = gp.parse(grammar)
    parser = Parser(grammar)

    file = open(sys.argv[1], "rb")
    tokens = []
    for token in tokenize.tokenize(file.readline):
        if token.type in (tokenize.ENCODING, tokenize.COMMENT, tokenize.NL):
            continue
        tokens.append(token)
    parser.parse(tokens)


main()
