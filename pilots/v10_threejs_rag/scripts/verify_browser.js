const { spawn } = require('node:child_process');
const { chromium } = require('playwright');

const root = require('node:path').resolve(__dirname, '..');
const port = Number(process.env.V10_THREE_PORT || 8766);
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'],
  { cwd: root, stdio: 'ignore' });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
  let browser;
  try {
    let ready = false;
    for (let i = 0; i < 50; i++) {
      try { if ((await fetch(`http://127.0.0.1:${port}/`)).ok) { ready = true; break; } }
      catch (_) { await sleep(100); }
    }
    if (!ready) throw new Error('local static server did not start');
    browser = await chromium.launch({ headless: true,
      args: ['--use-gl=angle', '--use-angle=swiftshader'] });
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(`http://127.0.0.1:${port}/?capture=1`, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.__dataReady === true, null, { timeout: 15000 });
    await page.evaluate(() => window.setFrame(1.2));
    const embedding = await page.evaluate(() => window.__renderStats);
    if (embedding.pointCount < 4 || embedding.pointCount >= 12 || embedding.queryVisible)
      throw new Error(`chunk embeddings were not progressively revealed: ${JSON.stringify(embedding)}`);
    await page.evaluate(() => window.setFrame(3.2));
    const query = await page.evaluate(() => window.__renderStats);
    if (!query.queryVisible || query.pointCount !== 12 || query.selectedIds.length !== 0)
      throw new Error(`query did not enter after chunk embeddings: ${JSON.stringify(query)}`);
    await page.evaluate(() => window.setFrame(7.9));
    await page.waitForTimeout(300);
    const stats = await page.evaluate(() => window.__renderStats);
    if (stats.pointCount !== 12 || stats.sourceDimension !== 384 || stats.displayDimension !== 3)
      throw new Error(`unexpected rendered dataset: ${JSON.stringify(stats)}`);
    if (stats.selectedIds.join(',') !== 'C08,C11,C07')
      throw new Error(`wrong selected IDs: ${stats.selectedIds.join(',')}`);
    const rankingText = await page.locator('#ranking').innerText();
    if (!rankingText.includes('C08 · d² 0.2307') || !rankingText.includes('C11 · d² 0.3707') ||
        !rankingText.includes('C07 · d² 0.3922'))
      throw new Error(`actual stored distance scores are missing: ${rankingText}`);
    if (!stats.drawCalls || stats.drawCalls < 1) throw new Error('WebGL did not draw scene calls');
    if (errors.length) throw new Error(`browser errors: ${errors.join(' | ')}`);
    await page.screenshot({ path: require('node:path').join(root, 'output/threejs_rag_smoke.png') });
    console.log(`PASS: progressive embeddings -> query -> actual 384D top3; points=${stats.pointCount}; top3=${stats.selectedIds.join(',')}; drawCalls=${stats.drawCalls}`);
  } finally {
    if (browser) await browser.close();
    server.kill('SIGTERM');
  }
})().catch(error => { console.error(error); process.exit(1); });
