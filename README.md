# May Smokes

Responsive React/Vite storefront replica based on the supplied Figma homepage, shop, and product frames. The site uses a May Smokes logo and edited hero and preroll product artwork.

## Run locally

```sh
npm install
npm run dev
```

Build with `npm run build`.

The reference sitemap supplies the route list. Product and collection data are snapshots gathered from the public Bay Smokes catalog on November 6, 2026. The three Figma layouts have tailored responsive components; other routes use shared collection, product, and content templates. Cart actions are local browser state, and checkout and contact submissions are disabled.

## Refresh reference data

```sh
python3 build_catalog.py
python3 build_collections.py
python3 build_content.py
python3 build_sitemap.py
```
