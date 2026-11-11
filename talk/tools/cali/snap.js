// Screenshots of every slide of the HTML deck, to review it without opening a browser.
//   node snap.js ../../techdaycali.html <out-dir>      → <out-dir>/NN-<id>.png (1920 × 1080)
// Needs Google Chrome (CHROME=… to point at another one).
const {chromium} = require('playwright-core');
const fs = require('fs'), path = require('path');
const [,, DECK, OUT] = process.argv;
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

(async () => {
  fs.mkdirSync(OUT, {recursive: true});
  const b = await chromium.launch({executablePath: CHROME});
  const p = await b.newPage({viewport: {width: 960, height: 540}, deviceScaleFactor: 2});
  await p.goto('file://' + path.resolve(DECK));
  await p.evaluate(() => document.fonts.ready);
  const n = await p.evaluate(() => window.__deck.slides.length);
  for (let k = 0; k < n; k++) {
    const id = await p.evaluate(k => { window.__deck.show(k); return window.__deck.slides[k].dataset.id; }, k);
    await p.waitForTimeout(450);                       // the fade between slides
    await p.screenshot({path: path.join(OUT, `${String(k + 1).padStart(2, '0')}-${id}.png`)});
  }
  console.log(`✔ ${n} slides in ${OUT}`);
  await b.close();
})();
