#!/usr/bin/env python3
"""Apply saved collection membership after the provisional product import."""

import json
from pathlib import Path
from urllib.parse import unquote

from sync_shopify_content import execute

ROOT = Path(__file__).resolve().parents[1]
MEMBERSHIP = json.loads((ROOT / 'src/collections.json').read_text())


def products_by_handle():
    products = {}
    cursor = None
    query = '''query($cursor:String) { products(first:250, after:$cursor) {
      nodes { id handle } pageInfo { hasNextPage endCursor }
    } }'''
    while True:
        result = execute(query, {'cursor': cursor})['products']
        products.update({item['handle']: item['id'] for item in result['nodes']})
        if not result['pageInfo']['hasNextPage']:
            return products
        cursor = result['pageInfo']['endCursor']


def current_members(collection_id):
    ids = set()
    cursor = None
    query = '''query($id:ID!,$cursor:String) { collection(id:$id) {
      products(first:250, after:$cursor) {
        nodes { id } pageInfo { hasNextPage endCursor }
      }
    } }'''
    while True:
        result = execute(query, {'id': collection_id, 'cursor': cursor})['collection']['products']
        ids.update(item['id'] for item in result['nodes'])
        if not result['pageInfo']['hasNextPage']:
            return ids
        cursor = result['pageInfo']['endCursor']


def main():
    product_ids = products_by_handle()
    collections = {item['handle']: item['id'] for item in
                   execute('query { collections(first:100) { nodes { id handle } } }')['collections']['nodes']}
    mutation = '''mutation($id:ID!,$productIds:[ID!]!) {
      collectionAddProducts(id:$id,productIds:$productIds) {
        collection { id } userErrors { field message }
      }
    }'''
    for handle, source_handles in MEMBERSHIP.items():
        collection_id = collections.get(handle)
        if not collection_id:
            print('MISSING COLLECTION', handle, flush=True)
            continue
        existing = current_members(collection_id)
        missing = [h for h in source_handles if unquote(h) not in product_ids]
        if missing:
            print('MISSING PRODUCTS', handle, missing[:10], len(missing), flush=True)
        desired = [product_ids[unquote(h)] for h in source_handles if unquote(h) in product_ids]
        to_add = list(dict.fromkeys(product_id for product_id in desired if product_id not in existing))
        for start in range(0, len(to_add), 250):
            batch = to_add[start:start + 250]
            result = execute(mutation, {'id': collection_id, 'productIds': batch}, mutation=True)['collectionAddProducts']
            if result['userErrors']:
                print('COLLECTION ERROR', handle, result['userErrors'], flush=True)
            else:
                print('COLLECTION MEMBERS', handle, len(batch), flush=True)


if __name__ == '__main__':
    main()
