import sys
import argparse
import json
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
        return dot_text(self)

    def __truediv__(self, other):
        return map_pred(self, other)

    def __matmul__(self, attr):
        return at_attr(self, attr)

    def select(self, tree):
        return tree.xpath(self.xpath)

@dataclass(frozen=True)
class css:
    css: str

    @property
    def text(self):
        return dot_text(self)

    def __truediv__(self, other):
        return map_pred(self, other)

    def __matmul__(self, attr):
        return at_attr(self, attr)

    def select(self, tree):
        return tree.cssselect(self.css)

@dataclass(frozen=True)
class dot_text:
    expr: 'Expr'

@dataclass(frozen=True)
class at_attr:
    expr: 'Expr'
    attr: str

@dataclass(frozen=True)
class map_pred:
    expr: 'Expr'
    pred: T.Any

@dataclass(frozen=True)
class unary_func:
    name: str
text = unary_func('text')

@dataclass(frozen=True)
class attr:
    name: str

Expr = T.Union[xpath, css, dot_text, at_attr, map_pred, unary_func, attr, T.Dict[str, 'Expr']]

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

MAX_LINE_WIDTH = 80
def pretty_format_internal(obj, depth=0) -> T.List[str]:
    import lxml.etree

    if isinstance(obj, (int, float, str)) or obj is None:
        return [json.dumps(obj)]
    elif isinstance(obj, list):
        if len(obj) == 0:
            return ['[]']
        elems = [pretty_format_internal(x, depth+1) for x in obj]
        available = MAX_LINE_WIDTH - 2*depth
        if all(len(e) == 1 for e in elems) and (sum(len(e[0]) for e in elems) + 2 * (len(obj) - 1) <= available):
            return ['[{}]'.format(', '.join(e[0] for e in elems))]
        result = []
        for i, es in enumerate(elems):
            for e in es[:-1]:
                result.append('  ' + e)
            if i != len(elems) - 1:
                result.append('  '+es[-1]+',')
            else:
                result.append('  '+es[-1])
        ('  ' + e for es in elems for e in es)
        return ['[', *result, ']']
    elif isinstance(obj, dict):
        if len(obj) == 0:
            return ['{}']
        elems = {k: pretty_format_internal(v, depth+1) for k, v in obj.items()}
        available = MAX_LINE_WIDTH - 2*depth
        if all(len(e) == 1 for e in elems.values()) and (sum(4 + len(k) + len(es[0]) for k, es in elems.items()) + 2 * (len(obj) - 1) <= available):
            # TODO: escape key
            return ['{' + ', '.join('"{}": {}'.format(k, es[0]) for k, es in elems.items()) + '}']
        result = []
        for i, (k, es) in enumerate(elems.items()):
            # TODO: escape key
            result.append('  "{}": {}'.format(k, es[0]))
            for e in es[1:-1]:
                result.append('  ' + e)
            if len(es) > 1:
                if i != len(elems) - 1:
                    result.append('  ' + es[-1] + ',')
                else:
                    result.append('  ' + es[-1])
        return ['{', *result,'}']
    elif isinstance(obj, lxml.etree._Element):
        return lxml.etree.tostring(obj).decode('utf-8').splitlines()
    raise TypeError()

def pretty_format(obj):
    return '\n'.join(pretty_format_internal(obj))

def evaluate(expr: Expr):
    def _evaluate1(tree):
        return _evaluate(expr, tree)
    def _evaluate(e, t):
        if isinstance(e, map_pred):
            return [_evaluate(e.pred, t1) for t1 in _evaluate(e.expr, t)]
        elif isinstance(e, dot_text):
            return ''.join(s for t1 in _evaluate(e.expr, t) for s in t1.itertext())
        elif isinstance(e, at_attr):
            selected = _evaluate(e.expr, t)
            if not selected:
                return ''
            return selected[0].attrib.get(e.attr, '')
        elif isinstance(e, (xpath, css)):
            return e.select(t)
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

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', help='script source file')
    parser.add_argument('--output', '-o', help='output file')
    parser.add_argument('--input', '-i', help='input file (stdin is used if not given)')
    parser.add_argument('--debug', '-d', action='store_true')
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
    if args.debug:
        format_func = pretty_format
    else:
        format_func = lambda x: json.dumps(x, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, 'wb') as fp:
            fp.write(format_func(out).encode('utf-8'))
    else:
        print(format_func(out))

if __name__ == '__main__':
    main()
