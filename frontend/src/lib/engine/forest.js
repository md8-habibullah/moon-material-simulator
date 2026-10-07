// Runs the exported scikit-learn Random Forest in the browser (see models/property_model.py).
import { binderBaseline, encode, inSituFraction, temperatureFactors } from './physics.js';

export function createEngine(forest, catalog) {
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

  function predict(row) {
    const x = encode(catalog, forest.features, row).map(Math.fround);
    const base = baselines[row.binder];
    const sum = new Float64Array(nTargets);
    const sumSq = new Float64Array(nTargets);
    for (const tree of trees) {
      const z = leafValues(tree, x);
      const props = new Float64Array(nTargets);
      for (let i = 0; i < nTargets; i += 1) props[i] = Math.exp(z[i] * std[i] + mean[i]) * base[i];
      const factors = temperatureFactors(catalog, row.binder, props[hdtIndex], row.temperature);
      for (let i = 0; i < nTargets; i += 1) {
        const value = props[i] * factors[targets[i]];
        sum[i] += value;
        sumSq[i] += value * value;
      }
    }
    const properties = {};
    const uncertainty = {};
    const n = trees.length;
    targets.forEach((t, i) => {
      const m = sum[i] / n;
      properties[t] = m;
      uncertainty[t] = Math.sqrt(Math.max(0, sumSq[i] / n - m * m));
    });
    return {
      properties,
      uncertainty,
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
