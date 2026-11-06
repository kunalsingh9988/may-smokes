import json
import re
from pathlib import Path
from urllib.request import urlopen, Request
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

root=Path(__file__).parent
routes=json.loads((root/'src/routes.json').read_text())
paths=[r for r in routes if r.startswith('/pages/') or r.startswith('/blogs/')]

def read(path):
    req=Request('https://baysmokes.com'+path,headers={'User-Agent':'Mozilla/5.0'})
    html=urlopen(req,timeout=25).read()
    soup=BeautifulSoup(html,'html.parser')
    main=soup.find('main')
    if not main:return path,[]
    for el in main.find_all(['script','style','nav','form','noscript','button']):
        el.decompose()
    blocks=[];seen=set()
    for el in main.find_all(['h1','h2','h3','p','li']):
        if el.find_parent(['h1','h2','h3','p','li']):continue
        text=re.sub(r'\s+',' ',el.get_text(' ',strip=True))
        text=re.sub('Bay Smokes','May Smokes',text,flags=re.I)
        if not 15<=len(text)<=1500 or text in seen:continue
        if any(x in text.lower() for x in ['add to cart','shop all','verified buyer','subscribe to our newsletter']):continue
        seen.add(text)
        blocks.append({'tag':el.name,'text':text})
        if len(blocks)>=100:break
    return path,blocks

content={}
with ThreadPoolExecutor(max_workers=10) as pool:
    futures=[pool.submit(read,p) for p in paths]
    for f in as_completed(futures):
        try:
            path,blocks=f.result();content[path]=blocks
            print(path,len(blocks))
        except Exception as error:print('ERROR',error)
(root/'src/content.json').write_text(json.dumps(content,separators=(',',':')))
