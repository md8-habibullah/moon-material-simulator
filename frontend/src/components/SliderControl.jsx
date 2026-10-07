import { useId } from 'react';

export default function SliderControl({ label, value, onChange, min, max, step = 1, unit, zones = [], hint, children }) {
  const id = useId();
  const hintId = useId();
  const pct = (v) => ((v - min) / (max - min)) * 100;

  return (
    <div className="field">
      <div className="field-head">
        <label htmlFor={id}>{label}</label>
        <output htmlFor={id} className="field-value">
          {value}
          <span>{unit}</span>
        </output>
      </div>
      <div className="slider-track">
        {zones.map((z) => (
          <span key={z.label} className="slider-zone" style={{ left: `${pct(z.from)}%`, width: `${pct(z.to) - pct(z.from)}%` }}>
            <span>{z.label}</span>
          </span>
        ))}
        <input
          id={id}
          type="range"
          className="slider"
          min={min}
          max={max}
          step={step}
          value={value}
          aria-describedby={hint ? hintId : undefined}
          style={{ '--fill': `${pct(value)}%` }}
          onChange={(e) => onChange(Number(e.target.value))}
        />
      </div>
      <div className="slider-scale" aria-hidden="true">
        <span>
          {min}
          {unit}
        </span>
        <span>
          {max}
          {unit}
        </span>
      </div>
      {hint && (
        <p id={hintId} className="field-hint">
          {hint}
        </p>
      )}
      {children}
    </div>
  );
}
