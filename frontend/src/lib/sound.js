// Sound for the 3D views, synthesised with the Web Audio API (no audio files to download).
// Off by default: browsers only allow audio after a click, and a page that suddenly hums is rude.
// The on/off choice is remembered per browser.

const KEY = 'mms-sound';
const listeners = new Set();
let enabled = false;
try {
  enabled = localStorage.getItem(KEY) === 'on';
} catch {
  /* storage blocked: stay off */
}

let ctx = null;
let master = null;
let noiseBuffer = null;
let ambient = null;
let ambientWanted = false;
let creak = null;

function audio() {
  if (!ctx) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    ctx = new Ctx();
    master = ctx.createGain();
    master.gain.value = 0.55;
    const comp = ctx.createDynamicsCompressor();
    master.connect(comp).connect(ctx.destination);
    noiseBuffer = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
    const d = noiseBuffer.getChannelData(0);
    let last = 0;
    for (let i = 0; i < d.length; i += 1) {
      // Brown-ish noise: softer than white noise, reads as rumble and dust.
      last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02;
      d[i] = last * 3.5;
    }
  }
  if (ctx.state === 'suspended') ctx.resume();
  return ctx;
}

function envGain(at, peak, attack, decay) {
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(peak, at + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, at + attack + decay);
  return g;
}

function tone(freq, { type = 'sine', peak = 0.2, attack = 0.005, decay = 0.25, delay = 0, slideTo } = {}) {
  if (!enabled || !audio()) return;
  const at = ctx.currentTime + delay;
  const osc = ctx.createOscillator();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, at);
  if (slideTo) osc.frequency.exponentialRampToValueAtTime(slideTo, at + attack + decay);
  osc.connect(envGain(at, peak, attack, decay)).connect(master);
  osc.start(at);
  osc.stop(at + attack + decay + 0.05);
}

function noise({ peak = 0.4, attack = 0.002, decay = 0.4, filter = 'bandpass', freq = 1200, q = 0.8, sweepTo, delay = 0 } = {}) {
  if (!enabled || !audio()) return;
  const at = ctx.currentTime + delay;
  const src = ctx.createBufferSource();
  src.buffer = noiseBuffer;
  const f = ctx.createBiquadFilter();
  f.type = filter;
  f.frequency.setValueAtTime(freq, at);
  if (sweepTo) f.frequency.exponentialRampToValueAtTime(sweepTo, at + attack + decay);
  f.Q.value = q;
  src.connect(f).connect(envGain(at, peak, attack, decay)).connect(master);
  src.start(at, Math.random());
  src.stop(at + attack + decay + 0.05);
}

function startAmbient() {
  if (ambient || !enabled || !audio()) return;
  const out = ctx.createGain();
  out.gain.setValueAtTime(0.0001, ctx.currentTime);
  out.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + 2.5);
  out.connect(master);
  const lp = ctx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = 420;
  lp.connect(out);
  // A low, slowly breathing drone: two detuned oscillators plus filtered rumble.
  const oscs = [55, 82.4, 110.3].map((f, i) => {
    const o = ctx.createOscillator();
    o.type = i === 2 ? 'triangle' : 'sine';
    o.frequency.value = f;
    const g = ctx.createGain();
    g.gain.value = i === 2 ? 0.18 : 0.5;
    o.connect(g).connect(lp);
    o.start();
    return o;
  });
  const lfo = ctx.createOscillator();
  lfo.frequency.value = 0.07;
  const lfoGain = ctx.createGain();
  lfoGain.gain.value = 160;
  lfo.connect(lfoGain).connect(lp.frequency);
  lfo.start();
  const rumble = ctx.createBufferSource();
  rumble.buffer = noiseBuffer;
  rumble.loop = true;
  const rg = ctx.createGain();
  rg.gain.value = 0.25;
  rumble.connect(rg).connect(lp);
  rumble.start();
  ambient = { out, nodes: [...oscs, lfo, rumble] };
}

