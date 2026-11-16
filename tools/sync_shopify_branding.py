#!/usr/bin/env python3
"""Refresh Shopify page/article bodies after the May Smokes branding pass."""

from sync_shopify_content import CONTENT, body_for, execute

POLICIES = {'privacy-policy', 'refund-policy', 'shipping-policy', 'subscription-policy', 'terms-of-service'}


def batches(items, size=10):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def title_for(route, fallback):
    return next((block['text'] for block in CONTENT.get(route, []) if block['tag'] == 'h1'), fallback)


def update_pages():
    pages = execute('query { pages(first:100) { nodes { id handle title } } }')['pages']['nodes']
    targets = [page for page in pages if '/pages/' + page['handle'] in CONTENT and page['handle'] not in POLICIES]
    for batch in batches(targets):
        definitions = ','.join(f'$id{i}:ID!,$page{i}:PageUpdateInput!' for i in range(len(batch)))
        fields = ''.join(f'p{i}:pageUpdate(id:$id{i},page:$page{i}){{page{{handle}}userErrors{{field message}}}}'
                         for i in range(len(batch)))
        variables = {}
        for i, page in enumerate(batch):
            route = '/pages/' + page['handle']
            variables[f'id{i}'] = page['id']
            variables[f'page{i}'] = {'title': title_for(route, page['title']), 'body': body_for(route)}
        result = execute(f'mutation({definitions}){{{fields}}}', variables, mutation=True)
        for i, page in enumerate(batch):
            print('PAGE UPDATE', page['handle'], result[f'p{i}']['userErrors'], flush=True)


def update_articles():
    blogs = execute('query { blogs(first:10) { nodes { handle articles(first:100) { nodes { id handle title } } } } }')['blogs']['nodes']
    news = next(blog for blog in blogs if blog['handle'] == 'news')
    targets = [article for article in news['articles']['nodes'] if '/blogs/news/' + article['handle'] in CONTENT]
    for batch in batches(targets):
        definitions = ','.join(f'$id{i}:ID!,$article{i}:ArticleUpdateInput!' for i in range(len(batch)))
        fields = ''.join(f'a{i}:articleUpdate(id:$id{i},article:$article{i}){{article{{handle}}userErrors{{field message}}}}'
                         for i in range(len(batch)))
        variables = {}
        for i, article in enumerate(batch):
            route = '/blogs/news/' + article['handle']
            variables[f'id{i}'] = article['id']
            variables[f'article{i}'] = {'title': title_for(route, article['title']), 'body': body_for(route)}
        result = execute(f'mutation({definitions}){{{fields}}}', variables, mutation=True)
        for i, article in enumerate(batch):
            print('ARTICLE UPDATE', article['handle'], result[f'a{i}']['userErrors'], flush=True)


if __name__ == '__main__':
    update_pages()
    update_articles()
