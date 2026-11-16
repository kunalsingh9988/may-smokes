import {defineConfig} from 'vite';
import {readFileSync, writeFileSync} from 'node:fs';

export default defineConfig({
  publicDir: false,
  define: {'process.env.NODE_ENV': JSON.stringify('production')},
  plugins: [{
    name: 'normalize-generated-whitespace',
    closeBundle() {
      const file = 'shopify-theme/assets/may-storefront.js';
      writeFileSync(file, readFileSync(file, 'utf8').replace(/[ \t]+$/gm, ''));
    },
  }],
  build: {
    outDir: 'shopify-theme/assets',
    emptyOutDir: false,
    lib: {entry: 'src/main.jsx', formats: ['iife'], name: 'MaySmokes'},
    rollupOptions: {output: {entryFileNames: 'may-storefront.js', assetFileNames: 'may-storefront.[ext]'}},
  },
});
