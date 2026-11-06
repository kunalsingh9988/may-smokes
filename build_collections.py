import json
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed

root=Path(__file__).parent
routes=json.loads((root/'src/routes.json').read_text())
handles=[r.rsplit('/',1)[-1] for r in routes if r.startswith('/collections/')]

def fetch(handle):
    result=[]
    for page in range(1,5):
        url=f'https://baysmokes.com/collections/{handle}/products.json?limit=250&page={page}'
        data=json.loads(urlopen(url,timeout=25).read()).get('products',[])
        result.extend(p['handle'] for p in data)
        if len(data)<250:break
    return handle,result

data={}
with ThreadPoolExecutor(max_workers=8) as pool:
    futures=[pool.submit(fetch,h) for h in handles]
    for f in as_completed(futures):
        try:
            handle,items=f.result()
            data[handle]=items
            print(handle,len(items))
        except Exception as error:print('ERROR',error)
(root/'src/collections.json').write_text(json.dumps(data,separators=(',',':')))
