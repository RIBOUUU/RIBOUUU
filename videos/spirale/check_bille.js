// Verifie que la bille reste bien dans l'image a chaque instant (coordonnees ecran -1..1)
const http = require('http'), fs = require('fs'), path = require('path'); const { chromium } = require('playwright');
const srv = http.createServer((q, r) => { const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/json' }); r.end(d); } }); })
.listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 270, height: 480 } });
  await p.goto(`http://localhost:${srv.address().port}/${process.env.SCENE || 'blocs10.html'}?capture${process.env.QS || ''}&w=270&h=480`);
  await p.waitForFunction('window.READY === true');
  const end = await p.evaluate('window.END'), off = await p.evaluate('window.OFF || 0'); const bad = [];
  for (let f = 0; f < Math.ceil(end * 30); f++) { const [x, y, z] = await p.evaluate(t => window.ballNDC(t), off + f / 30);
    if (Math.abs(x) > 0.8 || Math.abs(y) > 0.8 || z > 1) bad.push(`${f}:${x.toFixed(2)},${y.toFixed(2)}`); }
  console.log('hors cadre :', bad.length, bad.slice(0, 40).join(' ')); await b.close(); srv.close();
});
