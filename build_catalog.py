import json
import re
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

root = Path(__file__).parent
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
index = ET.fromstring(urlopen('https://baysmokes.com/sitemap.xml').read())
routes = []
for element in index.findall('.//s:loc', ns):
    url = element.text
    if '/es/' in url or 'agentic' in url:
        continue
    document = ET.fromstring(urlopen(url).read())
    for item in document.findall('.//s:loc', ns):
        path = urlparse(item.text).path
        if path and path not in routes:
            routes.append(path)
(root / 'src').mkdir(exist_ok=True)
(root / 'src' / 'routes.json').write_text(json.dumps(routes, separators=(',', ':')))

products = {}
for page in range(1, 9):
    data = json.loads(urlopen(f'https://baysmokes.com/products.json?limit=250&page={page}').read())['products']
    if not data:
        break
    for product in data:
        variants = product.get('variants') or []
        price = variants[0].get('price') if variants else None
        images = product.get('images') or []
        products[product['handle']] = {
            'title': re.sub(r'Bay Smokes', 'May Smokes', product['title'], flags=re.I),
            'price': price,
            'image': images[0].get('src') if images else None,
            'description': re.sub(r'Bay Smokes', 'May Smokes', re.sub('<[^>]+>', ' ', product.get('body_html') or ''), flags=re.I).strip()[:600],
        }
    print('products', page, len(data))
(root / 'src' / 'products.json').write_text(json.dumps(products, separators=(',', ':')))
print('routes', len(routes), 'products', len(products))
