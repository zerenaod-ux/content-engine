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
  // free pictures: every "icon" part names what it shows ("find"); look it up in open-licensed sets on Iconify, keep a copy in data/icons/ (so the system depends on the service less over time)
  const finds = [...new Set(spec.parts.filter(q => q.type === 'icon').map(q => q.find))];
  if (finds.length) {
    const dir = path.join(__dirname, '..', 'data', 'icons'); fs.mkdirSync(dir, { recursive: true });
    const idx = path.join(dir, 'index.json'); let known = {}; try { known = JSON.parse(fs.readFileSync(idx, 'utf8')); } catch (e) {}
    const SETS = 'fluent-emoji-flat,noto,twemoji,openmoji,flat-color-icons';   // licences: MIT, Apache-2.0, CC-BY-4.0, CC-BY-SA-4.0, MIT (credits in data/icons/CREDITS.md)
    const map = {}, missing = [];
    for (const f of finds) {
      let file = known[f];
      if (!file || !fs.existsSync(path.join(dir, file))) {
        file = null;
        try {
          const r = await fetch('https://api.iconify.design/search?limit=12&prefixes=' + SETS + '&query=' + encodeURIComponent(f));
          const hits = ((await r.json()).icons || []);
          for (const h of hits) {
            const [pre, name] = h.split(':'); const sv = await fetch('https://api.iconify.design/' + pre + '/' + name + '.svg?height=512');
            if (sv.ok) { const txt = await sv.text(); if (txt.startsWith('<svg')) { file = pre + '--' + name + '.svg'; fs.writeFileSync(path.join(dir, file), txt); break; } }
          }
        } catch (e) { console.log('icon lookup failed for', f, String(e).slice(0, 80)); }
        if (file) known[f] = file;
      }
      if (file) map[f] = 'data:image/svg+xml;base64,' + fs.readFileSync(path.join(dir, file)).toString('base64'); else missing.push(f);
    }
    fs.writeFileSync(idx, JSON.stringify(known, null, 1));
    await p.evaluate(m => window.loadIcons(m), map);
    if (missing.length) { console.log('ICON NOT FOUND: ' + missing.join(' | ')); await b.close(); process.exit(4); }
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
