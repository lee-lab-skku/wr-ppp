#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const editor = fs.readFileSync(path.join(__dirname, '..', 'assets', 'editor.html'), 'utf8');
const helpers = editor.slice(editor.indexOf('  function escapeHtml'), editor.indexOf('  function mdToHtml'));
global.window = {};
eval(helpers);

const rendered = inlineMd(String.raw`A \qty{200}{\micro\meter} gap, \num{1.71}, \qtyrange{53.7}{59.8}{\micro\meter}, \qtylist{10;3000}{\micro\meter}, \qty{1269}{ms}, and $D_p=\qty{41.8}{\micro\meter}$.`);
for(const expected of ['200 µm', '1.71', '53.7–59.8 µm', '10, 3,000 µm', '1,269 ms', 'D_p=41.8\\,\\text{µm}']){
  if(!rendered.includes(expected)) throw new Error(`missing ${expected}: ${rendered}`);
}
for(const raw of ['\\qty{', '\\qtyrange{', '\\qtylist{', '\\num{']){
  if(rendered.includes(raw)) throw new Error(`unrendered ${raw}: ${rendered}`);
}
console.log('ok: siunitx text and math commands render');
