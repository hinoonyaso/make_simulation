const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const out = path.join(root, 'output/threejs_rag_3d.mp4');
const port = Number(process.env.V10_THREE_PORT || 8767);
const frameDir = fs.mkdtempSync(path.join(os.tmpdir(), 'threejs-rag-frames-'));
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'],
  { cwd: root, stdio: 'ignore' });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
  let browser;
  try {
    fs.mkdirSync(path.dirname(out), { recursive: true });
    let ready = false;
    for (let i = 0; i < 50; i++) {
      try { if ((await fetch(`http://127.0.0.1:${port}/`)).ok) { ready = true; break; } }
      catch (_) { await sleep(100); }
    }
    if (!ready) throw new Error('local static server did not start');
    browser = await chromium.launch({ headless: true,
      args: ['--use-gl=angle', '--use-angle=swiftshader'] });
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    await page.goto(`http://127.0.0.1:${port}/?capture=1`, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.__dataReady === true, null, { timeout: 15000 });
    const totalFrames = 240;
    for (let i = 0; i < totalFrames; i++) {
      await page.evaluate(t => window.setFrame(t), i / 30);
      await page.screenshot({ path: path.join(frameDir, `frame_${String(i).padStart(5, '0')}.png`) });
    }
    await browser.close(); browser = null;
    const ffmpeg = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '30', '-i',
      path.join(frameDir, 'frame_%05d.png'), '-frames:v', String(totalFrames), '-an',
      '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
      '-movflags', '+faststart', out], { stdio: 'inherit' });
    if (ffmpeg.status !== 0) throw new Error(`ffmpeg exited with ${ffmpeg.status}`);
    console.log(`${out} (${fs.statSync(out).size} bytes; 8 sec, 1080p30, no audio)`);
  } finally {
    if (browser) await browser.close();
    server.kill('SIGTERM');
    fs.rmSync(frameDir, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exit(1); });
