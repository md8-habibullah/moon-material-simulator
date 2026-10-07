import { GitBranch } from 'lucide-react';
import catalog, { DOCS, REPO_URL, TEAM, VIDEO_URL, docUrl } from '../lib/catalog';
import { BrandMark } from './Navbar';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <div className="brand">
            <BrandMark />
            <span>
              <span className="brand-title">Moon-Material Simulator</span>
              <span className="brand-sub">Team Dreams of X · NASA Space Apps Challenge 2026</span>
            </span>
          </div>
          <p>
            Model values are estimates for exploring a design space, not qualified design data. Built on public NASA research:{' '}
            {catalog.sources.length} sources, {catalog.validation.length} measurements.
          </p>
          <p className="footer-links">
            <a href={REPO_URL} target="_blank" rel="noreferrer">
              <GitBranch size={14} aria-hidden="true" /> Source on GitHub
            </a>
            <a href={VIDEO_URL} target="_blank" rel="noreferrer">
              Pitch video
            </a>
            <a href={docUrl('LICENSE')} target="_blank" rel="noreferrer">
              MIT License
            </a>
          </p>
        </div>
        <nav aria-label="Documentation">
          <p className="group-label">Documentation</p>
          <ul>
            {DOCS.map((d) => (
              <li key={d.path}>
                <a href={docUrl(d.path)} target="_blank" rel="noreferrer">
                  {d.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div>
          <p className="group-label">Team</p>
          <ul className="team">
            {TEAM.map((m) => (
              <li key={m.name}>
                <strong>{m.name}</strong>
                <small>{m.role}</small>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}
