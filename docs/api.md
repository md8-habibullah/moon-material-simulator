# API reference

[← Back to README](../README.md) · Code: [`backend/main.py`](../backend/main.py)

The FastAPI backend serves the same model the website runs in the browser, plus live NASA NTRS search. Start it with:

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Interactive docs are at <http://127.0.0.1:8000/docs>.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | `{"status": "ok", "model_ready": true}` |
| `GET` | `/api/catalog` | Materials, uses, ranges, physics constants, model metrics, NASA validation, sources |
| `GET` | `/api/model` | Algorithm, parameters, hold-out R²/MAE, feature importance |
| `GET` | `/api/validation` | NASA measurements next to the model's predictions |
| `POST` | `/api/predict` | Predict one composition |
| `POST` | `/api/compare` | Predict up to 6 compositions |
| `GET` | `/api/research?q=` | Live NASA NTRS search (2–100 characters) |

## `POST /api/predict`

```bash
curl -X POST http://127.0.0.1:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"binder": "PHB", "regolith": "lunar_highlands", "regolith_wt": 50, "fiber_wt": 0, "particle_size": 60, "temperature": 20}'
```

Response (abridged):

```json
{
  "inputs": {"binder": "PHB", "regolith": "lunar_highlands", "regolith_wt": 50.0, "fiber_wt": 0.0, "particle_size": 60.0, "temperature": 20.0},
  "properties": {"tensile_strength": 20.2, "elastic_modulus": 7.6, "max_service_temp": 115.5, "decomposition_temp": 276.6, "...": "..."},
  "uncertainty": {"tensile_strength": 0.3, "...": "..."},
  "units": {"tensile_strength": "MPa", "...": "..."},
  "in_situ_fraction": 1.0
}
```

`binder` defaults to `PHB`, `fiber_wt` to 0, `particle_size` to 60 and `temperature` to 23.

## Errors

| Status | When |
| --- | --- |
| `422` | Out-of-range or unknown input (for example `regolith_wt + fiber_wt > 85`, or binder `ABS`) |
| `502` | NTRS didn't answer (`/api/research` only). The message is generic; details stay in server logs. |

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Browser origins allowed by CORS |
