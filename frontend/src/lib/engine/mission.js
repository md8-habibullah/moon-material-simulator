// Launch mass and cost avoided by printing a part on site instead of shipping it from Earth.

export function missionImpact(catalog, composition, { partMassKg, quantity, growBinderOnSite, drawFibreOnSite, costPerKg }) {
  const totalKg = Math.max(0, partMassKg) * Math.max(0, quantity);
  const binder = catalog.binders[composition.binder];
  const binderShare = (100 - composition.regolith_wt - composition.fiber_wt) / 100;
  const fibreShare = composition.fiber_wt / 100;

  const binderLocal = binder.made_on_site && growBinderOnSite;
  const shippedShare = (binderLocal ? 0 : binderShare) + (drawFibreOnSite ? 0 : fibreShare);
  const shippedKg = totalKg * shippedShare;
  const savedKg = totalKg - shippedKg;

  return {
    totalKg,
    shippedKg,
    savedKg,
    savedShare: totalKg > 0 ? savedKg / totalKg : 0,
    savedCost: savedKg * costPerKg,
    shippedCost: shippedKg * costPerKg,
    binderLocal,
    breakdown: [
      { key: 'regolith', label: 'Regolith', share: composition.regolith_wt / 100, local: true },
      { key: 'fibre', label: 'Basalt fibre', share: fibreShare, local: drawFibreOnSite },
      { key: 'binder', label: binder.label, share: binderShare, local: binderLocal },
    ].filter((b) => b.share > 0),
  };
}
