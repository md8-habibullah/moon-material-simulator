// "Design → test → optimize": search the composition space for mixes that meet a use's needs.

const WT_STEPS = Array.from({ length: 17 }, (_, i) => i * 5); // 0..80 wt%
const FIBER_STEPS = [0, 5, 10, 15];
const SIZE_STEPS = [25, 60, 120];

function regolithsFor(catalog, body) {
  const all = Object.keys(catalog.regoliths);
  return body === 'any' ? all : all.filter((r) => catalog.regoliths[r].body === body);
}

/** Smallest normalised slack across all requirements and temperatures (>= 0 means it passes). */
export function evaluate(engine, application, composition) {
  const checks = [];
  for (const temperature of application.temps) {
    const { properties } = engine.predict({ ...composition, temperature });
    for (const [key, rule] of Object.entries(application.requirements)) {
      const value = properties[key];
      if (rule.min !== undefined) checks.push({ key, temperature, value, limit: rule.min, kind: 'min', slack: (value - rule.min) / rule.min });
      if (rule.max !== undefined) checks.push({ key, temperature, value, limit: rule.max, kind: 'max', slack: (rule.max - value) / rule.max });
    }
  }
  const worst = checks.reduce((a, b) => (b.slack < a.slack ? b : a));
  return { pass: worst.slack >= 0, margin: worst.slack, worst, checks };
}

export function optimize(engine, catalog, application, { binders = Object.keys(catalog.binders), limit = 5 } = {}) {
  const maxFiller = catalog.physics.max_total_filler_wt;
  const best = new Map(); // one entry per binder/regolith/wt, keeping its best fibre and grain size
  let evaluated = 0;

  for (const binder of binders) {
    for (const regolith of regolithsFor(catalog, application.body)) {
      for (const regolithWt of WT_STEPS) {
        for (const fiberWt of FIBER_STEPS) {
          if (regolithWt + fiberWt > maxFiller) continue;
          for (const particleSize of SIZE_STEPS) {
            const composition = { binder, regolith, regolith_wt: regolithWt, fiber_wt: fiberWt, particle_size: particleSize };
            const result = evaluate(engine, application, composition);
            evaluated += 1;
            const inSitu = engine.predict({ ...composition, temperature: 23 }).in_situ_fraction;
            const candidate = { composition, inSitu, ...result };
            const key = `${binder}|${regolith}|${regolithWt}`;
            const current = best.get(key);
            if (!current || rank(candidate, current) < 0) best.set(key, candidate);
          }
        }
      }
    }
  }

  const all = [...best.values()];
  const feasible = all.filter((c) => c.pass).sort(rank);
  const nearest = feasible.length ? [] : all.sort((a, b) => b.margin - a.margin).slice(0, 3);
  return { feasible: feasible.slice(0, limit), feasibleCount: feasible.length, nearest, evaluated };
}

// Passing mixes first; then the most locally sourced; then the most regolith (dust is free, while
// growing bioplastic takes bioreactor time); then the most comfortable margin.
function rank(a, b) {
  if (a.pass !== b.pass) return a.pass ? -1 : 1;
  if (Math.abs(a.inSitu - b.inSitu) > 1e-9) return b.inSitu - a.inSitu;
  const fillerA = a.composition.regolith_wt + a.composition.fiber_wt;
  const fillerB = b.composition.regolith_wt + b.composition.fiber_wt;
  if (fillerA !== fillerB) return fillerB - fillerA;
  return b.margin - a.margin;
}
