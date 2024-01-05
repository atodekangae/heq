# ex3: Declarative DSL for structured data extraction from HTML based on XPath

## Usage
```python
from ex3 import extract, xpath
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
