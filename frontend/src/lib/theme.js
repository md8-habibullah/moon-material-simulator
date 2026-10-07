import { useEffect, useState } from 'react';

const KEY = 'mms-theme';
const OPTIONS = ['system', 'light', 'dark'];

export function storedTheme() {
  try {
    const value = localStorage.getItem(KEY);
    return OPTIONS.includes(value) ? value : 'system';
  } catch {
    return 'system';
  }
}

export function applyTheme(preference) {
  const root = document.documentElement;
  if (preference === 'system') root.removeAttribute('data-theme');
  else root.setAttribute('data-theme', preference);
  try {
    localStorage.setItem(KEY, preference);
  } catch {
    // Private mode or blocked storage: the choice just won't persist.
  }
}

export function useThemePreference() {
  const [preference, setPreference] = useState(storedTheme);
  useEffect(() => applyTheme(preference), [preference]);
  return [preference, setPreference];
}

const readVar = (styles, name) => styles.getPropertyValue(name).trim();

function readColors() {
  const s = getComputedStyle(document.documentElement);
  return {
    text: readVar(s, '--text'),
    muted: readVar(s, '--muted'),
    grid: readVar(s, '--chart-grid'),
    surface: readVar(s, '--surface'),
    accent: readVar(s, '--chart-accent'),
    accentSoft: readVar(s, '--chart-accent-soft'),
    zone: readVar(s, '--chart-zone'),
    series: [1, 2, 3, 4].map((i) => readVar(s, `--series-${i}`)),
    nasa: readVar(s, '--nasa'),
    ok: readVar(s, '--ok'),
    warn: readVar(s, '--warn'),
  };
}

/** Resolved CSS colours for canvases (Chart.js, three.js), refreshed when theme or accent changes. */
export function useThemeColors() {
  const [colors, setColors] = useState(readColors);
  useEffect(() => {
    const update = () => requestAnimationFrame(() => setColors(readColors()));
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'data-accent'] });
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    media.addEventListener('change', update);
    return () => {
      observer.disconnect();
      media.removeEventListener('change', update);
    };
  }, []);
  return colors;
}
