// The browser engine must reproduce the Python model: same forest, same physics, same numbers.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { createEngine } from '../src/lib/engine/forest.js';
import { optimize } from '../src/lib/engine/optimizer.js';
import { missionImpact } from '../src/lib/engine/mission.js';

const load = (name) => JSON.parse(readFileSync(new URL(`../src/generated/${name}`, import.meta.url)));
const catalog = load('catalog.json');
const engine = createEngine(load('forest.json'), catalog);
const close = (a, b) => Math.abs(a - b) <= 1e-3 * Math.max(1, Math.abs(b));

test('matches Python predictions on 60 random mixes', () => {
  const fixtures = load('parity_fixtures.json');
  assert.equal(fixtures.length, 60);
  for (const f of fixtures) {
    const got = engine.predict(f.input);
    for (const t of engine.targets) {
      assert.ok(close(got.properties[t], f.properties[t]), `${t} ${JSON.stringify(f.input)}: ${got.properties[t]} vs ${f.properties[t]}`);
      assert.ok(close(got.uncertainty[t], f.uncertainty[t]), `${t} uncertainty`);
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
