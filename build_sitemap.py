import json
from pathlib import Path
from xml.sax.saxutils import escape
root=Path(__file__).parent
paths=['/','/collections']+json.loads((root/'src/routes.json').read_text())
origin='https://may-smokes.vercel.app'
xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
xml+=''.join(f'  <url><loc>{escape(origin+path)}</loc></url>\n' for path in dict.fromkeys(paths))
xml+='</urlset>\n'
(root/'public/sitemap.xml').write_text(xml)
(root/'public/robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+origin+'/sitemap.xml\n')
