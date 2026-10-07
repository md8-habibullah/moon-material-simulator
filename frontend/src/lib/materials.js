// Display metadata. The numbers that matter come from the API; densities here only drive
// the 3D grain count so the viewer stays responsive while a prediction is in flight.

export const POLYMERS = {
  PLA: { label: 'PLA', name: 'Polylactic acid', note: 'Biodegradable', density: 1.24 },
  PEEK: { label: 'PEEK', name: 'Polyether ether ketone', note: 'High-temperature', density: 1.3 },
  LDPE: { label: 'LDPE', name: 'Low-density polyethylene', note: 'Flexible', density: 0.92 },
};

export const REGOLITHS = {
  lunar: { label: 'Lunar', name: 'Lunar highlands simulant', density: 2.9, maxTemp: 127, place: 'lunar noon' },
  martian: { label: 'Martian', name: 'Martian global simulant', density: 2.75, maxTemp: 20, place: 'a Martian summer day' },
};

export const TEMPERATURE_PRESETS = [
  { label: 'Lunar night', value: -173 },
  { label: 'Mars night', value: -125 },
  { label: 'Room', value: 23 },
  { label: 'Lunar noon', value: 120 },
];

export const PROPERTIES = [
  { key: 'tensile_strength', label: 'Tensile strength', unit: 'MPa', hint: 'Pulling load before it snaps' },
  { key: 'elastic_modulus', label: 'Elastic modulus', unit: 'GPa', hint: 'Stiffness: how little it bends' },
  { key: 'compressive_strength', label: 'Compressive strength', unit: 'MPa', hint: 'Crushing load it can carry' },
  { key: 'thermal_stability', label: 'Max service temp', unit: '°C', hint: 'Where the matrix starts to soften' },
];

export function volumeFraction(regolithWt, polymer, regolith) {
  const w = regolithWt / 100;
  if (w <= 0) return 0;
  const f = w / REGOLITHS[regolith].density;
  return f / (f + (1 - w) / POLYMERS[polymer].density);
}

export function formatNumber(value, digits = 1) {
  return Number(value).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}
