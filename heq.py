import sys
import argparse
from dataclasses import dataclass
import typing as T

Grammar = None

try:
    from parsimonious.grammar import Grammar
except ImportError:
    pass

@dataclass(frozen=True)
class xpath:
    xpath: str

    @property
    def text(self):
        return xpath_text(self.xpath)

    def __truediv__(self, other):
        return xpath_map_pred(self.xpath, other)

@dataclass(frozen=True)
class xpath_text:
    xpath: str

@dataclass(frozen=True)
class xpath_map_pred:
    xpath: str
    pred: T.Any

Expr = T.Union[xpath, xpath_text, xpath_map_pred, T.Dict[str, 'Expr']]

if Grammar is not None:
    from parsimonious.nodes import NodeVisitor

    grammar = Grammar(r'''
        s = expr _
        expr = (xpath_lit _ "/")? (dict_lit / dottext)
        dict_lit = _ "{" ((dict_field_value _ "," _ !"}")* dict_field_value _ ("," _)?)? "}"
        dict_field_value = dict_field _ ":" expr
        dict_field = _ ~r"[_a-zA-Z][_0-9a-zA-Z]*"
        xpath_lit = _ (backtick_lit / ("xpath" _ (single_quote_lit / double_quote_lit)))
        backtick_lit = "`" (~r"[^\\`]+" / "\\`" / "\\\\")+ "`"
        single_quote_lit = "'" (~r"[^\\']+" / "\\'" / "\\\\")+ "'"
        double_quote_lit = '"' (~r'[^\\"]+' / '\\"' / "\\\\")+ '"'
        dottext = xpath_lit _ ".text"
        _ = ws*
        ws = ~r"\s+"
    ''')

    class ExNodeVisitor(NodeVisitor):

        def visit_s(self, node, visited_children):
            return visited_children[0]

        def visit_expr(self, node, visited_children):
            maybe_xpath, leaf = visited_children
            if isinstance(maybe_xpath, list):
                return maybe_xpath[0][0] / leaf[0]
            return leaf[0]

        def visit_dict_lit(self, node, visited_children):
            _, _, ns, _ = visited_children
            if not isinstance(ns, list):
                return {}
            [[ns1, last, *_]] = ns
            d = {n[0][0]: n[0][1] for n in ns1}
            k, v = last
            d[k] = v
            return d

        def visit_dict_field_value(self, node, visited_children):
            k, *_, v = visited_children
            return (k, v)

        def visit_dict_field(self, node, visited_children):
            return visited_children[-1].text

        def visit_dottext(self, node, visited_children):
            return visited_children[0].text

        def visit_xpath_lit(self, node, visited_children):
            return visited_children[-1][0]

        def visit_backtick_lit(self, node, visited_children):
            return xpath(''.join({'\\`': '`', '\\\\': '\\'}.get(n.text, n.text) for n in node.children[1:-1]))

        def generic_visit(self, node, visited_children):
            return visited_children or node

    def parse(s: str):
        return ExNodeVisitor().visit(grammar.parse(s))

def evaluate(expr: Expr):
    def _evaluate1(tree):
        return _evaluate(expr, tree)
    def _evaluate(e, t):
        if isinstance(e, xpath_map_pred):
            return [_evaluate(e.pred, t1) for t1 in t.xpath(e.xpath)]
        elif isinstance(e, xpath_text):
            return ''.join(s for e in t.xpath(e.xpath) for s in e.itertext())
        elif isinstance(e, dict):
            return {k: _evaluate(v, t) for k, v in e.items()}
        raise TypeError(f'{type(e)} is not a value')
    return _evaluate1

def extract(expr, tree):
    return evaluate(expr)(tree)

def main():
    import lxml.etree
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--output', '-o')
    parser.add_argument('--input', '-i')
    parser.add_argument('EXPR', nargs='?')
    args = parser.parse_args()
    if bool(args.file) ==  bool(args.EXPR):
        raise Exception('Exactly one of --file and EXPR must be given')
    if args.file:
        with open(args.file, 'rb') as fp:
            source = fp.read().decode('utf-8')
    if args.EXPR:
        source = args.EXPR
    expr = parse(source)
    if args.input:
        with open(args.input, 'rb') as fp:
            html = fp.read().decode('utf-8')
    else:
        html = sys.stdin.read()
    tree = lxml.etree.HTML(html)
    out = extract(expr, tree)
    if args.output:
        with open(args.output, 'wb') as fp:
            fp.write(json.dumps(out, indent=2, ensure_ascii=False).encode('utf-8'))
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
