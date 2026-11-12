// The browser engine must reproduce the Python model: same forest, same physics, same numbers.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { createEngine } from '../src/lib/engine/forest.js';
import { optimize } from '../src/lib/engine/optimizer.js';
import { missionImpact } from '../src/lib/engine/mission.js';

const load = (name) => JSON.parse(readFileSync(new URL(`../src/generated/${name}`, import.meta.url)));
const catalog = load('catalog.json');
const engine = createEngine(load('forest.json'), catalog, load('evidence_grid.json'));
const close = (a, b) => Math.abs(a - b) <= 1e-3 * Math.max(1, Math.abs(b));

test('matches Python predictions on 60 random mixes', () => {
  const fixtures = load('parity_fixtures.json');
  assert.equal(fixtures.length, 60);
  for (const f of fixtures) {
    const got = engine.predict(f.input);
    for (const t of engine.targets) {
      assert.ok(close(got.properties[t], f.properties[t]), `${t} ${JSON.stringify(f.input)}: ${got.properties[t]} vs ${f.properties[t]}`);
      assert.ok(close(got.uncertainty[t], f.uncertainty[t]), `${t} uncertainty`);
      assert.ok(close(got.range[t][0], f.range[t][0]) && close(got.range[t][1], f.range[t][1]), `${t} range`);
      assert.ok(got.range[t][0] <= got.properties[t] && got.properties[t] <= got.range[t][1], `${t} range brackets the value`);
      assert.deepEqual(got.evidence[t], f.evidence[t], `${t} evidence support`);
    }
  }
});

test('optimizer finds an all-local wrench and refuses a thruster nozzle', () => {
  const app = (id) => catalog.applications.find((a) => a.id === id);
  const wrench = optimize(engine, catalog, app('wrench'));
  assert.ok(wrench.feasible.length > 0);
  assert.equal(wrench.feasible[0].inSitu, 1);
  assert.ok(wrench.feasible.every((c) => c.pass));

  const nozzle = optimize(engine, catalog, app('nozzle'));
  assert.equal(nozzle.feasible.length, 0);
  assert.ok(nozzle.nearest.length > 0);
});

test('mission impact counts only what ships from Earth', () => {
  const mix = { binder: 'PHB', regolith_wt: 50, fiber_wt: 10 };
  const local = missionImpact(catalog, mix, { partMassKg: 2, quantity: 5, growBinderOnSite: true, drawFibreOnSite: true, costPerKg: 1000 });
  assert.equal(local.savedShare, 1);
  const shipped = missionImpact(catalog, mix, { partMassKg: 2, quantity: 5, growBinderOnSite: false, drawFibreOnSite: false, costPerKg: 1000 });
  assert.ok(Math.abs(shipped.shippedKg - 5) < 1e-9);
  assert.ok(Math.abs(shipped.savedCost - 5000) < 1e-6);
});

test('evidence correction moves predictions towards real measurements', () => {
  const points = load('evidence_points.json').filter((p) => p.used && p.target === 'compressive_strength' && p.source === 'S008');
  assert.ok(points.length > 5);
  const raw = createEngine(load('forest.json'), catalog); // physics emulator only
  let corrected = 0;
  let physicsOnly = 0;
  for (const p of points) {
    const mix = { binder: p.binder, process: p.process, regolith: 'lunar_mare', regolith_wt: p.wt, fiber_wt: 0, particle_size: 60, temperature: 23 };
    corrected += Math.abs(engine.predict(mix).properties.compressive_strength - p.value) / p.value;
    physicsOnly += Math.abs(raw.predict(mix).properties.compressive_strength - p.value) / p.value;
  }
  // Mean relative error on the hot-pressed PEI/PPSU coupons must at least halve.
  assert.ok(corrected < 0.5 * physicsOnly, `corrected ${(corrected / points.length).toFixed(3)} vs physics ${(physicsOnly / points.length).toFixed(3)}`);
});

test('part load tests follow the beam and column formulas', async () => {
  const { PARTS, mechanics, partTest } = await import('../src/lib/engine/parts.js');
  const props = { tensile_strength: 30, compressive_strength: 40, elastic_modulus: 5, density: 2, elongation_at_break: 3 };
  // Wrench handle: Z = b h² / 6 = 6 · 20² / 6 = 400 mm³, arm 120 mm → F = 30 · 400 / 120 = 100 N.
  const w = mechanics(PARTS.wrench, props);
  assert.ok(Math.abs(w.failLoad - 100) < 1e-9);
  assert.ok(Math.abs(w.stressAt(w.failLoad) - 30) < 1e-9);
  // Brick: 200 × 100 mm face at 40 MPa → 800 kN.
  assert.ok(Math.abs(mechanics(PARTS.brick, props).failLoad - 800_000) < 1e-6);
  // Brick design load: (2.0 g/cm³ × 2 m + 1.5 × 3 m) × 1000 × 1.62 Pa over 0.02 m².
  assert.ok(Math.abs(PARTS.brick.designForce(PARTS.brick, props) - (2000 * 2 + 1500 * 3) * 1.62 * 0.02) < 1e-6);

  const mix = { binder: 'PEEK', process: 'sintered', regolith: 'lunar_mare', regolith_wt: 50, fiber_wt: 0, particle_size: 50, temperature: 20 };
  for (const part of Object.values(PARTS)) {
    const t = partTest(engine, part, mix, 20);
    assert.ok(t.failRange[0] <= t.failLoad && t.failLoad <= t.failRange[1], `${part.id} failure range brackets the estimate`);
    assert.ok(t.designLoad > 0 && Number.isFinite(t.safetyFactor));
  }
  // Colder is stiffer and stronger for these polymers: the lunar-night wrench should not be weaker than at room temperature.
  const warm = partTest(engine, PARTS.wrench, mix, 20);
  const cold = partTest(engine, PARTS.wrench, mix, -173);
  assert.ok(cold.strength >= warm.strength * 0.99);
});
