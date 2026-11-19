// Captures talk/techdaycali.html click by click for the PowerPoint version (build_pptx_cali.py).
// One entry per click: a 2x JPEG of the final state, and for the steps that move (the canvas charts, the
// architectures with packets, the station's acts) the frames of that click as Chrome paints them
// (DevTools screencast), with their timestamps, so ffmpeg can rebuild the motion at its real pace.
//   node capture_cali.js <deck.html> <out dir>
const {chromium} = require('../cali/node_modules/playwright-core');
const fs = require('fs'), path = require('path');
const [, , DECK, OUT] = process.argv;
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

(async () => {
  fs.mkdirSync(OUT, {recursive: true});
  const b = await chromium.launch({executablePath: CHROME});
  const ctx = await b.newContext({viewport: {width: 1920, height: 1080}, deviceScaleFactor: 2});
  const p = await ctx.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + path.resolve(DECK)); await p.waitForTimeout(1500);
  // no slide-to-slide fade in the capture: PowerPoint does that transition
  await p.addStyleTag({content: '.s{transition:none !important}'});
  const cdp = await ctx.newCDPSession(p);
  const order = await p.evaluate(() => { const S = window.__deck.slides, main = [], anx = [];
    S.forEach((s, k) => (s.dataset.annex ? anx : main).push(k)); return main.concat(anx); });
  const man = [];
  for (const k of order) {
    const info = await p.evaluate(k => { const s = window.__deck.slides[k];
      return {id: s.dataset.id, n: window.__deck.S[k].n, notes: s.dataset.notes || '', annex: !!s.dataset.annex,
              station: s.classList.contains('st'), console: s.classList.contains('cn'), canvas: !!s.querySelector('canvas.anim')}; }, k);
    for (let st = 0; st < info.n; st++) {
      // record from the click on, so the motion of that click is in the video
      let frames = [], rec = info.station || info.canvas;
      const onFrame = async ev => { frames.push({ts: ev.metadata.timestamp, data: ev.data});
        try { await cdp.send('Page.screencastFrameAck', {sessionId: ev.sessionId}); } catch (e) {} };
      if (rec) { cdp.on('Page.screencastFrame', onFrame);
        await cdp.send('Page.startScreencast', {format: 'jpeg', quality: 88, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1}); }
      if (st === 0) await p.evaluate(k => window.__deck.show(k), k); else await p.evaluate(() => window.__deck.next());
      const pk = await p.evaluate(k => (window.__deck.slides[k]._pk || []).length, k);
      if (!rec && pk) { rec = true; cdp.on('Page.screencastFrame', onFrame);
        await cdp.send('Page.startScreencast', {format: 'jpeg', quality: 88, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1}); }
      if (info.station) {                       // until the replay waits for the next click (max 30 s)
        const fr = await (await p.$(`section[data-id="${info.id}"] iframe.stn`)).contentFrame();
        const t0 = Date.now(); await p.waitForTimeout(1500);
        while (Date.now() - t0 < 30000) { const pl = await fr.evaluate(() => document.querySelector('#play').textContent);
          if (pl === '▶') break; await p.waitForTimeout(250); }
        await p.waitForTimeout(500);
      } else if (info.canvas) await p.waitForTimeout(3200);
      else if (pk) await p.waitForTimeout(3000);
      else await p.waitForTimeout(info.console && st === 0 ? 2600 : 900);
      if (rec) { await cdp.send('Page.stopScreencast'); cdp.off('Page.screencastFrame', onFrame); }
      const base = `${String(man.length + 1).padStart(3, '0')}-${info.id}-${st}`;
      await p.screenshot({path: path.join(OUT, base + '.jpg'), type: 'jpeg', quality: 92});
      const e = {file: base + '.jpg', id: info.id, step: st, annex: info.annex, notes: st === 0 ? info.notes : ''};
      if (rec && frames.length > 1) {
        const dir = path.join(OUT, base); fs.mkdirSync(dir, {recursive: true});
        frames.forEach((f, j) => fs.writeFileSync(path.join(dir, String(j).padStart(5, '0') + '.jpg'), Buffer.from(f.data, 'base64')));
        e.frames = base; e.ts = frames.map(f => f.ts);
      }
      man.push(e); process.stdout.write(`${base}${e.frames ? ' · ' + frames.length + ' frames' : ''}\n`);
    }
  }
  fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(man, null, 1));
  console.log('clicks:', man.length, '· errors:', errs.length ? errs.join(' | ') : 'none');
  await b.close();
})();
