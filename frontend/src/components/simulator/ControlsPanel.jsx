import { useId, useState } from 'react';
import { Check, Leaf, Link2, Moon, Orbit, Plus, RotateCcw, Sprout } from 'lucide-react';
import SliderControl from '../SliderControl';
import catalog, { DEFAULT_COMPOSITION, LOADING_ZONES, TEMPERATURE_PRESETS, maxFiberFor } from '../../lib/catalog';
import { compositionUrl } from '../../lib/url-state';

function OptionCards({ legend, name, value, options, onChange, columns }) {
  return (
    <fieldset className="field">
      <legend>{legend}</legend>
      <div className="option-grid" style={{ '--cols': columns }}>
        {options.map((opt) => (
          <label key={opt.value} className="option-card">
            <input type="radio" name={name} value={opt.value} checked={value === opt.value} onChange={() => onChange(opt.value)} />
            <span className="option-body">
              <span className="option-title">
                {opt.swatch && <span className="swatch" style={{ background: opt.swatch }} aria-hidden="true" />}
                {opt.label}
                {value === opt.value && <Check size={14} className="option-check" aria-hidden="true" />}
              </span>
              <small>{opt.note}</small>
              {opt.tags?.length > 0 && (
                <span className="option-tags">
                  {opt.tags.map((t) => (
                    <span key={t.label} className="tag">
                      <t.icon size={11} aria-hidden="true" />
                      {t.label}
                    </span>
                  ))}
                </span>
              )}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export default function ControlsPanel({ composition, onChange, onSave, canSave, saveLabel }) {
  const nameBinder = useId();
  const nameRegolith = useId();
  const [copied, setCopied] = useState(false);
  const set = (patch) => onChange((c) => ({ ...c, ...patch }));
  const fiberMax = maxFiberFor(composition.regolith_wt);

  const setRegolithWt = (regolith_wt) => set({ regolith_wt, fiber_wt: Math.min(composition.fiber_wt, maxFiberFor(regolith_wt)) });

  const share = async () => {
    try {
      await navigator.clipboard.writeText(compositionUrl(composition));
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      window.prompt('Copy this link', compositionUrl(composition));
    }
  };

  const binders = Object.entries(catalog.binders).map(([value, b]) => ({
    value,
    label: b.label,
    note: b.name,
    tags: [
      b.made_on_site && { label: 'Grown on site', icon: Sprout },
      b.biodegradable && { label: 'Biodegradable', icon: Leaf },
    ].filter(Boolean),
  }));
  const regoliths = Object.entries(catalog.regoliths).map(([value, r]) => ({
    value,
    label: r.label,
    note: r.simulant,
    swatch: r.color,
    tags: [{ label: r.body === 'moon' ? 'Moon' : 'Mars', icon: r.body === 'moon' ? Moon : Orbit }],
  }));

  return (
    <section className="card controls" aria-labelledby="controls-title">
      <div className="card-head">
        <div>
          <p className="kicker">Step 1 · Design</p>
          <h2 id="controls-title">Material selection</h2>
        </div>
        <button type="button" className="icon-button" onClick={() => onChange(DEFAULT_COMPOSITION)} aria-label="Reset to the default mix" title="Reset">
          <RotateCcw size={16} />
        </button>
      </div>

      <OptionCards legend="Binder" name={nameBinder} value={composition.binder} options={binders} columns={2} onChange={(binder) => set({ binder })} />
      <OptionCards legend="Regolith" name={nameRegolith} value={composition.regolith} options={regoliths} columns={3} onChange={(regolith) => set({ regolith })} />

      <p className="group-label">Simulation parameters</p>
      <SliderControl
        label="Regolith content"
        value={composition.regolith_wt}
        onChange={setRegolithWt}
        min={catalog.ranges.regolith_wt[0]}
        max={catalog.ranges.regolith_wt[1]}
        unit="wt%"
        zones={LOADING_ZONES}
      />
      <SliderControl
        label="Basalt fibre"
        value={composition.fiber_wt}
        onChange={(fiber_wt) => set({ fiber_wt: Math.min(fiber_wt, fiberMax) })}
        min={catalog.ranges.fiber_wt[0]}
        max={catalog.ranges.fiber_wt[1]}
        unit="wt%"
        hint={fiberMax < catalog.ranges.fiber_wt[1] ? `Capped at ${fiberMax}% so total filler stays ≤ ${catalog.physics.max_total_filler_wt}%.` : 'Short fibres drawn from melted regolith basalt.'}
      />
      <SliderControl
        label="Grain size (median)"
        value={composition.particle_size}
        onChange={(particle_size) => set({ particle_size })}
        min={catalog.ranges.particle_size[0]}
        max={catalog.ranges.particle_size[1]}
        step={5}
        unit="µm"
        hint="Finer, sieved grains bond better but cost more processing."
      />
      <SliderControl
        label="Operating temperature"
        value={composition.temperature}
        onChange={(temperature) => set({ temperature })}
        min={catalog.ranges.temperature[0]}
        max={catalog.ranges.temperature[1]}
        unit="°C"
      >
        <div className="presets" role="group" aria-label="Temperature presets">
          {TEMPERATURE_PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              className={`chip-button ${composition.temperature === p.value ? 'active' : ''}`}
              aria-pressed={composition.temperature === p.value}
              onClick={() => set({ temperature: p.value })}
            >
              {p.label}
              <span>{p.value}°</span>
            </button>
          ))}
        </div>
      </SliderControl>

      <div className="controls-actions">
        <button type="button" className="button button-primary" onClick={onSave} disabled={!canSave}>
          {canSave ? <Plus size={16} aria-hidden="true" /> : <Check size={16} aria-hidden="true" />}
          {saveLabel}
        </button>
        <button type="button" className="button button-ghost" onClick={share}>
          {copied ? <Check size={16} aria-hidden="true" /> : <Link2 size={16} aria-hidden="true" />}
          {copied ? 'Link copied' : 'Share'}
        </button>
      </div>
    </section>
  );
}
