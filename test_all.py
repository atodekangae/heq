import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from hexq import xpath, parse, extract
import pytest
import lxml.etree

def test_extract():
    tree = lxml.etree.HTML('''
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
    ''')

    assert extract(
        xpath('//div[@class="product"]') / {
            'name': xpath('.//h2[@class="name"]').text
        },
        tree
    ) == [{'name': 'Widget A'}, {'name': 'Gadget B'}]
    assert extract(
        xpath("//div[@class='product']") / {
            'name': xpath(".//h2[@class='name']").text,
            'price': xpath(".//p[@class='price']").text,
            'features': xpath(".//li") / {
                'feature': xpath('.').text
            }
        },
        tree
    ) == [
        {
            'name': 'Widget A',
            'price': '$10',
            'features': [
                {'feature': 'Durable'}, {'feature': 'Lightweight'}
            ]
        },
        {
            'name': 'Gadget B',
            'price': '$20',
            'features': [
                {'feature': 'Compact'},
                {'feature': 'Energy Efficient'}
            ]
        }
    ]

def test_parse():
    assert (
        parse('`x` / {}') ==
        xpath('x') / {}
    )
    assert (
        parse('`//div[@class="product"]` / {name: `.//h2[@class="name"]`.text}') ==
        xpath('//div[@class="product"]') / {
            'name': xpath('.//h2[@class="name"]').text
        }
    )
    assert (
        parse('''
        `//div[@class='product']` / {
            name: `.//h2[@class='name']`.text,
            price: `.//p[@class='price']`.text,
            features: `.//li` / {
                feature: `.`.text
            }
        }
        ''') ==
        xpath("//div[@class='product']") / {
            'name': xpath(".//h2[@class='name']").text,
            'price': xpath(".//p[@class='price']").text,
            'features': xpath(".//li") / {
                'feature': xpath('.').text
            }
        }
    )
