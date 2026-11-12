// Runs the exported scikit-learn Random Forest in the browser (see models/property_model.py).
import { binderBaseline, encode, inSituFraction, physicsFeatures, temperatureFactors } from './physics.js';
import { evidenceAt } from './evidence.js';

// About-68% band in log space (mirrors log_range in property_model.py): the evidence error is
// multiplicative, so the band is [value / e^s, value * e^s] and never goes below zero.
export function logRange(value, treeStd, evidenceSd) {
  if (value <= 0) return [value - treeStd, value + treeStd];
  const s = Math.sqrt((treeStd / value) ** 2 + evidenceSd ** 2);
  return [value * Math.exp(-s), value * Math.exp(s)];
}

export function createEngine(forest, catalog, evidenceGrid = null) {
  const targets = forest.targets;
  const nTargets = targets.length;
  const { mean, std } = forest.transform;
  const hdtIndex = targets.indexOf('max_service_temp');
  const baselines = Object.fromEntries(
    Object.keys(catalog.binders).map((b) => {
      const base = binderBaseline(catalog, b);
      return [b, targets.map((t) => base[t])];
    }),
  );
  const trees = forest.trees.map((t) => ({
    f: Int16Array.from(t.f),
    t: Float64Array.from(t.t),
    l: Int32Array.from(t.l),
    r: Int32Array.from(t.r),
    v: Float64Array.from(t.v),
  }));

  function leafValues(tree, x) {
    let node = 0;
    while (tree.f[node] !== -1) {
      // scikit-learn compares float32(x) against a float64 threshold.
      node = x[tree.f[node]] <= tree.t[node] ? tree.l[node] : tree.r[node];
    }
    const start = tree.l[node] * nTargets;
    return tree.v.subarray(start, start + nTargets);
  }

  // Correction from real measurements for this binder, process and filler volume fraction.
  function evidenceFor(row) {
    const process = row.process || catalog.default_process[row.binder];
    const phys = physicsFeatures(catalog, row);
    const phi = phys.phi_regolith + phys.phi_fiber;
    return Object.fromEntries(targets.map((t) => [t, evidenceAt(evidenceGrid, t, row.binder, process, phi)]));
  }

  function predict(row) {
    const x = encode(catalog, forest.features, row).map(Math.fround);
    const base = baselines[row.binder];
    const evidence = evidenceFor(row);
    const shift = targets.map((t) => Math.exp(evidence[t].mean));
    const sum = new Float64Array(nTargets);
    const sumSq = new Float64Array(nTargets);
    for (const tree of trees) {
      const z = leafValues(tree, x);
      const props = new Float64Array(nTargets);
      for (let i = 0; i < nTargets; i += 1) props[i] = Math.exp(z[i] * std[i] + mean[i]) * base[i] * shift[i];
      const factors = temperatureFactors(catalog, row.binder, props[hdtIndex], row.temperature);
      for (let i = 0; i < nTargets; i += 1) {
        const value = props[i] * factors[targets[i]];
        sum[i] += value;
        sumSq[i] += value * value;
      }
    }
    const properties = {};
    const uncertainty = {};
    const range = {};
    const n = trees.length;
    targets.forEach((t, i) => {
      const m = sum[i] / n;
      properties[t] = m;
      // Spread across trees (physics emulation) combined with the evidence model's ± (log units).
      const treeVar = Math.max(0, sumSq[i] / n - m * m);
      const ev = m * (Math.exp(evidence[t].std) - 1);
      uncertainty[t] = Math.sqrt(treeVar + ev * ev);
      range[t] = logRange(m, Math.sqrt(treeVar), evidence[t].std);
    });
    return {
      properties,
      uncertainty,
      range,
      evidence: Object.fromEntries(targets.map((t) => [t, { same: evidence[t].same, binder: evidence[t].binder }])),
      in_situ_fraction: inSituFraction(catalog, row.regolith_wt, row.fiber_wt, row.binder),
    };
  }

  return {
    targets,
    treeCount: trees.length,
    predict,
    predictMany: (rows) => rows.map(predict),
  };
}
