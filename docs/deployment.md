# Deployment

[← Back to README](../README.md) · Workflow: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml)

The live site is <https://md8-habibullah.github.io/moon-material-simulator/>. It is fully static: the Random Forest
runs in the browser, so GitHub Pages (free) is enough.

## One-time setup

1. On GitHub, open **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**. "Deploy from a branch" would only show this
   README, not the app.
3. Push to `main` (or run the workflow from the **Actions** tab). The site updates in about two minutes.

## What the workflow does

1. Installs Python and runs `pytest`: API contract, science-vs-NASA checks and export parity.
2. Runs `python -m scripts.export_frontend` to retrain the forest and refresh the model, catalog, parity fixtures and
   NASA NTRS snapshot in `frontend/src/generated/`. If NTRS is down, the committed snapshot is kept.
3. Installs Node, runs `npm test` (the browser engine must match Python) and `npm run build` with
   `VITE_BASE=/<repo-name>/`.
4. Publishes `frontend/dist` to GitHub Pages.

Pull requests run steps 1–3 without publishing. Third-party actions are pinned to commit SHAs.

## Run locally

```bash
cd frontend && npm install && npm run dev                 # http://127.0.0.1:5173
cd backend && uvicorn main:app --reload --port 8000       # optional: API + live NTRS search
```

The Vite dev server proxies `/api` to the backend. Both bind to `127.0.0.1` only.

## Preview the production build

```bash
cd frontend
VITE_BASE=/moon-material-simulator/ npm run build
npx vite preview --base /moon-material-simulator/
```
