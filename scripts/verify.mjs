import {readFileSync,existsSync} from 'node:fs';
import assert from 'node:assert/strict';
const html=readFileSync('dist/index.html','utf8');
const js=readFileSync('dist/app.js','utf8');
for (const match of html.matchAll(/(?:href|src)="([^"]*)"/g)) {
    assert(!/[<>]/.test(match[1]), `Invalid asset/link attribute: ${match[1]}`);
}
assert(/<link rel="stylesheet" href="style\.css(?:\?[^"<>]*)?">/.test(html), 'Base stylesheet markup is invalid');
assert(/<script src="app\.js(?:\?[^"<>]*)?"><\/script>/.test(html), 'Storefront script markup is invalid');
for(const file of ['dist/style.css','dist/app.js'])assert(existsSync(file));
for(const id of ['app','count','toast','searchbar','search','search-toggle'])assert(html.includes(`id="${id}"`),`Missing DOM target ${id}`);
for(const route of ['coffee','tea','edible-oils','about','brands','contact','cart','checkout','account','orders','wishlist','privacy','terms','shipping','returns'])assert(js.includes(`'${route}'`)||js.includes(`${route}:`),`Missing route ${route}`);
for(const fact of ['05AUSPC5607K1ZG','poojachhetri2588@gmail.com','248003'])assert((html+js).includes(fact),`Missing company fact ${fact}`);
assert(js.includes('No order has been placed.'));
console.log('Static assets, page routes, company facts and enquiry contract verified.');
