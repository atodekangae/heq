import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from heq import parse, extract, xpath, css, text, attr
import re
import json
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
                {'feature': 'Compact'}, {'feature': 'Energy Efficient'}
            ]
        }
    ]
    assert extract(
        xpath("//div[@class='product']") / {
            'name': xpath(".//h2[@class='name']").text,
            'price': xpath(".//p[@class='price']").text,
            'features': xpath(".//li") / text
        },
        tree
    ) == [
        {
            'name': 'Widget A',
            'price': '$10',
            'features': [
                'Durable', 'Lightweight'
            ]
        },
        {
            'name': 'Gadget B',
            'price': '$20',
            'features': [
                'Compact', 'Energy Efficient'
            ]
        }
    ]
    assert extract(
        css("div.product") / {
            'name': css("h2.name").text,
            'price': css("p.price").text,
            'features': css("li") / text
        },
        tree
    ) == [
        {
            'name': 'Widget A',
            'price': '$10',
            'features': [
                'Durable', 'Lightweight'
            ]
        },
        {
            'name': 'Gadget B',
            'price': '$20',
            'features': [
                'Compact', 'Energy Efficient'
            ]
        }
    ]

    assert (
        extract(
            text,
            lxml.etree.HTML('<span>a</span><div>b<span>c</span>d</div>')
        )
        ==
        'abcd'
    )
    assert (
        extract(
            xpath('//span') / text,
            lxml.etree.HTML('<span>a</span><div>b<span>c</span>d</div>')
        )
        ==
        ['a', 'c']
    )
    assert (
        extract(
            css('span') / text,
            lxml.etree.HTML('<span>a</span><div>b<span>c</span>d</div>')
        )
        ==
        ['a', 'c']
    )
    assert (
        extract(
            xpath('//a') / attr('href'),
            lxml.etree.HTML('<a href="/link"></a>')
        )
        ==
        ['/link']
    )
    assert (
        extract(
            xpath('//ul//a') / attr('href'),
            lxml.etree.HTML('''
              <a href="/link_a">link a</a>
              <a href="/link_b">link b</a>
              <ul>
                <li><a href="/link1">link 1</a></li>
                <li><a href="/link2">link 2</a></li>
              </ul>
            ''')
        )
        ==
        ['/link1', '/link2']
    )
    assert (
        extract(
            xpath('//li') / (xpath('.//a') @ 'href'),
            lxml.etree.HTML('''
              <a href="/link_a">link a</a>
              <a href="/link_b">link b</a>
              <ul>
                <li><a href="/link1">link 1</a></li>
                <li><a href="/link2">link 2</a></li>
              </ul>
            ''')
        )
        ==
        ['/link1', '/link2']
    )
    assert (
        extract(
            css('li') / (css('a') @ 'href'),
            lxml.etree.HTML('''
              <a href="/link_a">link a</a>
              <a href="/link_b">link b</a>
              <ul>
                <li><a href="/link1">link 1</a></li>
                <li><a href="/link2">link 2</a></li>
              </ul>
            ''')
        )
        ==
        ['/link1', '/link2']
    )
    assert (
        extract(
            xpath('//a') / attr('nonexistent'),
            lxml.etree.HTML('<a href="/link"></a>')
        )
        ==
        ['']
    )
    assert (
        extract(
            xpath('//a') @ 'nonexistent',
            lxml.etree.HTML('<a href="/link"></a>')
        )
        ==
        ''
    )
    assert (
        extract(
            css('ul a') / attr('href'),
            lxml.etree.HTML('''
              <a href="/link_a">link a</a>
              <a href="/link_b">link b</a>
              <ul>
                <li><a href="/link1">link 1</a></li>
                <li><a href="/link2">link 2</a></li>
              </ul>
            ''')
        )
        ==
        ['/link1', '/link2']
    )

def test_parse():
    assert parse('`x` / {}') == xpath('x') / {}
    assert parse('text') == text
    assert parse('`x` / text') == xpath('x') / text
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
    assert parse('@name') == attr('name')
    assert parse('@name-with-hyphen') == attr('name-with-hyphen')
    assert parse('`//input` / @name') == xpath('//input') / attr('name')
    assert parse('`//input` / {name: @name}') == xpath('//input') / {'name': attr('name')}
    assert parse('`//input`@name') == xpath('//input') @ 'name'
    assert parse('`//input` @name') == xpath('//input') @ 'name'
    assert parse('$`input` / @name') == css('input') / attr('name')
    assert parse('$`input` / {name: @name}') == css('input') / {'name': attr('name')}
    assert parse('$`input`@name') == css('input') @ 'name'
    assert parse('$`input` @name') == css('input') @ 'name'

def test_readme_examples():
    readme = (Path(__file__).parent / 'README.md').read_text()
    target_html_pat = re.compile(r'''### Target HTML
```html
(.+?)
```''', re.DOTALL)
    test_pair_pat = re.compile(r'''# Example(?:\s+\d+)?
```
(.+?)
```\s+evaluates to:\s+```(?:json)?
(.+?)
```''', re.DOTALL)

    target_html = target_html_pat.search(readme).groups()[0]
    tree = lxml.etree.HTML(target_html)
    count = 0
    for m in test_pair_pat.finditer(readme):
        count += 1
        expr, expected_json = m.groups()
        expected = json.loads(expected_json)
        assert extract(parse(expr), tree) == expected
    assert count > 0
