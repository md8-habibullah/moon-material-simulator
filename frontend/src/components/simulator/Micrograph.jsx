import { useEffect, useRef } from 'react';
import catalog from '../../lib/catalog';

// Procedural cross-polarised view, styled after NASA Glenn's micrographs of PHB + simulant:
// "kaleidoscope-like" spherulites, grey with Moon dust and reddish with Mars dust.
const W = 360;
const H = 216;
const TINTS = {
  lunar_highlands: [[70, 92, 128], [196, 214, 236], [230, 214, 160]],
  lunar_mare: [[52, 80, 96], [168, 206, 214], [214, 196, 150]],
  martian: [[110, 52, 36], [236, 168, 132], [244, 214, 150]],
};

function mulberry32(seed) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** NASA Glenn DSC trend for PHB: crystallinity falls from ~66% (neat) to ~27% at 80 wt% regolith. */
export function phbCrystallinity(regolithWt) {
  return 26 + 40 * Math.exp(-((regolithWt / 38) ** 1.5));
}

function draw(ctx, { regolith, regolith_wt: wt, particle_size: size, binder }) {
  const rand = mulberry32(7 + Math.round(wt) * 31 + Math.round(size));
  // Grains act as nucleation sites: more regolith, more and smaller spherulites.
  const nuclei = Array.from({ length: Math.round(9 + wt * 1.4) }, () => ({
    x: rand() * W,
    y: rand() * H,
    phase: rand() * Math.PI,
    ring: 7 + rand() * 6,
  }));
  const [dark, light, warm] = TINTS[regolith];
  const crystalline = binder === 'LDPE' ? 0.75 : binder === 'PLA' ? 0.55 : 1;
  const img = ctx.createImageData(W, H);

  for (let y = 0; y < H; y += 1) {
    for (let x = 0; x < W; x += 1) {
      let d1 = Infinity;
      let d2 = Infinity;
      let n1 = nuclei[0];
      for (const n of nuclei) {
        const d = (x - n.x) ** 2 + (y - n.y) ** 2;
        if (d < d1) {
          d2 = d1;
          d1 = d;
          n1 = n;
        } else if (d < d2) d2 = d;
      }
      const r = Math.sqrt(d1);
      const theta = Math.atan2(y - n1.y, x - n1.x);
      // Maltese cross under crossed polarisers, plus faint birefringence rings.
      const cross = Math.sin(2 * theta) ** 2;
      const rings = 0.5 + 0.5 * Math.cos(r / n1.ring + n1.phase);
      const boundary = Math.min(1, (Math.sqrt(d2) - r) / 2.2);
      const b = (0.18 + 0.82 * cross * (0.65 + 0.35 * rings)) * (0.35 + 0.65 * boundary) * crystalline + (1 - crystalline) * 0.25;
      const w = 0.35 * rings * cross;
      const i = (y * W + x) * 4;
      img.data[i] = dark[0] + (light[0] - dark[0]) * b + (warm[0] - light[0]) * w * b;
      img.data[i + 1] = dark[1] + (light[1] - dark[1]) * b + (warm[1] - light[1]) * w * b;
      img.data[i + 2] = dark[2] + (light[2] - dark[2]) * b + (warm[2] - light[2]) * w * b;
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);

  // Regolith grains: dark, angular specks sized by the median grain size.
  const count = Math.round(wt * 2.2);
  const px = 0.6 + size / 28;
  ctx.fillStyle = 'rgba(12, 10, 10, 0.85)';
  for (let k = 0; k < count; k += 1) {
    const cx = rand() * W;
    const cy = rand() * H;
    const rad = px * (0.5 + rand());
    ctx.beginPath();
    const sides = 5 + Math.floor(rand() * 3);
    for (let s = 0; s < sides; s += 1) {
      const a = (s / sides) * Math.PI * 2 + rand() * 0.6;
      const rr = rad * (0.7 + rand() * 0.5);
      ctx.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr);
    }
    ctx.closePath();
    ctx.fill();
  }
}

export default function Micrograph({ composition }) {
  const canvasRef = useRef(null);
  const { regolith, regolith_wt: wt, particle_size: size, binder } = composition;

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const ctx = canvasRef.current?.getContext('2d');
      if (ctx) draw(ctx, { regolith, regolith_wt: wt, particle_size: size, binder });
    });
    return () => cancelAnimationFrame(frame);
  }, [regolith, wt, size, binder]);

  const crystallinity = binder === 'PHB' ? phbCrystallinity(wt) : null;

  return (
    <div className="viewer-wrap">
      <div className="micrograph">
        <canvas ref={canvasRef} width={W} height={H} role="img" aria-label="Illustrative cross-polarised micrograph of the composite" />
        <span className="scale-bar" aria-hidden="true">
          <i />
          100 µm
        </span>
      </div>
      <div className="viewer-legend">
        {crystallinity !== null ? (
          <span>
            Crystallinity ≈ <strong>{Math.round(crystallinity)}%</strong> (NASA Glenn DSC trend)
          </span>
        ) : (
          <span>Crystal pattern is illustrative for {catalog.binders[binder].label}</span>
        )}
        <span className="viewer-hint">Illustrative · more regolith = more, smaller crystals</span>
      </div>
    </div>
  );
}
