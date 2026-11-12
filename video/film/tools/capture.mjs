// Records the real app for the film: crisp screenshots and deterministic 30 fps clips (the page clock is
// frozen and stepped 1/30 s per frame). Needs the app served (cd ../../frontend && npx vite preview --port 4174)
// and chromium. Plans are JSON: {gpu, width, height, scale, steps:[{nav}|{eval}|{wait}|{shot}|{vrec}|{rec}]}.
// Usage: node cap.mjs PLAN.json   — plan: {gpu, width, height, scale, steps:[...]}
// steps: {nav:url} {eval:js} {wait:ms} {shot:path, clip?:{x,y,width,height}, sel?:css, pad?:n}
//        {rec:dir, seconds:n}  (screencast frames with timestamps → dir/frames + dir/index.json)
import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
const plan = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const flags = ['--headless=new', '--no-sandbox', '--remote-debugging-port=9236', '--hide-scrollbars', '--autoplay-policy=no-user-gesture-required'];
if (plan.gpu) flags.push('--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--use-angle=vulkan', '--enable-features=Vulkan');
else flags.push('--use-angle=swiftshader', '--enable-unsafe-swiftshader');
const chrome = spawn('chromium', [...flags, 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets; for (let i = 0; i < 60; i++) { try { targets = await (await fetch('http://127.0.0.1:9236/json')).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl); await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map(); const logs = []; let frameSink = null;
let budgetDone = null;
ws.onmessage = (e) => { const m = JSON.parse(e.data);
  if (m.method === 'Emulation.virtualTimeBudgetExpired') { budgetDone?.(); budgetDone = null; }
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result ?? m.error); pending.delete(m.id); }
  if (m.method === 'Page.screencastFrame') { frameSink?.(m.params); send('Page.screencastFrameAck', { sessionId: m.params.sessionId }); }
  if (m.method === 'Runtime.exceptionThrown') logs.push('EXC ' + JSON.stringify(m.params.exceptionDetails).slice(0, 400));
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') logs.push('ERR ' + m.params.args.map((a) => a.value ?? a.description).join(' ').slice(0, 300)); };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send('Runtime.enable'); await send('Page.enable');
const W = plan.width || 1920, H = plan.height || 1080, SC = plan.scale || 1;
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: SC, mobile: false });
await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }, { name: 'prefers-reduced-motion', value: 'no-preference' }] });
await send('Page.addScriptToEvaluateOnNewDocument', { source: `try{localStorage.setItem('mms-theme','dark');localStorage.setItem('mms-sound','off')}catch(e){}; document.documentElement && (document.documentElement.style.scrollBehavior='auto');` });
for (const s of plan.steps) {
  if (s.nav) { await send('Page.navigate', { url: s.nav }); await sleep(s.wait ?? 5000); continue; }
  if (s.eval) { const r = await send('Runtime.evaluate', { expression: s.eval, returnByValue: true, awaitPromise: true }); if (r?.result?.value !== undefined) console.log('eval:', JSON.stringify(r.result.value).slice(0, 300)); if (r?.exceptionDetails) console.log('evalerr', JSON.stringify(r.exceptionDetails).slice(0, 300)); }
  if (s.wait && !s.rec) await sleep(s.wait);
  if (s.shot) {
    const p = { format: 'png', captureBeyondViewport: false };
    let clip = s.clip;
    if (s.sel) { const r = await send('Runtime.evaluate', { expression: `(()=>{const b=document.querySelector(${JSON.stringify(s.sel)}).getBoundingClientRect();return {x:b.x+scrollX,y:b.y+scrollY,width:b.width,height:b.height}})()`, returnByValue: true }); clip = r.result.value; const pad = s.pad ?? 0; clip = { x: clip.x - pad, y: clip.y - pad, width: clip.width + 2 * pad, height: clip.height + 2 * pad }; }
    else if (clip) { const r = await send('Runtime.evaluate', { expression: 'scrollY', returnByValue: true }); clip = { ...clip, y: clip.y + r.result.value }; }
    if (clip) p.clip = { ...clip, scale: 1 };
    const shot = await send('Page.captureScreenshot', p); writeFileSync(s.shot, Buffer.from(shot.data, 'base64')); console.log('shot', s.shot);
  }
  if (s.vrec) {
    // Deterministic capture: pause the page clock, advance exactly 1/fps per frame, screenshot each frame.
    mkdirSync(s.vrec + '/frames', { recursive: true });
    const fps = s.fps || 30, n = Math.round(s.seconds * fps);
    await send('Emulation.setVirtualTimePolicy', { policy: 'pause' });
    if (s.during) await send('Runtime.evaluate', { expression: `setTimeout(()=>{${s.during}}, ${s.duringAt ?? 300})` });
    for (let i = 0; i < n; i++) {
      const done = new Promise((r) => (budgetDone = r));
      await send('Emulation.setVirtualTimePolicy', { policy: 'advance', budget: 1000 / fps });
      await done;
      const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 90 });
      writeFileSync(`${s.vrec}/frames/f${String(i).padStart(5, '0')}.jpg`, Buffer.from(shot.data, 'base64'));
    }
    await send('Emulation.setVirtualTimePolicy', { policy: 'advance', budget: 0 });
    await send('Emulation.setVirtualTimePolicy', { policy: 'pauseIfNetworkFetchesPending', budget: 0 });
    writeFileSync(`${s.vrec}/index.json`, JSON.stringify({ fps, frames: n }));
    console.log('vrec', s.vrec, n, 'frames @', fps);
  }
  if (s.rec) {
    mkdirSync(s.rec + '/frames', { recursive: true }); const index = []; let n = 0;
    frameSink = (f) => { const name = `f${String(n++).padStart(5, '0')}.jpg`; writeFileSync(`${s.rec}/frames/${name}`, Buffer.from(f.data, 'base64')); index.push({ name, t: f.metadata.timestamp }); };
    await send('Page.startScreencast', { format: 'jpeg', quality: 88, maxWidth: W * SC, maxHeight: H * SC, everyNthFrame: 1 });
    if (s.during) { await sleep(s.duringAt ?? 300); await send('Runtime.evaluate', { expression: s.during }); }
    await sleep(s.seconds * 1000); await send('Page.stopScreencast'); frameSink = null;
    writeFileSync(`${s.rec}/index.json`, JSON.stringify(index)); const d = index.length > 1 ? index.at(-1).t - index[0].t : 0;
    console.log('rec', s.rec, index.length, 'frames over', d.toFixed(2), 's =', (index.length / Math.max(d, 0.01)).toFixed(1), 'fps');
  }
}
console.log(logs.length ? logs.join('\n') : 'no console errors'); ws.close(); chrome.kill();
