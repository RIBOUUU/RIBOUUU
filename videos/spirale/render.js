// Rend scene.html (ou la page SCENE=...) image par image (Chromium headless) -> frames/NNNN.jpg
// Usage : node render.js [fps] [w] [h] [t1,t2,... | debut-fin]  (liste de temps = apercu, debut-fin = tranche d'images)
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const [fps = 30, w = 1080, h = 1920, only] = process.argv.slice(2);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const srv = http.createServer((q, r) => {
  const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); } });
}).listen(0, async () => {
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: +w, height: +h } });
  page.on('console', m => console.log('[page]', m.text())); page.on('pageerror', e => console.log('[err]', e.message));
  await page.goto(`http://localhost:${port}/${process.env.SCENE || 'scene.html'}?capture${process.env.QS || ''}&w=${w}&h=${h}`);
  await page.waitForFunction('window.READY === true', null, { timeout: 120000 });
  const end = await page.evaluate('window.END');
  const range = only && only.includes('-') ? only.split('-').map(Number) : null;
  const preview = only && !range;
  const out = path.join(__dirname, preview ? 'preview' : 'frames'); fs.mkdirSync(out, { recursive: true });
  const nAll = Math.ceil(end * fps - 1e-6);
  const idx = preview ? null : [...Array(nAll).keys()].filter(i => !range || (i >= range[0] && i < range[1]));
  const off = await page.evaluate('window.OFF || 0');
  const times = preview ? only.split(',').map(Number) : idx.map(i => off + i / fps);
  const t0 = Date.now();
  for (let i = 0; i < times.length; i++) {
    const url = await page.evaluate(t => window.renderAt(t), times[i]);
    fs.writeFileSync(path.join(out, preview ? `t${times[i]}.jpg` : String(idx[i]).padStart(4, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
    if (i % 30 === 0) console.log(`${i}/${times.length}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await browser.close(); srv.close();
});
