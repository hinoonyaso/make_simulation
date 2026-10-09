const { spawn, spawnSync } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');

const projectRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(projectRoot, '../..');
const port = Number(process.env.V10_THREE_PORT || 8767);
const duration = Number(process.env.V10_THREE_DURATION || 8);
const fps = Number(process.env.V10_THREE_FPS || 30);
const out = path.resolve(process.env.V10_THREE_VIDEO || path.join(projectRoot, 'output/threejs_rag_3d.mp4'));
const projectionPath = path.resolve(process.env.V10_THREE_PROJECTION || path.join(projectRoot, 'data/embedding_space_3d.json'));
const projectionUrl = '/' + path.relative(repoRoot, projectionPath).split(path.sep).join('/');
const pageUrl = `http://127.0.0.1:${port}/pilots/v10_threejs_rag/index.html?capture=1&duration=${duration}&projection=${encodeURIComponent(projectionUrl)}`;
const frameDir = fs.mkdtempSync(path.join(os.tmpdir(), 'threejs-rag-frames-'));
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'],
  { cwd: repoRoot, stdio: 'ignore' });
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
  let browser;
  try {
    fs.mkdirSync(path.dirname(out), { recursive: true });
    let ready = false;
    for (let i = 0; i < 50; i++) {
      try { if ((await fetch(`http://127.0.0.1:${port}/pilots/v10_threejs_rag/`)).ok) { ready = true; break; } }
      catch (_) { await sleep(100); }
    }
    if (!ready) throw new Error('local static server did not start');
    browser = await chromium.launch({ headless: true,
      args: ['--use-gl=angle', '--use-angle=swiftshader'] });
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') pageErrors.push(message.text()); });
    page.on('requestfailed', request => pageErrors.push(`${request.url()}: ${request.failure()?.errorText}`));
    const pageResponse = await page.goto(pageUrl, { waitUntil: 'networkidle' });
    if (!pageResponse?.ok()) throw new Error(`3D view returned HTTP ${pageResponse?.status()}: ${pageUrl}`);
    try {
      await page.waitForFunction(() => window.__dataReady === true, null, { timeout: 30000 });
    } catch (error) {
      throw new Error(`3D projection did not load (${pageUrl}): ${pageErrors.join(' | ') || error.message}`);
    }
    const totalFrames = Math.round(duration * fps);
    for (let i = 0; i < totalFrames; i++) {
      await page.evaluate(t => window.setFrame(t), i / fps);
      await page.screenshot({ path: path.join(frameDir, `frame_${String(i).padStart(5, '0')}.png`) });
    }
    await browser.close(); browser = null;
    const ffmpeg = spawnSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(fps), '-i',
      path.join(frameDir, 'frame_%05d.png'), '-frames:v', String(totalFrames), '-an',
      '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
      '-movflags', '+faststart', out], { stdio: 'inherit' });
    if (ffmpeg.status !== 0) throw new Error(`ffmpeg exited with ${ffmpeg.status}`);
    const projectionData = JSON.parse(fs.readFileSync(projectionPath, 'utf8'));
    const sceneHash = crypto.createHash('sha256');
    for (const relative of ['index.html', 'src/main.js', 'src/style.css',
      'scripts/build_projection.py', 'scripts/capture_video.js', 'package-lock.json']) {
      sceneHash.update(relative); sceneHash.update(fs.readFileSync(path.join(projectRoot, relative)));
    }
    fs.writeFileSync(out.replace(/\.mp4$/, '.manifest.json'), JSON.stringify({
      schema: 'v10-rag-embedding-video/v1', trace_id: projectionData.trace_id,
      query_id: projectionData.query_id, source_trace_sha256: projectionData.source_trace_sha256,
      scene_sha256: sceneHash.digest('hex'),
      chunk_ids: projectionData.points.filter(point => point.kind === 'chunk').map(point => point.id),
      retrieval: projectionData.retrieval, duration_sec: duration, fps,
      width: 1920, height: 1080, audio: false,
      render_options: {duration, fps, width: 1920, height: 1080},
    }, null, 2) + '\n');
    console.log(`${out} (${fs.statSync(out).size} bytes; ${duration}s, 1080p${fps}, no audio)`);
  } finally {
    if (browser) await browser.close();
    server.kill('SIGTERM');
    fs.rmSync(frameDir, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exit(1); });
