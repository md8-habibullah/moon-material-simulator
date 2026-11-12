// Colours shared by the 3D views.
export const MATRIX_COLORS = { PHB: 0xf1d9a7, PLA: 0x9fd4ff, PEEK: 0xd9b27a, LDPE: 0xe6eef4, PEI: 0xe0a24a, PPSU: 0xc9b98f };

// Stress / strength from 0 (cool) to 1 (failure).
export const STRESS_STOPS = [
  [0, '#1d4ed8'],
  [0.25, '#06b6d4'],
  [0.5, '#22c55e'],
  [0.75, '#facc15'],
  [0.9, '#f97316'],
  [1, '#ef4444'],
];

export const STRESS_GRADIENT = `linear-gradient(90deg, ${STRESS_STOPS.map(([t, c]) => `${c} ${t * 100}%`).join(', ')})`;
