// Evidence correction learned from real lab measurements (backend/models/evidence_model.py).
// The Gaussian process is exported as a table on a grid of filler volume fractions for every
// binder × process; this linear interpolation mirrors models/evidence_model.interpolate exactly.

/** { mean, std } of the log-correction and how many real measurements sit near this mix. */
export function evidenceAt(grid, target, binder, process, phi) {
  const t = grid?.targets?.[target];
  if (!t) return { mean: 0, std: 0, same: 0, binder: 0 };
  const cell = t.table[`${binder}|${process}`];
  if (!cell) return { mean: 0, std: 0, same: 0, binder: 0 };
  const xs = grid.phi;
  const x = Math.min(Math.max(phi, xs[0]), xs[xs.length - 1]);
  const i = Math.min(Math.trunc((x - xs[0]) / (xs[1] - xs[0])), xs.length - 2);
  const f = (x - xs[i]) / (xs[i + 1] - xs[i]);
  const lerp = (arr) => arr[i] * (1 - f) + arr[i + 1] * f;
  const nearest = f < 0.5 ? i : i + 1;
  return { mean: lerp(cell.mean), std: lerp(cell.std), same: cell.same[nearest], binder: cell.binder[nearest] };
}

/** How a prediction is backed: measured with this process, measured with another process, or physics only. */
export function supportLevel(ev) {
  if (ev.same > 0) return 'measured';
  if (ev.binder > 0) return 'related';
  return 'physics';
}
