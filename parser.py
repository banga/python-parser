from collections import namedtuple

# token = string
Symbol = namedtuple("Symbol", ["token", "is_terminal"])

# expansion = [Symbol]
Rule = namedtuple("Rule", ['symbol', 'expansion'])

# rules = [Symbol]
# start = Symbol
Grammar = namedtuple("Grammar", ['rules', 'start'])


def match(symbol, token):
    return symbol == token


class Item(object):
    def __init__(self, rule, start, position=0):
        self.rule = rule
        self.start = start
        self.position = position

    def __eq__(self, other):
        return (self.rule == other.rule and
            self.start == other.start and
            self.position == other.position)

    def is_partial_parse(self):
        return self.position == len(self.rule.expansion) and self.start == 0

    def is_full_parse(self, grammar):
        return self.is_partial_parse() and self.rule.symbol == grammar.start

    def can_match(self, symbol):
        return (self.position < len(self.rule.expansion) and
            self.rule.expansion[self.position] == symbol)

    def __str__(self):
        s = ""
        s += self.rule.symbol.token + " ->"
        for symbol in self.rule.expansion[:self.position]:
            s += " " + symbol.token
        s += " •"
        for symbol in self.rule.expansion[self.position:]:
            s += " " + symbol.token
        s += " (%d)" % self.start
        return s


class Parser(object):
    def __init__(self, grammar):
        self.grammar = grammar

    def parse(self, input):
        self.states = [[] for _ in range(len(input) + 1)]

        # Intiialize S(0)
        for rule in self.grammar.rules:
            if rule.symbol == self.grammar.start:
                self.states[0].append(Item(rule, 0))

        for idx, state in enumerate(self.states):
            print("=" * 10)
            if idx < len(input):
                token = input[idx]
            else:
                token = None
            print("Parsing", token)
            print("=" * 10)
            for item in state:
                print(item)
                # Completion
                if item.position == len(item.rule.expansion):
                    print("  Completions:",)
                    for completing_item in self.get_advancing_items(
                            item.rule.symbol, self.states[item.start]):
                        print("   ", completing_item)
                        state.append(Item(
                            completing_item.rule,
                            completing_item.start,
                            completing_item.position + 1))
                else:
                    symbol = item.rule.expansion[item.position]
                    # Scan
                    if symbol.is_terminal:
                        if match(symbol, token):
                            print("  Scanned successfully", token)
                            self.add_item(self.states[idx + 1],
                                Item(item.rule, item.start, item.position + 1))
                    else:
                        # Prediction
                        for rule in self.get_predictions(symbol):
                            print("  Predicted:", rule.symbol.token, "->",
                                [s.token for s in rule.expansion])
                            self.add_item(state, Item(rule, idx))

        print("=" * 10)
        print("Finished parsing")
        for item in self.states[-1]:
            if item.is_full_parse(self.grammar):
                print("Fully parsed:", item)
                break
        else:
            for state in self.states[::-1]:
                for item in state:
                    if item.is_full_parse(self.grammar):
                        print("Partial parse:", item)

    def get_advancing_items(self, symbol, state):
        """Find any items in state that can match symbol"""
        for item in state:
            if item.can_match(symbol):
                yield item

    def get_predictions(self, symbol):
        """Get all rules that expand symbol"""
        for rule in self.grammar.rules:
            if rule.symbol == symbol:
                yield rule

    def add_item(self, state, new_item):
        # TODO: use sets for states
        for item in state:
            if item == new_item:
                return
        state.append(new_item)

    def __str__(self):
        s = []
        for i, state in enumerate(self.states):
            s.append("-" * 10)
            s.append("  State %d" % i)
            s.append("-" * 10)
            for item in state:
                s.append("    " + str(item))
        return "\n".join(s)


def test():
    Sum = Symbol("Sum", False)
    Product = Symbol("Product", False)
    Factor = Symbol("Factor", False)
    Number = Symbol("Number", False)
    # TODO: tokenization
    one = Symbol("1", True)
    plus = Symbol("+", True)
    star = Symbol("*", True)
    lparen = Symbol("(", True)
    rparen = Symbol(")", True)

    grammar = Grammar(
        rules=[
            Rule(Sum, [Sum, plus, Product]),
            Rule(Sum, [Product]),
            Rule(Product, [Product, star, Factor]),
            Rule(Product, [Factor]),
            Rule(Factor, [lparen, Sum, rparen]),
            Rule(Factor, [Number]),
            Rule(Number, [one, Number]),
            Rule(Number, [one]),
        ],
        start=Sum)
    input = [one, plus, one, star, lparen, one, rparen]
    # input = [one, plus, lparen, one, star, one, plus, one, rparen]
    # input = [one, plus, lparen, one, rparen]
    # input = [lparen, one, rparen]
    # input = [one, plus, one]
    # input = [one]
    parser = Parser(grammar)
    parser.parse(input)
    # print(parser)

test()
