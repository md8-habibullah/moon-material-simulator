// Mirrors backend/utils/materials.py and utils/data_processor.py line for line.
// Any change there must be repeated here; `npm test` checks both agree on 60 random mixes.

const sigmoid = (x) => 1 / (1 + Math.exp(-Math.max(-60, Math.min(60, x))));

export function volumeFractions(catalog, regolithWt, fiberWt, binder, regolith) {
  const wr = regolithWt / 100;
  const wf = fiberWt / 100;
  const vr = wr / catalog.regoliths[regolith].density;
  const vf = wf / catalog.fiber.density;
  const vm = (1 - wr - wf) / catalog.binders[binder].density;
  const total = vr + vf + vm;
  return [vr / total, vf / total];
}

export function porosity(P, phiTotal, voidFactor = 1) {
  return P.porosity_base + P.porosity_coef * voidFactor * phiTotal ** 2;
}

export function sizeFactor(P, particleSize) {
  return Math.min(P.size_max, Math.max(P.size_min, 1 + P.size_coef * Math.log(P.size_ref_um / particleSize)));
}

export function theoreticalDensity(catalog, regolithWt, fiberWt, binder, regolith) {
  const wr = regolithWt / 100;
  const wf = fiberWt / 100;
  return (
    1 /
    (wr / catalog.regoliths[regolith].density +
      wf / catalog.fiber.density +
      (1 - wr - wf) / catalog.binders[binder].density)
  );
}

export function physicsFeatures(catalog, row) {
  const P = catalog.physics;
  const r = catalog.regoliths[row.regolith];
  const [phiR, phiF] = volumeFractions(catalog, row.regolith_wt, row.fiber_wt, row.binder, row.regolith);
  const bond = r.interface_quality * catalog.binders[row.binder].filler_affinity * sizeFactor(P, row.particle_size);
  const p = porosity(P, phiR + phiF, r.void_factor);
  return {
    phi_regolith: phiR,
    phi_fiber: phiF,
    bond,
    reinforcement: bond * phiR,
    porosity: p,
    grain_modulus: row.regolith_wt > 0 ? r.grain_modulus : 0,
    density_estimate: theoreticalDensity(catalog, row.regolith_wt, row.fiber_wt, row.binder, row.regolith) * (1 - p),
  };
}

/** Feature vector in the exact column order the forest was trained on. */
export function encode(catalog, featureNames, row) {
  const values = { ...physicsFeatures(catalog, row) };
  values.regolith_wt = row.regolith_wt;
  values.fiber_wt = row.fiber_wt;
  values.particle_size = row.particle_size;
  for (const b of Object.keys(catalog.binders)) values[`binder_${b}`] = row.binder === b ? 1 : 0;
  for (const r of Object.keys(catalog.regoliths)) values[`regolith_${r}`] = row.regolith === r ? 1 : 0;
  return featureNames.map((name) => values[name]);
}

function coldRatio(P, tempC, ratio77k, logScale = false) {
  const t = Math.min(1, Math.max(0, (P.room_temp - tempC) / P.room_to_77k));
  return logScale ? Math.exp(Math.log(ratio77k) * t) : 1 + (ratio77k - 1) * t;
}

/** Multipliers that move room-temperature properties to `tempC` (see materials.temperature_factors). */
export function temperatureFactors(catalog, binder, maxServiceTemp, tempC) {
  const P = catalog.physics;
  const b = catalog.binders[binder];
  const soft = Math.min(
    1,
    sigmoid((maxServiceTemp - tempC) / P.softening_width) / sigmoid((maxServiceTemp - P.room_temp) / P.softening_width),
  );
  const hotStretch =
    (1 + P.hot_stretch_gain * sigmoid((tempC - maxServiceTemp) / P.hot_stretch_width)) /
    (1 + P.hot_stretch_gain * sigmoid((P.room_temp - maxServiceTemp) / P.hot_stretch_width));
  return {
    tensile_strength: soft * coldRatio(P, tempC, b.cryo_strength_ratio),
    elastic_modulus: soft * coldRatio(P, tempC, b.cryo_modulus_ratio),
    compressive_strength: soft * coldRatio(P, tempC, b.cryo_strength_ratio),
    elongation_at_break: coldRatio(P, tempC, b.cryo_elongation_ratio, true) * hotStretch,
    density: 1,
    thermal_conductivity: 1,
    max_service_temp: 1,
    decomposition_temp: 1,
  };
}

/** Share of the part's mass that could come from local resources (0..1). */
export function inSituFraction(catalog, regolithWt, fiberWt, binder) {
  let local = regolithWt + fiberWt;
  if (catalog.binders[binder].made_on_site) local += 100 - regolithWt - fiberWt;
  return local / 100;
}

export function binderBaseline(catalog, binder) {
  const b = catalog.binders[binder];
  return Object.fromEntries(Object.entries(catalog.physics.baseline_keys).map(([target, key]) => [target, b[key]]));
}
