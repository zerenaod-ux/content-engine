// Renders a scene spec frame by frame with the scene engine.  node scene_lib/render.js <spec.json> [json list of sample frames]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')), only = process.argv[3] ? new Set(JSON.parse(process.argv[3])) : null;
  const b = await chromium.launch(process.env.CHROME_CHANNEL ? { channel: process.env.CHROME_CHANNEL } : {});
  const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
  let bad = 0; p.on('pageerror', e => { bad++; console.log('PAGEERR', e.message); });
  await p.goto('file://' + path.join(__dirname, 'scene.html'));
  const total = await p.evaluate(s => window.loadSpec(s), spec);
  // emoji pictures: use the machine's emoji font, or the bundled free one (Noto Color Emoji) if the machine has none
  const chars = [...new Set(spec.parts.filter(q => q.type === 'emoji').map(q => q.char))];
  if (chars.length) {
    let badE = await p.evaluate(c => window.emojiOK(c), chars);
    const css = path.resolve('node_modules/@fontsource/noto-color-emoji/index.css');
    if (badE.length && fs.existsSync(css)) {
      await p.addStyleTag({ url: 'file://' + css });
      await p.evaluate(async c => { await Promise.all(c.map(ch => document.fonts.load('48px "Noto Color Emoji"', ch))); }, chars);
      badE = await p.evaluate(c => window.emojiOK(c), chars);
    }
    if (badE.length) { console.log('EMOJI NOT DRAWABLE: ' + badE.join(' ')); await b.close(); process.exit(3); }
  }
  fs.mkdirSync('fr', { recursive: true });
  for (let f = 0; f < total; f++) {
    if (only && !only.has(f)) continue;
    const d = await p.evaluate(i => window.frame(i), f);
    fs.writeFileSync(path.join('fr', String(f).padStart(4, '0') + '.jpg'), Buffer.from(d.split(',')[1], 'base64'));
    if (f % 200 === 0) console.log('frame', f, '/', total);
  }
  const pe = await p.evaluate(() => [window.partErrors || 0, window.partErrorMsg || '']);
  if (pe[0]) console.log('PART SKIPPED ' + pe[0] + ' times (first: ' + pe[1] + ')');
  await b.close();
  if (bad) process.exit(1);
})();
