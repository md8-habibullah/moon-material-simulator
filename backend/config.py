"""Runtime settings, read from environment variables with safe defaults."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "regolith_composites.csv"

RANDOM_SEED = 42

# Browser origins allowed to call the API (comma-separated). The Vite dev server proxies
# /api, so this only matters when the frontend is hosted somewhere else.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

MAX_COMPARE_ITEMS = 6
