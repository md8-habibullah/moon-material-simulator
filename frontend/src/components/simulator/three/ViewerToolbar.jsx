import { useEffect, useState, useSyncExternalStore } from 'react';
import { Maximize2, Minimize2, RotateCcw, Volume2, VolumeX, ZoomIn, ZoomOut } from 'lucide-react';
import { sound } from '../../../lib/sound';

export function useSoundEnabled() {
  return useSyncExternalStore(sound.subscribe, () => sound.enabled, () => false);
}

// Floating buttons over a 3D view: camera reset, zoom, fullscreen (for recording) and sound.
export default function ViewerToolbar({ stageRef, wrapRef, children }) {
  const soundOn = useSoundEnabled();
  const [full, setFull] = useState(false);

  useEffect(() => {
    const onChange = () => {
      const isFull = document.fullscreenElement === wrapRef.current;
      setFull(isFull);
      stageRef.current?.setWheelZoom(isFull);
    };
    document.addEventListener('fullscreenchange', onChange);
    return () => document.removeEventListener('fullscreenchange', onChange);
  }, [stageRef, wrapRef]);

  const toggleFull = () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else wrapRef.current?.requestFullscreen?.().catch(() => {});
  };

  return (
    <div className="viewer-toolbar" role="toolbar" aria-label="3D view controls">
      {children}
      <button type="button" onClick={() => stageRef.current?.zoom(0.75)} aria-label="Zoom in" title="Zoom in">
        <ZoomIn size={16} aria-hidden="true" />
      </button>
      <button type="button" onClick={() => stageRef.current?.zoom(1.33)} aria-label="Zoom out" title="Zoom out">
        <ZoomOut size={16} aria-hidden="true" />
      </button>
      <button type="button" onClick={() => stageRef.current?.resetView()} aria-label="Reset view" title="Reset view">
        <RotateCcw size={16} aria-hidden="true" />
      </button>
      {document.fullscreenEnabled && (
        <button type="button" onClick={toggleFull} aria-label={full ? 'Exit full screen' : 'Full screen'} title={full ? 'Exit full screen' : 'Full screen (good for recording)'}>
          {full ? <Minimize2 size={16} aria-hidden="true" /> : <Maximize2 size={16} aria-hidden="true" />}
        </button>
      )}
      <button
        type="button"
        className={soundOn ? 'on' : ''}
        onClick={() => sound.setEnabled(!soundOn)}
        aria-pressed={soundOn}
        aria-label={soundOn ? 'Turn sound off' : 'Turn sound on'}
        title={soundOn ? 'Sound on' : 'Sound off'}
      >
        {soundOn ? <Volume2 size={16} aria-hidden="true" /> : <VolumeX size={16} aria-hidden="true" />}
      </button>
    </div>
  );
}
