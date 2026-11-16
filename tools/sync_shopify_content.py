#!/usr/bin/env python3
"""Create the May Smokes page and collection routes in the connected Shopify store."""

import html
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = 'may-smokes.myshopify.com'
ROUTES = json.loads((ROOT / 'src/routes.json').read_text())
CONTENT = json.loads((ROOT / 'src/content.json').read_text())
LEGAL_HANDLES = {'privacy-policy', 'refund-policy', 'shipping-policy', 'subscription-policy', 'terms-of-service'}


def execute(query, variables=None, mutation=False):
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder) / 'response.json'
        args = ['shopify', 'store', 'execute', '--store', STORE, '--no-input', '--json',
                '--query', query, '--output-file', str(output)]
        if variables is not None:
            args += ['--variables', json.dumps(variables, ensure_ascii=False)]
        if mutation:
            args.append('--allow-mutations')
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode:
            raise RuntimeError((output.read_text() if output.exists() else '') + result.stderr + result.stdout)
        payload = json.loads(output.read_text())
    if payload.get('errors'):
        raise RuntimeError(payload['errors'])
    return payload.get('data', payload)


def title_case(handle):
    return handle.replace('-', ' ').replace('Thca', 'THCa').title().replace('Thca', 'THCa')


def body_for(route):
    blocks = CONTENT.get(route, [])
    return ''.join(f'<{block["tag"]}>{html.escape(block["text"])}</{block["tag"]}>'
                   for block in blocks if block['tag'] in {'h1', 'h2', 'h3', 'p', 'li'})


def sync_pages():
    query = 'query { pages(first: 250) { nodes { handle } } }'
    existing = {node['handle'] for node in execute(query)['pages']['nodes']}
    create = 'mutation($page: PageCreateInput!) { pageCreate(page: $page) { page { handle } userErrors { field message } } }'
    for route in ROUTES:
        if not route.startswith('/pages/'):
            continue
        handle = route.split('/')[-1]
        if handle in existing or handle in LEGAL_HANDLES:
            continue
        blocks = CONTENT.get(route, [])
        title = next((b['text'] for b in blocks if b['tag'] == 'h1'), title_case(handle))
        result = execute(create, {'page': {'handle': handle, 'title': title, 'body': body_for(route), 'isPublished': True}}, mutation=True)['pageCreate']
        if result['userErrors']:
            print('PAGE ERROR', handle, result['userErrors'], flush=True)
        else:
            print('PAGE', handle, flush=True)


def sync_collections():
    query = 'query { collections(first: 250) { nodes { handle } } }'
    existing = {node['handle'] for node in execute(query)['collections']['nodes']}
    create = 'mutation($collection: CollectionCreateInput!) { collectionCreate(collection: $collection) { collection { handle } userErrors { field message } } }'
    for route in ROUTES:
        if not route.startswith('/collections/'):
            continue
        handle = route.split('/')[-1]
        if handle in existing:
            continue
        result = execute(create, {'collection': {'handle': handle, 'title': title_case(handle)}}, mutation=True)['collectionCreate']
        if result['userErrors']:
            print('COLLECTION ERROR', handle, result['userErrors'], flush=True)
        else:
            print('COLLECTION', handle, flush=True)


def sync_blog():
    query = 'query { blogs(first: 25) { nodes { id handle articles(first: 100) { nodes { handle } } } } }'
    blogs = {node['handle']: node for node in execute(query)['blogs']['nodes']}
    blog = blogs.get('news')
    if not blog:
        create_blog = 'mutation($blog: BlogCreateInput!) { blogCreate(blog: $blog) { blog { id handle } userErrors { field message } } }'
        result = execute(create_blog, {'blog': {'handle': 'news', 'title': 'May Smokes News'}}, mutation=True)['blogCreate']
        if result['userErrors']:
            raise RuntimeError(result['userErrors'])
        blog = result['blog']
        blog['articles'] = {'nodes': []}
    existing = {node['handle'] for node in blog['articles']['nodes']}
    create = 'mutation($article: ArticleCreateInput!) { articleCreate(article: $article) { article { handle } userErrors { field message } } }'
    for route in ROUTES:
        if not route.startswith('/blogs/news/'):
            continue
        handle = route.split('/')[-1]
        if handle in existing:
            continue
        blocks = CONTENT.get(route, [])
        title = next((b['text'] for b in blocks if b['tag'] == 'h1'), title_case(handle))
        article = {'blogId': blog['id'], 'handle': handle, 'title': title,
                   'author': {'name': 'May Smokes'}, 'body': body_for(route), 'isPublished': True}
        result = execute(create, {'article': article}, mutation=True)['articleCreate']
        if result['userErrors']:
            print('ARTICLE ERROR', handle, result['userErrors'], flush=True)
        else:
            print('ARTICLE', handle, flush=True)


if __name__ == '__main__':
    sync_pages()
    sync_collections()
    sync_blog()
