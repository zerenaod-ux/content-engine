// Renders a scene spec frame by frame with the scene engine.  node scene_lib/render.js <spec.json> [json list of sample frames]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  let spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')), only = process.argv[3] ? new Set(JSON.parse(process.argv[3])) : null;
  const b = await chromium.launch(process.env.CHROME_CHANNEL ? { channel: process.env.CHROME_CHANNEL } : {});
  const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
  let bad = 0; p.on('pageerror', e => { bad++; console.log('PAGEERR', e.message); });
  await p.goto('file://' + path.join(__dirname, 'scene.html'));
  if (spec.evidence_version === 1) {
    // The browser understands all SVG commands, including arcs and curves.
    // Measure the path instead of assuming every path is centred at (0,0).
    const bounds = await p.evaluate(parts => {
      const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg');
      document.body.appendChild(svg); const out = {};
      for (const part of parts.filter(q => q.type === 'path')) {
        const el = document.createElementNS(ns, 'path'); el.setAttribute('d', part.d); svg.appendChild(el);
        const b = el.getBBox(); out[part.d] = [b.x,b.y,b.width,b.height]; el.remove();
      }
      svg.remove(); return out;
    }, spec.parts);
    const cp = require('child_process').spawnSync(process.env.PYTHON || 'python3',
      [path.join(__dirname,'prepare.py'), process.argv[2]], {input:JSON.stringify(bounds),encoding:'utf8'});
    if (cp.status !== 0) throw new Error('camera preparation failed: ' + cp.stderr);
    spec = JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
  }
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
        const words = String(f).toLowerCase().split(/\s+/).filter(Boolean);
        for (const q of [f, words.filter(w => w !== 'icon').join(' '), words[words.length - 1], words[0]].filter((v, i, a) => v && a.indexOf(v) === i)) { if (file) break;
        try {
          const r = await fetch('https://api.iconify.design/search?limit=12&prefixes=' + SETS + '&query=' + encodeURIComponent(q));
          const hits = ((await r.json()).icons || []); console.log('icon search', JSON.stringify(q), r.status, hits.slice(0, 3).join(' '));
          const key = String(q).toLowerCase().split(/[^a-z]+/).filter(w => w.length > 2 && !['icon', 'the', 'and', 'with'].includes(w));
          for (const h of hits) {
            const [pre, name] = h.split(':');
            if (!key.some(w => name.includes(w.replace(/s$/, '')))) continue;   /* RIGHT_PICTURE: the picture's own name must contain the word asked for (no cup for "wind") */ const sv = await fetch('https://api.iconify.design/' + pre + '/' + name + '.svg?height=512');
            if (sv.ok) { const txt = await sv.text(); if (txt.startsWith('<svg')) { file = pre + '--' + name + '.svg'; fs.writeFileSync(path.join(dir, file), txt); break; } }
          }
        } catch (e) { console.log('icon lookup failed for', q, String(e).slice(0, 120)); } }
        if (file) known[f] = file;
      }
      if (file) map[f] = 'data:image/svg+xml;base64,' + fs.readFileSync(path.join(dir, file)).toString('base64'); else missing.push(f);
    }
    fs.writeFileSync(idx, JSON.stringify(known, null, 1));
    await p.evaluate(m => window.loadIcons(m), map);
    if (missing.length) {   // no right picture: leave that part out instead of showing a wrong one
      console.log('ICON NOT FOUND (left out): ' + missing.join(' | '));
      const stars = new Set(spec.steps.map(st => st.shows)); const lost = spec.parts.filter(q => q.type === 'icon' && missing.includes(q.find) && stars.has(q.id));
      if (lost.length) { console.log('NO VIDEO: the main picture of a step could not be found (' + lost.map(q => q.find).join(', ') + '); better no video than an empty one'); await b.close(); process.exit(4); }
      spec.parts = spec.parts.filter(q => !(q.type === 'icon' && missing.includes(q.find))); await p.evaluate(s => window.loadSpec(s), spec);
    }
  }
  fs.mkdirSync('fr', { recursive: true });
  for (let f = 0; f < total; f++) {
    if (only && !only.has(f)) continue;
    const d = await p.evaluate(i => window.frame(i), f);
    fs.writeFileSync(path.join('fr', String(f).padStart(4, '0') + '.jpg'), Buffer.from(d.split(',')[1], 'base64'));
    if (f % 200 === 0) console.log('frame', f, '/', total);
  }
  // Render actual/part-removed pairs at both contract endpoints. Difference
  // measures a part's visible contribution in the final composition, even if
  // another object covers it. It does not interpret what the drawing means.
  if (spec.evidence_version === 1) {
    const dir = 'fr/evidence'; fs.mkdirSync(dir, { recursive: true });
    const manifest = [];
    for (const [i, step] of spec.steps.entries()) {
      const requirements=[...(step.evidence||[])], declared=new Set(requirements.map(e=>e.part));
      for (const group of (step.contrasts||[])) for (const id of group.parts) if(!declared.has(id)){requirements.push({part:id,field:'contrast',at:[step.start,step.end]});declared.add(id)}
      for (const [j, ev] of requirements.entries()) {
        const files = [];
        for (const [k, t] of ev.at.entries()) {
          const f = Math.round(t * 30), base = `${i}-${j}-${k}`;
          await p.evaluate(s => window.loadSpec(s), spec);
          const actual = await p.evaluate(n => window.frame(n), f);
          const hidden = {...spec, parts: spec.parts.filter(q => q.id !== ev.part)};
          await p.evaluate(s => window.loadSpec(s), hidden);
          const removed = await p.evaluate(n => window.frame(n), f);
          for (const [name, data] of [['actual', actual], ['removed', removed]]) {
            fs.writeFileSync(`${dir}/${base}-${name}.jpg`, Buffer.from(data.split(',')[1], 'base64'));
          }
          files.push(base);
        }
        manifest.push({step: i + 1, part: ev.part, field: ev.field, files});
      }
    }
    fs.writeFileSync(`${dir}/manifest.json`, JSON.stringify(manifest));
  }
  const pe = await p.evaluate(() => [window.partErrors || 0, window.partErrorMsg || '']);
  if (pe[0]) console.log('PART SKIPPED ' + pe[0] + ' times (first: ' + pe[1] + ')');
  await b.close();
  if (bad || pe[0]) process.exit(1);
})();
