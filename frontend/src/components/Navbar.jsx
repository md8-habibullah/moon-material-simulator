import { BookOpen, ChevronDown, GitBranch, Menu, Monitor, Moon, Play, Sun } from 'lucide-react';
import { DOCS, REPO_URL, VIDEO_URL, docUrl } from '../lib/catalog';

const LINKS = [
  { href: '#simulator', label: 'Simulator' },
  { href: '#optimize', label: 'Optimize' },
  { href: '#compare', label: 'Compare' },
  { href: '#impact', label: 'Impact' },
  { href: '#science', label: 'Science' },
  { href: '#research', label: 'NASA research' },
];
const THEMES = [
  { id: 'system', label: 'System theme', icon: Monitor },
  { id: 'light', label: 'Light theme', icon: Sun },
  { id: 'dark', label: 'Dark theme', icon: Moon },
];

export function BrandMark() {
  return (
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
  );
}

function DocsMenu() {
  return (
    <details className="menu">
      <summary className="button button-ghost button-small">
        <BookOpen size={15} aria-hidden="true" /> Docs <ChevronDown size={14} aria-hidden="true" />
      </summary>
      <div className="menu-panel" role="menu">
        {DOCS.map((d) => (
          <a key={d.path} role="menuitem" href={docUrl(d.path)} target="_blank" rel="noreferrer">
            <strong>{d.label}</strong>
            <small>{d.note}</small>
          </a>
        ))}
        <a role="menuitem" href={REPO_URL} target="_blank" rel="noreferrer" className="menu-footer">
          <GitBranch size={14} aria-hidden="true" /> Source code on GitHub
        </a>
      </div>
    </details>
  );
}

export default function Navbar({ theme, onTheme }) {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <a href="#top" className="brand">
          <BrandMark />
          <span>
            <span className="brand-title">Moon-Material Simulator</span>
            <span className="brand-sub">Dreams of X · NASA Space Apps 2026</span>
          </span>
        </a>

        <nav className="nav-links" aria-label="Sections">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href}>
              {l.label}
            </a>
          ))}
        </nav>

        <div className="nav-actions">
          <div className="theme-switch" role="radiogroup" aria-label="Colour theme">
            {THEMES.map((t) => (
              <button key={t.id} type="button" role="radio" aria-checked={theme === t.id} aria-label={t.label} title={t.label} className={theme === t.id ? 'active' : ''} onClick={() => onTheme(t.id)}>
                <t.icon size={15} />
              </button>
            ))}
          </div>
          <DocsMenu />
          <a className="button button-primary button-small hide-sm" href={VIDEO_URL} target="_blank" rel="noreferrer">
            <Play size={14} aria-hidden="true" /> Pitch
          </a>
          <details className="menu mobile-nav">
            <summary className="icon-button" aria-label="Open section menu">
              <Menu size={18} />
            </summary>
            <div className="menu-panel" role="menu">
              {LINKS.map((l) => (
                <a key={l.href} role="menuitem" href={l.href} onClick={(e) => e.currentTarget.closest('details').removeAttribute('open')}>
                  <strong>{l.label}</strong>
                </a>
              ))}
              <a role="menuitem" href={VIDEO_URL} target="_blank" rel="noreferrer">
                <strong>Watch the pitch</strong>
              </a>
            </div>
          </details>
        </div>
      </div>
    </header>
  );
}
