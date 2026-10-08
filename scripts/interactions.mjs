import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const elements=new Map(),events={},windowEvents={},storage=new Map();
function element(id){if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',value:'',hidden:true,classList:{add(){},remove(){}},addEventListener(t,f){this[t]=f},focus(){},setAttribute(){}});return elements.get(id)}
const context={document:{querySelector:element,addEventListener(t,f){events[t]=f}},location:{hash:'',href:''},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},window:{addEventListener:(t,f)=>windowEvents[t]=f,scrollTo(){}},setTimeout:()=>1,clearTimeout(){},console};
vm.createContext(context);vm.runInContext(readFileSync('dist/app.js','utf8'),context);
assert(element('#app').innerHTML.includes('Goodness for'));
events.click({target:{closest:s=>s==='[data-add],[data-buy]'?{dataset:{add:'ctc-tea'}}:null}});
assert.equal(element('#count').textContent,1);assert.equal(JSON.parse(storage.get('kedarmart-cart'))['ctc-tea'],1);
context.location.hash='#cart';windowEvents.hashchange();assert(element('#app').innerHTML.includes('Strong Premium CTC Tea'));
events.change({target:{dataset:{qty:'ctc-tea'},value:4}});assert.equal(element('#count').textContent,4);
const heart={dataset:{wish:'green-tea'},setAttribute(){}};
events.click({target:{closest:s=>s==='[data-wish]'?heart:null}});assert.equal(heart.textContent,'♥');
context.location.hash='#wishlist';windowEvents.hashchange();assert(element('#app').innerHTML.includes('Green Tea'));
element('#search').input({target:{value:'mustard'}});assert(element('#app').innerHTML.includes('Cold Pressed Mustard Oil'));assert(!element('#app').innerHTML.includes('Strong Premium CTC Tea'));
for(const route of ['shop','coffee','tea','edible-oils','product/instant-coffee','about','brands','contact','checkout','account','orders','privacy','terms','shipping','returns']){context.location.hash='#'+route;windowEvents.hashchange();assert(element('#app').innerHTML.length>100,route)}
context.location.hash='#cart';windowEvents.hashchange();events.click({target:{closest:s=>s==='[data-remove]'?{dataset:{remove:'ctc-tea'}}:null}});assert.equal(element('#count').textContent,0);assert(element('#app').innerHTML.includes('currently empty'));
console.log('Catalog search, all routes, cart persistence/quantity/removal and wishlist interactions passed.');
