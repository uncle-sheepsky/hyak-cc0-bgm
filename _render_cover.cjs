const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path');
(async () => {
  const dir = __dirname;
  const html = pathToFileURL(path.join(dir, 'cover.html')).href;
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1280 }, deviceScaleFactor: 1 });
  await p.goto(html, { waitUntil: 'networkidle' });
  await p.screenshot({ path: path.join(dir, 'cover.png'), clip: { x:0, y:0, width:1280, height:1280 } });
  await b.close();
  console.log('[OK] cover.png');
})();
