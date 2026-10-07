const VIDEO_URL = 'https://youtu.be/1Gtmq5XUytc';

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="brand">
        <svg className="brand-mark" viewBox="0 0 64 64" aria-hidden="true">
          <defs>
            <linearGradient id="brand-gradient" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0" stopColor="#ff4d1a" />
              <stop offset="0.5" stopColor="#ff8a1a" />
              <stop offset="1" stopColor="#2f7bff" />
            </linearGradient>
          </defs>
          <path d="M18 14 L46 50 M46 14 L18 50" stroke="url(#brand-gradient)" strokeWidth="7" strokeLinecap="round" />
        </svg>
        <div>
          <p className="brand-title">Moon-Material Simulator</p>
          <p className="brand-sub">Dreams of X · NASA Space Apps 2026</p>
        </div>
      </div>
      <a className="button button-ghost" href={VIDEO_URL} target="_blank" rel="noreferrer">
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
          <path fill="currentColor" d="M8 5.5v13l11-6.5z" />
        </svg>
        Watch the pitch
      </a>
    </header>
  );
}
