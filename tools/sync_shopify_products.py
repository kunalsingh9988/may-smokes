#!/usr/bin/env python3
"""Import provisional one-variant products from the saved Vercel catalog."""

import html
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote

from sync_shopify_content import execute

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = json.loads((ROOT / 'src/products.json').read_text())
ROUTES = json.loads((ROOT / 'src/routes.json').read_text())
BATCH_SIZE = 10


def existing_products():
    handles = set()
    cursor = None
    query = '''query($cursor: String) {
      products(first: 250, after: $cursor) {
        nodes { handle }
        pageInfo { hasNextPage endCursor }
      }
    }'''
    while True:
        result = execute(query, {'cursor': cursor})['products']
        handles.update(node['handle'] for node in result['nodes'])
        if not result['pageInfo']['hasNextPage']:
            return handles
        cursor = result['pageInfo']['endCursor']


def product_input(handle):
    source = PRODUCTS[handle]
    title = re.sub(r'Bay Smokes', 'May Smokes', source['title'], flags=re.I)
    title = re.sub(r'Baysentials', 'May Essentials', title, flags=re.I)
    description = re.sub(r'Bay Smokes', 'May Smokes', source.get('description') or '', flags=re.I)
    price = str(Decimal(str(source['price'])).quantize(Decimal('0.01')))
    return {
        'title': title,
        'handle': handle,
        'status': 'ACTIVE',
        'descriptionHtml': '<p>' + html.escape(description).replace('\n', '<br>') + '</p>',
        'productOptions': [{'name': 'Title', 'position': 1, 'values': [{'name': 'Standard'}]}],
        'variants': [{'price': price, 'optionValues': [{'optionName': 'Title', 'name': 'Standard'}]}],
        'files': [{'originalSource': source['image'], 'contentType': 'IMAGE', 'alt': title}],
    }


def publish(ids, publication):
    if not ids:
        return
    variables = {f'id{i}': product_id for i, product_id in enumerate(ids)}
    definitions = ','.join(f'$id{i}:ID!' for i in range(len(ids)))
    fields = ''.join(
        f'p{i}:publishablePublish(id:$id{i},input:[{{publicationId:"{publication}"}}])'
        f'{{publishable {{ publishedOnPublication(publicationId:"{publication}") }} userErrors {{ field message }} }}'
        for i in range(len(ids))
    )
    result = execute(f'mutation({definitions}){{{fields}}}', variables, mutation=True)
    for i, product_id in enumerate(ids):
        errors = result[f'p{i}']['userErrors']
        if errors or not result[f'p{i}']['publishable']['publishedOnPublication']:
            print('PUBLISH ERROR', product_id, errors, flush=True)


def create_batch(handles, publication):
    if not handles:
        return
    definitions = ','.join(f'$p{i}:ProductSetInput!' for i in range(len(handles)))
    fields = ''.join(
        f'p{i}:productSet(input:$p{i},synchronous:true)'
        '{product { id handle } userErrors { field message }}'
        for i in range(len(handles))
    )
    variables = {f'p{i}': product_input(handle) for i, handle in enumerate(handles)}
    try:
        result = execute(f'mutation({definitions}){{{fields}}}', variables, mutation=True)
    except Exception as error:
        if len(handles) == 1:
            print('PRODUCT ERROR', handles[0], str(error)[-500:], flush=True)
            return
        half = len(handles) // 2
        create_batch(handles[:half], publication)
        create_batch(handles[half:], publication)
        return
    ids = []
    for i, handle in enumerate(handles):
        item = result[f'p{i}']
        if item['userErrors'] or not item['product']:
            print('PRODUCT ERROR', handle, item['userErrors'], flush=True)
        else:
            created = item['product']
            print('PRODUCT', handle, '=>', created['handle'], flush=True)
            ids.append(created['id'])
    try:
        publish(ids, publication)
    except Exception as error:
        print('PUBLISH BATCH ERROR', handles, str(error)[-500:], flush=True)


def main():
    seen = existing_products()
    publications = execute('query { publications(first: 20) { nodes { id name } } }')['publications']['nodes']
    publication = next(p['id'] for p in publications if p['name'] == 'Online Store')
    handles = [unquote(route.split('/')[-1]) for route in ROUTES if route.startswith('/products/')]
    pending = [handle for handle in handles if handle not in seen]
    print(f'Existing {len(seen)}; pending {len(pending)}', flush=True)
    for index in range(0, len(pending), BATCH_SIZE):
        create_batch(pending[index:index + BATCH_SIZE], publication)
        print(f'BATCH {index // BATCH_SIZE + 1}/{(len(pending) + BATCH_SIZE - 1) // BATCH_SIZE}', flush=True)


if __name__ == '__main__':
    sys.exit(main())
