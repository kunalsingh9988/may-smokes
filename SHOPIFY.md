# May Smokes Shopify storefront

The `shopify-theme/` folder is the pulled Horizon theme for `may-smokes.myshopify.com`, theme ID `161953710251` (unpublished). The live theme was not edited.

## Build and upload

```sh
npx vite build --config vite.shopify.config.js
shopify theme push --environment horizon --path shopify-theme --nodelete
```

The build writes `may-storefront.js` and `may-storefront.css` to the theme assets folder. It keeps the original Horizon markup available through the **Show May Smokes storefront** theme setting. The theme uses the Vite site's saved data and image assets, while product/cart actions use Shopify storefront endpoints.

## Store records

The scripts under `tools/` use the Shopify CLI Connector App's Admin API session. They create content, provisional products, and collection membership in the **store**, so their changes are visible to every theme. Run them only against the confirmed May Smokes store:

```sh
python3 tools/sync_shopify_content.py
python3 tools/sync_shopify_products.py
python3 tools/sync_shopify_collections.py
python3 tools/sync_shopify_branding.py
```

Provisional catalog entries have a single Standard variant at the saved first price. Alien ET THCa Flower has the five sizes from its Figma frame. The saved source catalog does not contain full variant or inventory data; replace provisional records with an approved export before launch. Five policy pages are unpublished placeholders pending approved May Smokes legal copy.

Draft preview: https://may-smokes.myshopify.com/?preview_theme_id=161953710251 (password protected).
