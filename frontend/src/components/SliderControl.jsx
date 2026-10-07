import { useId } from 'react';

export default function SliderControl({ label, value, onChange, min, max, step = 1, unit, children }) {
  const id = useId();
  const fill = ((value - min) / (max - min)) * 100;

  return (
    <div className="field">
      <div className="field-head">
        <label htmlFor={id}>{label}</label>
        <output htmlFor={id} className="field-value">
          {value}
          <span>{unit}</span>
        </output>
      </div>
      <input
        id={id}
        type="range"
        className="slider"
        min={min}
        max={max}
        step={step}
        value={value}
        style={{ '--fill': `${fill}%` }}
        onChange={(e) => onChange(Number(e.target.value))}
      />
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
      {children}
    </div>
  );
}

export function SegmentedControl({ label, value, options, onChange }) {
  const name = useId();
  return (
    <fieldset className="field">
      <legend>{label}</legend>
      <div className="segmented">
        {options.map((opt) => (
          <label key={opt.value} className="segment">
            <input type="radio" name={name} value={opt.value} checked={value === opt.value} onChange={() => onChange(opt.value)} />
            <span>
              <strong>{opt.label}</strong>
              {opt.note && <small>{opt.note}</small>}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
