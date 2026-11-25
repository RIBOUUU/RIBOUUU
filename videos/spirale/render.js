// Rend scene.html image par image (Chromium headless) -> frames/NNNN.jpg
// Usage : node render.js [fps] [w] [h] [t1,t2,...]   (liste de temps = apercu)
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
  await page.goto(`http://localhost:${port}/scene.html?capture&w=${w}&h=${h}`);
  await page.waitForFunction('window.READY === true', null, { timeout: 120000 });
  const end = await page.evaluate('window.END');
  const out = path.join(__dirname, only ? 'preview' : 'frames'); fs.mkdirSync(out, { recursive: true });
  const times = only ? only.split(',').map(Number) : [...Array(Math.ceil(end * fps)).keys()].map(i => i / fps);
  const t0 = Date.now();
  for (let i = 0; i < times.length; i++) {
    const url = await page.evaluate(t => window.renderAt(t), times[i]);
    fs.writeFileSync(path.join(out, only ? `t${times[i]}.jpg` : String(i).padStart(4, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
    if (i % 30 === 0) console.log(`${i}/${times.length}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await browser.close(); srv.close();
});
