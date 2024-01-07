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
        return sel_text(self)

    def __truediv__(self, other):
        return sel_map_pred(self, other)

    def __matmul__(self, attr):
        return sel_attr(self, attr)

    def select(self, tree):
        return tree.xpath(self.xpath)

@dataclass(frozen=True)
class css:
    css: str

    @property
    def text(self):
        return sel_text(self)

    def __truediv__(self, other):
        return sel_map_pred(self, other)

    def __matmul__(self, attr):
        return sel_attr(self, attr)

    def select(self, tree):
        return tree.cssselect(self.css)

@dataclass(frozen=True)
class sel_text:
    sel: T.Union[xpath, css]

@dataclass(frozen=True)
class sel_attr:
    sel: T.Union[xpath, css]
    attr: str

@dataclass(frozen=True)
class sel_map_pred:
    sel: T.Union[xpath, css]
    pred: T.Any

@dataclass(frozen=True)
class unary_func:
    name: str
text = unary_func('text')

@dataclass(frozen=True)
class attr:
    name: str

Expr = T.Union[xpath, css, sel_text, sel_map_pred, unary_func, attr, T.Dict[str, 'Expr']]

if Grammar is not None:
    from parsimonious.nodes import NodeVisitor

    grammar = Grammar(r'''
        s = expr _
        expr = (selector_lit _ "/")? (dict_lit / dottext / atattr / unary_func / attr_lit)
        unary_func = _ ident
        dict_lit = _ "{" ((dict_field_value _ "," _ !"}")* dict_field_value _ ("," _)?)? "}"
        dict_field_value = dict_field _ ":" expr
        dict_field = _ ~r"[_a-zA-Z][_0-9a-zA-Z]*"
        selector_lit = css_lit / xpath_lit
        xpath_lit = _ backtick_lit
        css_lit = _ "$" backtick_lit
        backtick_lit = "`" (~r"[^\\`]+" / "\\`" / "\\\\")+ "`"
        single_quote_lit = "'" (~r"[^\\']+" / "\\'" / "\\\\")+ "'"
        double_quote_lit = '"' (~r'[^\\"]+' / '\\"' / "\\\\")+ '"'
        dottext = selector_lit _ ".text"
        atattr = selector_lit attr_lit
        attr_lit = _ "@" ~r"[-_0-9a-zA-Z]+"
        ident = ~r"[_a-zA-Z][_0-9a-zA-Z]+"
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

        def visit_unary_func(self, node, visited_children):
            _, ident = visited_children
            return unary_func(ident)

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

        def visit_atattr(self, node, visited_children):
            xp, at = visited_children
            return xp @ at.name

        def visit_selector_lit(self, node, visited_children):
            sel, = visited_children
            return sel

        def visit_xpath_lit(self, node, visited_children):
            *_, lit = visited_children
            return xpath(lit)

        def visit_css_lit(self, node, visited_children):
            *_, lit = visited_children
            return css(lit)

        def visit_backtick_lit(self, node, visited_children):
            return ''.join({'\\`': '`', '\\\\': '\\'}.get(n.text, n.text) for n in node.children[1:-1])

        def visit_ident(self, node, visited_children):
            return node.text

        def visit_attr_lit(self, node, visited_children):
            return attr(node.children[-1].text)

        def generic_visit(self, node, visited_children):
            return visited_children or node

    def parse(s: str) -> Expr:
        return ExNodeVisitor().visit(grammar.parse(s))

def evaluate(expr: Expr):
    def _evaluate1(tree):
        return _evaluate(expr, tree)
    def _evaluate(e, t):
        if isinstance(e, sel_map_pred):
            return [_evaluate(e.pred, t1) for t1 in e.sel.select(t)]
        elif isinstance(e, sel_text):
            return ''.join(s for t1 in e.sel.select(t) for s in t1.itertext())
        elif isinstance(e, sel_attr):
            return e.sel.select(t)[0].attrib.get(e.attr, '')
        elif isinstance(e, dict):
            return {k: _evaluate(v, t) for k, v in e.items()}
        elif isinstance(e, unary_func) and e.name == 'text':
            return ''.join(s for s in t.itertext())
        elif isinstance(e, attr):
            return t.attrib.get(e.name, '')
        raise TypeError(f'{type(e)} is not a value; given: {e}')
    return _evaluate1

def extract(expr: Expr, tree_or_html: T.Union[str, 'lxml.etree._Element']):
    if isinstance(tree_or_html, str):
        import lxml.etree
        tree = lxml.etree.HTML(tree_or_html)
    else:
        tree = tree_or_html
    return evaluate(expr)(tree)

def main():
    import lxml.etree
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', help='script source file')
    parser.add_argument('--output', '-o', help='output file')
    parser.add_argument('--input', '-i', help='input file (stdin is used if not given)')
    parser.add_argument('EXPR', nargs='?', help='script')
    args = parser.parse_args()
    if bool(args.file) ==  bool(args.EXPR):
        parser.print_help()
        print('Exactly one of --file and EXPR must be given', file=sys.stderr)
        sys.exit(1)
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
