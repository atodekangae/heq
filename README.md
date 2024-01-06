# heq: Yet Another 'jq for HTML'
heq is a tool designed to provide a jq-like experience for HTML content. It is declarative in nature, allowing users to specify what they want to extract from HTML documents using a syntax similar to jq. heq can be used both as a CLI tool and as a Python library. As a Python library, it is particularly useful for web scraping, enabling users to easily extract structured data from HTML.

## Usage as a CLI tool
```
$ cat << 'EOF' | heq '`//div[@class="product"]` / {name: `.//h2[@class="name"]`.text}'
<body>
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
