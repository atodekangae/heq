import argparse
from dataclasses import dataclass
import typing as T

Grammar = None

try:
    from parsimonious.grammar import Grammar
except ImportError:
    pass

@dataclass(frozen=True)
class seq:
    elems: list

    def __truediv__(self, elem):
        return self.__class__(self.elems + [elem])

@dataclass(frozen=True)
class xpath:
    xpath: str

    @property
    def text(self):
        return xpath_text(self.xpath)

    def __truediv__(self, other):
        return seq([self]) / other

@dataclass(frozen=True)
class xpath_text:
    xpath: str

Expr = T.Union[seq, xpath, xpath_text, dict[str, 'Expr']]

if Grammar is not None:
    grammar = Grammar(r'''
        s = expr _
        expr = (xpath_lit _ "/")* (dict_lit / dottext)
        dict_lit = _ "{" ((dict_field_value _ "," _ !"}")* dict_field_value _ ("," _)?)? "}"
        dict_field_value = dict_field _ ":" expr
        dict_field = _ ~r"[_a-zA-Z][_0-9a-zA-Z]*"
        xpath_lit = _ "xpath" _ (single_quote_lit / double_quote_lit)
        single_quote_lit = "'" (~r"[^\\']+" / "\\'" / "\\\\")+ "'"
        double_quote_lit = '"' (~r'[^\\"]+' / '\\"' / "\\\\")+ '"'
        dottext = xpath_lit _ ".text"
        _ = ws*
        ws = ~r"\s+"
    ''')

    def parse():
        pass

def evaluate(expr: Expr):
    def _evaluate1(tree):
        return _evaluate(expr, tree)
    def _evaluate(e, t):
        if isinstance(e, seq):
            if len(e.elems) == 0:
                raise ValueError()
            if len(e.elems) == 1:
                return _evaluate(e.elems[0], t)
            first = e.elems[0]
            rest = e.elems[1:]
            seq_rest = seq(rest)
            return [_evaluate(seq_rest, t1) for t1 in _evaluate(first, t)]
        elif isinstance(e, xpath):
            return t.xpath(e.xpath)
        elif isinstance(e, xpath_text):
            return t.xpath(e.xpath)[0].text
        elif isinstance(e, dict):
            return {k: _evaluate(v, t) for k, v in e.items()}
        raise TypeError()
    return _evaluate1

def extract(expr, tree):
    return evaluate(expr)(tree)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', required=True)
    parser.add_argument('--output', '-o')
    parser.add_argument('--input', '-i')
    args = parser.parse_args()
    with open(args.file, 'rb') as fp:
        source = fp.read().decode('utf-8')
    expr = evaluate(parse(source))
    if args.input:
        with open(args.input, 'rb') as fp:
            html = fp.read().decode('utf-8')
    else:
        html = sys.stdin.read()
    tree = lxml.etree.HTML(html)
    out = extract(expr, tree)
    if args.output:
        with open(args.output, 'wb') as fp:
            fp.write(json.dumps(out, indent=2).encode('utf-8'))
    else:
        print(json.dumps(out, indent=2))

if __name__ == '__main__a':
    main()