function stopAmbient() {
  if (!ambient) return;
  const { out, nodes } = ambient;
  ambient = null;
  const t = ctx.currentTime;
  out.gain.cancelScheduledValues(t);
  out.gain.setValueAtTime(Math.max(out.gain.value, 0.0001), t);
  out.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
  nodes.forEach((n) => n.stop(t + 0.7));
}

export const sound = {
  get enabled() {
    return enabled;
  },
  subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
  setEnabled(on) {
    enabled = on;
    try {
      localStorage.setItem(KEY, on ? 'on' : 'off');
    } catch {
      /* ignore */
    }
    if (on) {
      audio();
      if (ambientWanted) startAmbient();
      this.blip(660);
    } else {
      stopAmbient();
      this.creak(null);
    }
    listeners.forEach((fn) => fn());
  },
  // The drone plays while a 3D view is on screen.
  ambient(on) {
    ambientWanted = on;
    if (on) startAmbient();
    else stopAmbient();
  },
  blip(freq = 880) {
    tone(freq, { type: 'sine', peak: 0.12, decay: 0.12 });
    tone(freq * 1.5, { type: 'sine', peak: 0.05, decay: 0.1, delay: 0.04 });
  },
  tick() {
    noise({ peak: 0.18, decay: 0.03, filter: 'highpass', freq: 3500 });
    tone(1800 + Math.random() * 400, { type: 'square', peak: 0.015, decay: 0.02 });
  },
  whoosh() {
    noise({ peak: 0.22, attack: 0.15, decay: 0.6, freq: 300, sweepTo: 2400, q: 1.2 });
  },
  chime() {
    [784, 1175, 1568].forEach((f, i) => tone(f, { peak: 0.09, decay: 1.1, delay: i * 0.09 }));
  },
  crack() {
    noise({ peak: 0.9, attack: 0.001, decay: 0.35, freq: 2600, sweepTo: 400, q: 0.6 });
    noise({ peak: 0.5, attack: 0.001, decay: 0.12, filter: 'highpass', freq: 5000, delay: 0.02 });
    tone(90, { type: 'sine', peak: 0.6, attack: 0.002, decay: 0.5, slideTo: 32 });
    noise({ peak: 0.25, attack: 0.01, decay: 1.4, filter: 'lowpass', freq: 500, delay: 0.1 });
  },
  crunch() {
    for (let i = 0; i < 6; i += 1) noise({ peak: 0.45, decay: 0.08 + Math.random() * 0.1, freq: 600 + Math.random() * 2400, q: 1.5, delay: i * 0.05 + Math.random() * 0.03 });
    tone(70, { type: 'sine', peak: 0.55, decay: 0.7, slideTo: 28 });
  },
  // A sustained strain tone that rises with load. level 0..1, or null to stop.
  creak(level) {
    if (level === null || !enabled) {
      if (creak) {
        const t = ctx.currentTime;
        creak.g.gain.cancelScheduledValues(t);
        creak.g.gain.setTargetAtTime(0.0001, t, 0.05);
        creak.o.stop(t + 0.3);
        creak = null;
      }
      return;
    }
    if (!audio()) return;
    if (!creak) {
      const o = ctx.createOscillator();
      o.type = 'sawtooth';
      const f = ctx.createBiquadFilter();
      f.type = 'bandpass';
      f.Q.value = 6;
      const g = ctx.createGain();
      g.gain.value = 0.0001;
      o.connect(f).connect(g).connect(master);
      o.start();
      creak = { o, f, g };
    }
    const t = ctx.currentTime;
    creak.o.frequency.setTargetAtTime(70 + level * 260, t, 0.05);
    creak.f.frequency.setTargetAtTime(300 + level * 1600, t, 0.05);
    creak.g.gain.setTargetAtTime(0.02 + level * 0.1, t, 0.05);
  },
};
