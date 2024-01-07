# heq: Yet Another 'jq for HTML'
**heq** is a command-line tool for extracting structured data as JSON from HTML using concise expressions, akin to `jq`. Additionally, heq serves as a Python library, facilitating the efficient scraping of HTML content through its jq-inspired DSL based on XPath.

<!--
## Goal and Non-Goals
heq is not intended to replicate `jq`'s full functionality for HTML. The rationale is simple: once HTML is converted to JSON, users can utilize the comprehensive features of any existing tool operating on JSON -- most notably, `jq` -- for advanced JSON operations. Therefore, `heq` focuses on offering a way to efficiently transform HTML into JSON, with its jq-inspired DSL that leverages XPath.
-->

## Installation
```sh
pip install heq
```

heq depends on the following Python packages:

 * lxml
 * parsimonious

## Usage as a command-line tool
```console
$ cat << 'EOF' | heq '$`div.product` / {name: $`h2.name`.text}'
<body>
    <div id="header">Welcome to Our Store!</div>
    <div class="product">
      <h2 class="name">Widget A</h2>
      <p class="price">$10</p>
      <ul class="features"><li>Durable</li><li>Lightweight</li></ul>
      <a href="/products/widget_a">Details</a>
    </div>
    <div class="product">
      <h2 class="name">Gadget B</h2>
      <p class="price">$20</p>
      <ul class="features"><li>Compact</li><li>Energy Efficient</li></ul>
      <a href="/products/gadget_b">Details</a>
    </div>
</body>
EOF
```

Output:

```json
[
  {"name": "Widget A"},
  {"name": "Gadget B"}
]
```

```console
$ cat expr.heq
`//div[@class="product"]` / {
    name: `.//h2[@class="name"]`.text,
    price: `.//p[@class="price"]`.text,
    features: `.//li` / text,
    url: `.//a`@href
}
$ cat << 'EOF' | heq -f expr.heq
(The same HTML as above)
EOF
```

Output:

```json
[
  {
    "name": "Widget A",
    "price": "$10",
    "features": ["Durable", "Lightweight"],
    "url": "/products/widget_a"
  },
  {
    "name": "Gadget B",
    "price": "$20",
    "features": ["Compact", "Energy Efficient"],
    "url": "/products/gadget_b"
  }
]
```

## Usage as a library
```python
from heq import extract, xpath

html = '''<body>
    <div class="product">
      <h2 class="name">Widget A</h2>
      <p class="price">$10</p>
      <ul class="features"><li>Durable</li><li>Lightweight</li></ul>
    </div>
    <div class="product">
      <h2 class="name">Gadget B</h2>
      <p class="price">$20</p>
      <ul class="features"><li>Compact</li><li>Energy Efficient</li></ul>
    </div>
</body>'''

expr = xpath("//div[@class='product']") / {
    'name': xpath(".//h2[@class='name']").text,
    'price': xpath(".//p[@class='price']").text,
    'features': xpath(".//li") / {
      'feature': xpath('.').text
    }
}

print(extract(expr, html))
```

Output:

```
[{'name': 'Widget A',
  'price': '$10',
  'features': [{'feature': 'Durable'}, {'feature': 'Lightweight'}]},
 {'name': 'Gadget B',
  'price': '$20',
  'features': [{'feature': 'Compact'}, {'feature': 'Energy Efficient'}]}]
```

## Syntax and Semantics
### Informal BNF-like Representation
```
<S> ::= <expr>
<expr> ::= <selector_lit> '/' <term>
         | <term>
<term> ::= <dict_lit> | <dottext> | <atattr> | <filter>
<filter> ::= 'text' | <attr_lit>
<dict_lit> ::= '{' ((<dict_field_value> ',')* <dict_field_value>)? '}'
<dict_field_value> ::= <dict_field> ':' <expr>
<dottext> ::= <selector_lit> '.text'
<atattr> ::= <selector_lit> <attr_lit>
<selector_lit> ::= <css_lit> / <xpath_lit>
<css_lit> ::= '$' <backtick_lit>
<xpath_lit> ::= <backtick_lit>
<attr_lit> ::= '@' <ident_with_hyphen>
```

heq has the concept of *context DOM tree*. This is the DOM tree against which XPath expressions or CSS selectors are evaluated. Initially, it is set to the root tree, and it changes as the `/` operator is applied, to each of the elements.

Available syntactic constructs and their semantics are as follows:

 1. Value Forms
    * `{key: expression}`: Evaluates to a dictionary. `key` is a string without quotes and `expression` is an expression.
    * `text`: Evaluates to a string representing the text content of the context DOM tree.
    * `@attr`: Evaluates to the value associated with the attribute `attr` of the context DOM tree.
    * `<selector>.text`: Evaluates to a string representing the text content of the element(s) selected by the specified selector.
    * `<selector>@attr`: Evaluates to a string representing the value associated with the attribute `attr` of the first element selected by the specified XPath expression.
 2. Selectors
    * `` `<xpath>` ``: Selects elements by evaluating the XPath against the context DOM tree.
    * `` $`<css_selector>` ``: Selects elements by evaluating the CSS selector against the context DOM tree.
 3. Mapping Against Query Results
    * `<selector> / <value_form>`: First, evaluates the selector to obtain a list of elements. Then, for each element, the `value_form` is evaluated with the element as the new context DOM tree. The entire expression evaluates to an array.

## Examples
### Target HTML
```html
<body>
    <div id="header">Welcome to Our Store!</div>
    <div class="product">
      <h2 class="name">Widget A</h2>
      <p class="price">$10</p>
      <ul class="features"><li>Durable</li><li>Lightweight</li></ul>
      <a href="/products/widget_a">Details</a>
    </div>
    <div class="product">
      <h2 class="name">Gadget B</h2>
      <p class="price">$20</p>
      <ul class="features"><li>Compact</li><li>Energy Efficient</li></ul>
      <a href="/products/gadget_b">Details</a>
    </div>
</body>
```

### Example 1
```
{ header: `//div[@id="header"]`.text }
```

evaluates to:

```json
{ "header": "Welcome to Our Store!" }
```


### Example 2
```
`//div[@id="header"]`.text
```

evaluates to:

```json
"Welcome to Our Store!"
```

### Example 3
```
`//div[@class="product"]` / `.//a`@href
```

evaluates to:

```json
["/products/widget_a", "/products/gadget_b"]
```

### Example 4
```
`//div[@class="product"]` / {
    name: `.//h2[@class="name"]`.text,
    price: `.//p[@class="price"]`.text,
    features: `.//li` / text,
    url: `.//a`@href
}
```

evaluates to:

```json
[
  {
    "name": "Widget A",
    "price": "$10",
    "features": ["Durable", "Lightweight"],
    "url": "/products/widget_a"
  },
  {
    "name": "Gadget B",
    "price": "$20",
    "features": ["Compact", "Energy Efficient"],
    "url": "/products/gadget_b"
  }
]
```

### Example 5
```
$`div.product` / {
    name: $`h2.name`.text,
    price: $`p.price`.text,
    features: $`li` / text,
    url: $`a`@href
}
```

evaluates to:

```json
[
  {
    "name": "Widget A",
    "price": "$10",
    "features": ["Durable", "Lightweight"],
    "url": "/products/widget_a"
  },
  {
    "name": "Gadget B",
    "price": "$20",
    "features": ["Compact", "Energy Efficient"],
    "url": "/products/gadget_b"
  }
]
```
