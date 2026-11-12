// Load tests for real parts, using textbook beam and column formulas on the model's predictions.
// The materials data come from the model; part sizes and design loads are stated assumptions.
// Units: mm, N, MPa (= N/mm²). Strength in MPa, stiffness in GPa, density in g/cm³.

export const GRAVITY = { moon: 1.62, mars: 3.71, earth: 9.81 };

export const ENVIRONMENTS = [
  { id: 'habitat', label: 'Inside the habitat', short: 'Habitat', temperature: 20 },
  { id: 'noon', label: 'Lunar noon', short: 'Lunar noon', temperature: 127 },
  { id: 'night', label: 'Lunar night', short: 'Lunar night', temperature: -173 },
];

export const PARTS = {
  wrench: {
    id: 'wrench',
    label: 'Wrench',
    test: 'Bending',
    limit: 'tensile_strength',
    why: 'In bending the tension side fails first, so tensile strength sets the limit.',
    // Open-end wrench for an M6 bolt: the handle is a beam clamped at the head and pulled by hand.
    dims: { arm: 120, depth: 20, thickness: 6, hand: 138 }, // arm: handle root → hand; hand: bolt → hand
    design: { torque: 10, label: 'Tightening an M6 bolt to 10 N·m (assumed)' },
    designForce(p) {
      return (p.design.torque * 1000) / p.dims.hand;
    },
  },
  bracket: {
    id: 'bracket',
    label: 'Shelf bracket',
    test: 'Bending',
    limit: 'tensile_strength',
    why: 'In bending the tension side fails first, so tensile strength sets the limit.',
    // L-bracket: a 100 mm arm, 30 mm wide and 8 mm thick, bolted to the habitat wall.
    dims: { arm: 100, depth: 8, thickness: 30 },
    design: { mass: 20, label: '20 kg of equipment on its tip, in lunar gravity (assumed)' },
    designForce(p) {
      return p.design.mass * GRAVITY.moon;
    },
  },
  brick: {
    id: 'brick',
    label: 'Shelter brick',
    test: 'Compression',
    limit: 'compressive_strength',
    why: 'A brick in a wall is squeezed, so compressive strength sets the limit.',
    // 200 × 100 mm face, 60 mm tall, at the bottom of a 2 m wall under 3 m of regolith shielding.
    dims: { length: 200, width: 100, height: 60, wall: 2000, shielding: 3000, regolithDensity: 1.5 },
    design: { label: 'Bottom of a 2 m wall under 3 m of regolith radiation shielding (assumed)' },
    designForce(p, props) {
      const { length, width, wall, shielding, regolithDensity } = p.dims;
      // ρ [g/cm³] × 1000 = kg/m³; × g × height [m] = Pa; × area [m²] = N
      const pressure = (props.density * 1000 * wall + regolithDensity * 1000 * shielding) / 1000 * GRAVITY.moon;
      return pressure * ((length * width) / 1e6);
    },
  },
};

// Load at failure, and the matching stiffness response, from a property set.
export function mechanics(part, props) {
  const strength = props[part.limit];
  const E = props.elastic_modulus * 1000; // GPa → MPa
  if (part.id === 'brick') {
    const { length, width, height } = part.dims;
    const area = length * width;
    return {
      failLoad: strength * area,
      stressAt: (F) => F / area,
      // Shortening of the brick under F (mm).
      deflectionAt: (F) => (F * height) / (E * area),
    };
  }
  const { arm, depth, thickness } = part.dims;
  const I = (thickness * depth ** 3) / 12;
  const Z = (thickness * depth ** 2) / 6;
  return {
    failLoad: (strength * Z) / arm,
    stressAt: (F) => (F * arm) / Z,
    // Tip deflection of a cantilever (mm).
    deflectionAt: (F) => (F * arm ** 3) / (3 * E * I),
    I,
    Z,
  };
}

// Everything the part test shows, for one mix at one temperature.
export function partTest(engine, part, composition, temperature) {
  const result = engine.predict({ ...composition, temperature });
  const props = result.properties;
  const mid = mechanics(part, props);
  const [lo, hi] = result.range[part.limit];
  const scale = (v) => (v / props[part.limit]) * mid.failLoad;
  const design = part.designForce(part, props);
  const elongation = props.elongation_at_break;
  return {
    result,
    props,
    temperature,
    strength: props[part.limit],
    strengthRange: [lo, hi],
    failLoad: mid.failLoad,
    failRange: [scale(lo), scale(hi)],
    designLoad: design,
    safetyFactor: mid.failLoad / design,
    // Below about 2% strain at break a polymer composite snaps rather than bends.
    brittle: elongation < 2,
    elongation,
    stressAt: mid.stressAt,
    deflectionAt: mid.deflectionAt,
    deflectionAtFailure: mid.deflectionAt(mid.failLoad),
    // A column of the material standing on the Moon crushes its own base above this height (buckling ignored).
    selfSupportKm: (props.compressive_strength * 1e6) / (props.density * 1000 * GRAVITY.moon) / 1000,
  };
}

export function massEquivalent(force, body = 'moon') {
  return force / GRAVITY[body];
}

export function formatForce(n) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)} MN`;
  if (n >= 1e4) return `${(n / 1000).toFixed(0)} kN`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)} kN`;
  return `${n.toFixed(n < 10 ? 1 : 0)} N`;
}

export function formatMass(kg) {
  if (kg >= 1e5) return `${Math.round(kg / 1000).toLocaleString('en-US')} t`;
  if (kg >= 1000) return `${(kg / 1000).toFixed(1)} t`;
  return `${kg.toFixed(kg < 10 ? 1 : 0)} kg`;
}

export function formatFactor(sf) {
  if (sf >= 100) return `${Math.round(sf).toLocaleString('en-US')}×`;
  if (sf >= 10) return `${sf.toFixed(0)}×`;
  return `${sf.toFixed(sf < 1 ? 2 : 1)}×`;
}
