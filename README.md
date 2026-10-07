<p align="center">
  <img src="docs/assets/dreams-of-x-logo.jpeg" alt="Dreams of X logo" width="120" />
</p>

<h1 align="center">Moon-Material Simulator</h1>

<p align="center">
  Design a building material from moon dust, then see how it holds up.<br />
  <strong>Team Dreams of X · NASA Space Apps Challenge 2026</strong>
</p>

<p align="center">
  <a href="https://youtu.be/1Gtmq5XUytc">▶ Watch our 240-second pitch</a>
</p>

---

## What it is

Future bases on the Moon and Mars can't ship every brick from Earth. One promising idea is to mix
local **regolith** (moon or Mars dust) with a **polymer binder**, including biodegradable ones such as
PLA, and 3D-print parts on site.

Moon-Material Simulator is an interactive web app for exploring that design space. Pick a polymer,
choose lunar or Martian regolith, set how much regolith goes in and the temperature the part has to
survive, and a machine-learning model predicts the composite's properties in real time.

### Features

- **Real-time property prediction:** tensile strength, elastic modulus, compressive strength and
  maximum service temperature, each with an uncertainty band.
- **"vs pure polymer" deltas** that show what the regolith adds or costs.
- **Environment check:** does the mix hold its shape at lunar noon (127 °C) or on a Martian day?
- **3D microstructure view** (three.js): grain count follows the filler volume fraction.
- **Comparison mode:** save up to four mixes and compare them on one chart and table.

## Project status

This is an **early prototype**. The model is trained on a **synthetic, physics-informed dataset**
(classic particulate-composite models with lab-like scatter added), not on measured coupon data yet.
Treat the numbers as plausible trends, not design values. See
[docs/data_dictionary.md](docs/data_dictionary.md) for every assumption and
[backend/data/data_sources.md](backend/data/data_sources.md) for the sources we plan to calibrate against.

## Tech stack

| Layer | Tools |
| --- | --- |
| Frontend | React 19, Vite 8, three.js, Chart.js (react-chartjs-2) |
| Backend | Python 3, FastAPI, Pydantic |
| Machine learning | scikit-learn `RandomForestRegressor`, pandas, NumPy |

## Run it locally

You need Python 3.11+ and Node.js 20+.

```bash
# 1. Backend (http://127.0.0.1:8000)
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 2. Frontend (http://127.0.0.1:5173), in a second terminal
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to the backend. The model trains from
`backend/data/regolith_composites.csv` at startup (about a second), so no model file needs downloading.

Run the backend tests:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness and model readiness |
| `GET` | `/api/options` | Polymers, regolith types, input ranges, environment temperatures |
| `GET` | `/api/model` | Hold-out R² / MAE per property and feature importance |
| `POST` | `/api/predict` | Predict properties for one composition |
| `POST` | `/api/compare` | Predict up to 6 compositions in one call |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"regolith_wt": 30, "regolith_type": "lunar", "polymer_type": "PLA", "temperature": 23}'
```

Interactive docs are at `http://127.0.0.1:8000/docs` while the backend runs.

## Project structure

```text
moon-material-simulator/
├── backend/
│   ├── main.py                    # FastAPI app and routes
│   ├── config.py                  # Settings (paths, CORS origins)
│   ├── models/property_model.py   # Random Forest training + prediction with uncertainty
│   ├── utils/materials.py         # Reference properties and physics heuristics
│   ├── utils/data_processor.py    # Feature encoding shared by training and the API
│   ├── data/generate_dataset.py   # Builds the synthetic training set
│   ├── data/regolith_composites.csv
│   └── tests/test_api.py
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/            # Navbar, SliderControl, PredictionCard, ThreeDViewer, ComparisonMode
│       └── lib/                   # API client and display metadata
└── docs/
    ├── architecture.md
    ├── data_dictionary.md
    └── demo_script.md
```

## Roadmap

1. Calibrate the model against measured polymer–regolith coupon data from NASA technical reports and
   published simulant studies.
2. Add more binders (PHA, PEI) and regolith simulant variants.
3. Model print-process effects (layer adhesion, porosity) and radiation ageing.
4. Export a material card (JSON/PDF) for a chosen mix.

## Team: Dreams of X

- Mahdin Islam Mukim (Team Lead)
- Yousuf Abdullah (Data Scientist)
- Md. Habibullah Sharif (Systems Architect)
- Maliha Sanjana (UI/UX Designer)
- Lamisa Yeasmin Nakia (Research & Storytelling Lead)

## License

[MIT](LICENSE)
