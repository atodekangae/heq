# heq: Yet Another 'jq for HTML'
**heq** is a command-line tool for extracting structured data from HTML using concise expressions, akin to jq. Additionally, heq serves as a Python library, facilitating the efficient scraping of HTML content through its jq-inspired DSL based on XPath.

## Usage as a command-line tool
```
$ cat << 'EOF' | heq '`//div[@class="product"]` / {name: `.//h2[@class="name"]`.text}'
<body>
    <div id="header">Welcome to Our Store!</div>
    <div id="announcement">Special Offer: 20% off on all products this week!</div>
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
</body>
EOF
```

Output:

```
[
  {"name": "Widget A"},
  {"name": "Gadget B"}
]
```

```
$ cat expr.heq
`//div[@class="product"]` / {
    name: `.//h2[@class="name"]`.text,
    price: `.//p[@price="name"]`.text,
    features': `.//li` / text
}
$ cat << 'EOF' | heq -f expr.heq
(same as above)
EOF
```

Output:

```
[
  {
    "name": "Widget A",
    "price": "$10",
    "features": ["Durable", "Lightweight"]
  },
  {
    "name": "Gadget B",
    "price": "$20",
    "features": ["Compact", "Energy Efficient"]
  }
]
```

## Usage as a library
```python
from heq import extract, xpath
import lxml.etree
tree = lxml.etree.HTML('''<body>
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
</body>''')

expr = xpath("//div[@class='product']") / {
    'name': xpath(".//h2[@class='name']").text,
    'price': xpath(".//p[@class='price']").text,
    'features': xpath(".//li") / {
      'feature': xpath('.').text
    }
}

print(extract(expr, tree))
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
<expr> ::= <xpath_lit> '/' <term>
         | <term>
<term> ::= <dict_lit> | <dottext> | <filter>
<filter> ::= "text"
<dict_lit> ::= '{' ((<dict_field_value> ',')* <dict_field_value>)? '}'
<dict_field_value> ::= <dict_field> ':' <expr>
<xpath_lit> ::= <backtick_lit>
<dottext> ::= <xpath_lit> '.text'
```

heq has the concept of *context DOM tree*. This is the DOM tree against which XPath expressions are evaluated. It changes as the `/` operator is applied, to each of the elements.

 1. Value Forms
    * `{key: expression}`: Evaluates to a dictionary. `key` is a string without quotes and `expression` is an expression.
    * `text`: Evaluates to a string representing the text content of the context DOM tree.
    * `` `<xpath>`.text ``: Evaluates to a string representing the text content of the element(s) selected by the specified XPath expression.
 2. Mapping Against Query Results
    * `` `<xpath>` / <value_form> ``: First, evaluates the XPath expression to obtain a list of elements. Then, for each element, the `value_form` is evaluated with the element as the new context DOM tree. The entire expression evaluates to an array.

## Examples
### Target HTML
```html
<body>
    <div id="header">Welcome to Our Store!</div>
    <div id="announcement">Special Offer: 20% off on all products this week!</div>
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
</body>
```

### Example 1
```
{ header: `//div[@id="header"]`.text }
```

evaluates to:

```
{ "header": "Welcome to Our Store!" }
```


### Example 2
```
`//div[@id="header"]`.text
```

evaluates to:

```
"Welcome to Our Store!"
```

### Example 3
```
`//div[@class="product"]` / {
    name: `.//h2[@class="name"]`.text,
    price: `.//p[@class="price"]`.text,
    features: `.//li` / text
}
```

evaluates to:

```
[
  {
    "name": "Widget A",
    "price": "$10",
    "features": ["Durable", "Lightweight"]
  },
  {
    "name": "Gadget B",
    "price": "$20",
    "features": ["Compact", "Energy Efficient"]
  }
]
```
