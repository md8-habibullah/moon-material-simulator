import catalog from '../generated/catalog.json';

export default catalog;

export const REPO_URL = 'https://github.com/md8-habibullah/moon-material-simulator';
export const VIDEO_URL = 'https://youtu.be/1Gtmq5XUytc';
export const docUrl = (path) => `${REPO_URL}/blob/main/${path}`;

export const DOCS = [
  { label: 'README', path: 'README.md', note: 'Overview, setup, team' },
  { label: 'Architecture', path: 'docs/architecture.md', note: 'How the pieces fit' },
  { label: 'Science model', path: 'docs/science_model.md', note: 'Equations and NASA calibration' },
  { label: 'Data dictionary', path: 'docs/data_dictionary.md', note: 'Every input and output' },
  { label: 'NASA data sources', path: 'docs/data_sources.md', note: 'What we used and how' },
  { label: 'API reference', path: 'docs/api.md', note: 'FastAPI endpoints' },
  { label: 'Deployment', path: 'docs/deployment.md', note: 'GitHub Pages and local run' },
  { label: 'Demo script', path: 'docs/demo_script.md', note: 'A 90-second walkthrough' },
];

export const TEAM = [
  { name: 'Mahdin Islam Mukim', role: 'Team Lead' },
  { name: 'Yousuf Abdullah', role: 'Data Scientist' },
  { name: 'Md. Habibullah Sharif', role: 'Systems Architect' },
  { name: 'Maliha Sanjana', role: 'UI/UX Designer' },
  { name: 'Lamisa Yeasmin Nakia', role: 'Research & Storytelling Lead' },
];

// Display order and copy for the eight predicted properties.
export const PROPERTIES = [
  { key: 'tensile_strength', label: 'Tensile strength', short: 'Tensile', hint: 'Pulling load before it breaks', better: 'higher' },
  { key: 'elastic_modulus', label: 'Stiffness', short: 'Stiffness', hint: 'Elastic modulus: how little it bends', better: 'higher' },
  { key: 'compressive_strength', label: 'Compressive strength', short: 'Compressive', hint: 'Crushing load it can carry', better: 'higher' },
  { key: 'elongation_at_break', label: 'Flexibility', short: 'Flexibility', hint: 'Stretch before breaking', better: 'higher' },
  { key: 'max_service_temp', label: 'Max service temp', short: 'Service temp', hint: 'Softens above this', better: 'higher' },
  { key: 'decomposition_temp', label: 'Decomposition temp', short: 'Decomposes', hint: 'Breaks down chemically', better: 'higher' },
  { key: 'density', label: 'Density', short: 'Density', hint: 'Mass per volume', better: 'neutral' },
  { key: 'thermal_conductivity', label: 'Thermal conductivity', short: 'Conductivity', hint: 'How fast heat flows through', better: 'neutral' },
];
export const PROPERTY = Object.fromEntries(PROPERTIES.map((p) => [p.key, p]));

export const TEMPERATURE_PRESETS = [
  { label: 'Lunar night', value: -173 },
  { label: 'Mars night', value: -125 },
  { label: 'Habitat', value: 20 },
  { label: 'Lunar noon', value: 127 },
];

// Regions on the regolith slider, straight from the pitch: ~10% for tools, ~50% for structures.
export const LOADING_ZONES = [
  { label: 'Tools', from: 5, to: 20 },
  { label: 'Structures', from: 45, to: 80 },
];

export const DEFAULT_COMPOSITION = {
  binder: 'PHB',
  regolith: 'lunar_highlands',
  regolith_wt: 30,
  fiber_wt: 0,
  particle_size: 60,
  temperature: 20,
};

export const ACCENT_BY_REGOLITH = { lunar_highlands: 'highlands', lunar_mare: 'mare', martian: 'mars' };

export function unitOf(key) {
  return catalog.units[key];
}

export function formatValue(value, key) {
  if (value === undefined || value === null || Number.isNaN(value)) return '–';
  const unit = catalog.units[key];
  const abs = Math.abs(value);
  const digits = unit === '°C' ? 0 : abs >= 100 ? 0 : abs >= 10 ? 1 : abs >= 1 ? 2 : 3;
  return value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function describeMix(c) {
  const parts = [`${c.regolith_wt}% ${catalog.regoliths[c.regolith].label}`];
  if (c.fiber_wt > 0) parts.push(`${c.fiber_wt}% fibre`);
  return `${parts.join(' + ')} in ${catalog.binders[c.binder].label}`;
}

export function maxFiberFor(regolithWt) {
  return Math.max(0, Math.min(catalog.ranges.fiber_wt[1], catalog.physics.max_total_filler_wt - regolithWt));
}
