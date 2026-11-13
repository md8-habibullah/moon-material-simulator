// The stories of the machines NASA left behind: every card must be complete, placed on the map, linked to a NASA source,
// and its "Try it" button must open a real part test.
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { test } from 'node:test';
import { RELICS, WORLDS } from '../src/lib/relics.js';
import { ENVIRONMENTS, PARTS } from '../src/lib/engine/parts.js';

const catalog = JSON.parse(readFileSync(new URL('../src/generated/catalog.json', import.meta.url)));
const publicFile = (path) => new URL(`../public/${path}`, import.meta.url);

test('every story is complete and has a unique id', () => {
  assert.equal(new Set(RELICS.map((r) => r.id)).size, RELICS.length);
  for (const r of RELICS) {
    for (const key of ['name', 'kind', 'year', 'place', 'did', 'why', 'science', 'lesson', 'fact']) {
      assert.ok(typeof r[key] === 'string' && r[key].trim().length > 0, `${r.id} is missing ${key}`);
    }
    assert.ok(WORLDS[r.world], `${r.id} has an unknown world`);
  }
  for (const world of Object.keys(WORLDS)) assert.ok(RELICS.some((r) => r.world === world), `no story on ${world}`);
});

test('every machine sits at a real place on its map', () => {
  for (const r of RELICS) {
    assert.ok(r.lat >= -90 && r.lat <= 90, `${r.id} latitude`);
    assert.ok(r.lon >= -180 && r.lon <= 180, `${r.id} longitude`);
  }
  for (const w of Object.values(WORLDS)) assert.ok(existsSync(publicFile(w.map)), `missing map ${w.map}`);
});

test('every photo exists, has alt text and a NASA credit link', () => {
  for (const r of RELICS) {
    assert.ok(r.images.length > 0, `${r.id} has no photo`);
    for (const im of r.images) {
      assert.ok(existsSync(publicFile(im.src)), `missing ${im.src}`);
      assert.ok(im.alt.length > 20, `${im.src} needs real alt text`);
      assert.match(im.credit, /NASA/);
      assert.match(im.link, /^https:\/\/images\.nasa\.gov\/details\//);
    }
  }
});

test('every story cites at least one NASA source over https', () => {
  for (const r of RELICS) {
    assert.ok(r.sources.length > 0, `${r.id} has no source`);
    for (const s of r.sources) assert.match(s.url, /^https:\/\/([a-z]+\.)*nasa\.gov\//, `${r.id}: ${s.url}`);
  }
});

test('every "Try it" opens a real part test with a real soil', () => {
  for (const r of RELICS) {
    const { part, env, regolith } = r.tryIt;
    assert.ok(PARTS[part], `${r.id}: unknown part ${part}`);
    assert.ok(ENVIRONMENTS.some((e) => e.id === env), `${r.id}: unknown place ${env}`);
    assert.ok(catalog.regoliths[regolith], `${r.id}: unknown soil ${regolith}`);
    // Martian machines use Martian dust; Moon machines use lunar dust.
    assert.equal(regolith === 'martian', r.world === 'mars', `${r.id}: soil does not match its world`);
  }
});
