import { useCallback, useEffect, useState } from 'react';
import forestUrl from '../../generated/forest.json?url';
import catalog from '../../generated/catalog.json';
import { createEngine } from './forest.js';

let pending = null;

function loadEngine() {
  if (!pending) {
    pending = fetch(forestUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`Model download failed (${res.status})`);
        return res.json();
      })
      .then((forest) => createEngine(forest, catalog))
      .catch((err) => {
        pending = null; // allow a retry
        throw err;
      });
  }
  return pending;
}

/** The in-browser Random Forest, downloaded once (~0.5 MB gzipped) and shared by every panel. */
export function useEngine() {
  const [state, setState] = useState({ engine: null, error: null });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    loadEngine()
      .then((engine) => alive && setState({ engine, error: null }))
      .catch((error) => alive && setState({ engine: null, error }));
    return () => {
      alive = false;
    };
  }, [attempt]);

  const retry = useCallback(() => {
    setState({ engine: null, error: null });
    setAttempt((n) => n + 1);
  }, []);

  return { ...state, retry };
}
