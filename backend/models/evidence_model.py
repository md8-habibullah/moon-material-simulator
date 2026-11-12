"""Evidence correction: how far real lab measurements sit from the physics model, learned with a GP.

The physics model (utils/materials.py) gives every composition a prior. Real coupons differ from
it in ways the physics doesn't capture: how the part was made (printed filament, printed pellets,
injection molded, hot-pressed, cold-compacted and sintered), how well a binder wets the grains, and
lab-to-lab scatter. For each property we learn that difference in log space:

    log(measured) = log(physics(x)) + δ(x) + noise,     δ ~ GP(0, k)

from every usable measurement in data/evidence/measurements.csv. Far from any data, δ falls back to 0,
so the prediction falls back to physics and the uncertainty grows. That is the honest behaviour we want.

Kernel on x = (φ = filler volume fraction, binder, process), with r(φ, φ') = exp(-(φ-φ')² / 2ℓ²):

    k = s_all²·r  +  s_binder²·r·[same binder]  +  s_process²·r·[same process]
      + s_pair²·r·[same binder and process]

so effects are shared across everything, per binder, per process and per binder-process pair; the
data decides how much of each (hyperparameters maximise the marginal likelihood). Each point's
noise is a fitted floor plus its own reported scatter (std/value).

Validation is leave-one-study-out: every source is predicted by a model that never saw it.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config import BASE_DIR
from utils.materials import BINDERS, PROCESSES, REGOLITHS, room_temperature_properties, volume_fractions

MEASUREMENTS = BASE_DIR / "data" / "evidence" / "measurements.csv"

# Simulator output -> the evidence property it is trained on.
TARGET_PROPERTY = {
    "tensile_strength": "tensile_strength",
    "elastic_modulus": "tensile_modulus",
    "compressive_strength": "compressive_strength",
    "elongation_at_break": "elongation_at_break",
    "density": "density",
    "thermal_conductivity": "thermal_conductivity",
    "max_service_temp": "hdt",
    "decomposition_temp": "decomposition_temp",
}
# Evidence process -> simulator process. "compression" usually means melt compression molding
# (NASA Glenn's PHB films); in S004 it means cold-compacted, then sintered bricks.
PROCESS_MAP = {
    "FFF": "fff", "pellet_AM": "pellet", "injection": "molded", "compression": "molded",
    "hot_press": "hot_pressed", "sinter": "sintered", "cold_sinter": "sintered",
}
PROCESS_OVERRIDES = {"S004": {"compression": "sintered"}}
# Evidence soil -> the simulator soil used for the physics prior (densities, grain stiffness).
SOIL_MAP = {
    "lunar_highlands": "lunar_highlands", "lunar_mare": "lunar_mare", "martian": "martian",
    "basalt": "lunar_mare",  # basalt moon dust is a mare-type basalt
    "lunar_generic": "lunar_mare",  # EAC-1A (basaltic) and VI-75: documented in docs/science_model.md
    "none": "lunar_highlands", "": "lunar_highlands",  # neat polymer: soil irrelevant at 0 wt%
}
ROOM_TEMP_RANGE = (15.0, 30.0)
PHI_GRID = np.round(np.arange(0.0, 0.9001, 0.025), 4)
MIN_POINTS = 8


def usable_measurements(path=MEASUREMENTS) -> pd.DataFrame:
    """Room-temperature, experimental, first-hand measurements that map onto the simulator's inputs."""
    m = pd.read_csv(path, dtype=str).fillna("")
    m["value_si"] = pd.to_numeric(m["value_si"], errors="coerce")
    m["std_si"] = pd.to_numeric(m["std_si"], errors="coerce")
    m["wt"] = pd.to_numeric(m["regolith_wt"], errors="coerce")
    filled = ~m["filler"].str.lower().isin(["", "none"])
    m["wt_known"] = m["wt"].notna() | ~filled  # a filled composite needs its filler content
    m["wt"] = m["wt"].fillna(0.0)
    m["fiber"] = pd.to_numeric(m["fiber_wt"], errors="coerce").fillna(0.0)
    m["temp"] = pd.to_numeric(m["temperature_c"], errors="coerce").fillna(23.0)
    m["binder_key"] = m["binder"].str.upper().str.strip()
    m["process_key"] = [
        PROCESS_OVERRIDES.get(sid, {}).get(proc, PROCESS_MAP.get(proc)) for sid, proc in zip(m["source_id"], m["process"])
    ]
    m.loc[(m["wt"] == 0) & m["process_key"].isna() & (m["model_property"] == "density"), "process_key"] = None
    keep = (
        (m["origin"] == "experimental") & (m["cited"] == "no") & (m["duplicate_of"] == "")
        & m["value_si"].notna() & (m["value_si"] > 0)
        & m["model_property"].isin(TARGET_PROPERTY.values())
        & m["binder_key"].isin(BINDERS) & m["process_key"].notna()
        & m["temp"].between(*ROOM_TEMP_RANGE)
        & (m["environment"] != "vacuum")  # vacuum-cured bricks (S004 Table A2) are a separate treatment
        & (m["confidence"] != "low")
        & m["wt_known"]
    )
    out = m[keep].copy()
    # The same chart can appear in two decks (NASA Glenn's S006 and S011): count a value once.
    out["dup_key"] = (out["binder_key"] + "|" + out["filler"].str.upper() + "|" + out["wt"].round(1).astype(str) + "|"
                      + out["process_key"] + "|" + out["model_property"] + "|" + out["environment"] + "|" + out["notes"].str.contains("quench", case=False).astype(str))
    kept = []
    for _, g in out.groupby("dup_key", sort=False):
        chosen = []
        for _, r in g.iterrows():
            if any(c["source_id"] != r["source_id"] and abs(c["value_si"] - r["value_si"]) <= 0.015 * abs(c["value_si"]) for c in chosen):
                continue  # near-identical value already taken from another source
            chosen.append(r)
        kept += [r.name for r in chosen]
    out = out.loc[kept]
    out["soil"] = out["soil_type"].map(SOIL_MAP).fillna("lunar_mare")
    out["phi"] = [
        sum(volume_fractions(min(w, 99.0), min(f, 99.0 - min(w, 99.0)), b, s))
        for w, f, b, s in zip(out["wt"], out["fiber"], out["binder_key"], out["soil"])
    ]
    return out.reset_index(drop=True)


def physics_value(row, target: str) -> float:
    d50 = pd.to_numeric(row.get("d50_um"), errors="coerce")
    size = float(d50) if d50 == d50 and d50 else 60.0
    props = room_temperature_properties(min(row["wt"], 99.0), min(row["fiber"], 1.0), min(max(size, 10.0), 150.0), row["soil"], row["binder_key"])
    return props[target]


# ------------------------------------------------------------------------- GP
@dataclass
class GP:
    """Small exact GP with the structured kernel described above."""
    params: np.ndarray  # log of [ell, s_all, s_binder, s_process, s_pair, noise]
    X_phi: np.ndarray
    X_b: np.ndarray
    X_p: np.ndarray
    y: np.ndarray
    extra_var: np.ndarray
    alpha: np.ndarray = None
    L: np.ndarray = None
    s_ref: float = 0.3  # typical size of a correction for this property (log units), from its own data

    @staticmethod
    def kernel(p, phi1, b1, p1, phi2, b2, p2):
        ell, s0, sb, sp, sbp = np.exp(p[:5])
        r = np.exp(-((phi1[:, None] - phi2[None, :]) ** 2) / (2 * ell**2))
        same_b = (b1[:, None] == b2[None, :]).astype(float)
        same_p = (p1[:, None] == p2[None, :]).astype(float)
        return r * (s0**2 + sb**2 * same_b + sp**2 * same_p + sbp**2 * same_b * same_p)

    def _nll(self, p):
        K = self.kernel(p, self.X_phi, self.X_b, self.X_p, self.X_phi, self.X_b, self.X_p)
        K[np.diag_indices_from(K)] += np.exp(p[5]) ** 2 + self.extra_var + 1e-8
        try:
            L = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            return 1e10
        a = np.linalg.solve(L.T, np.linalg.solve(L, self.y))
        nll = 0.5 * self.y @ a + np.log(np.diag(L)).sum()
        # Weak priors keep hyperparameters sensible with few points: lengthscale ~0.2 in φ; signal
        # scales near this property's typical correction (decomposition temperature moves ~1%,
        # compressive strength by factors), so an untested binder gets a ± that fits the property.
        ref = np.log(self.s_ref)
        prior = ((p[0] - np.log(0.2)) / 1.0) ** 2 + (((p[1:5] - ref) / 1.0) ** 2).sum() + ((p[5] - ref + np.log(2)) / 1.0) ** 2
        return nll + 0.5 * prior

    def fit(self, restarts: int = 4, seed: int = 0) -> "GP":
        rng = np.random.default_rng(seed)
        best = None
        for i in range(restarts):
            p0 = np.log([0.2, self.s_ref, self.s_ref, self.s_ref, self.s_ref, self.s_ref / 2]) + (rng.normal(0, 0.5, 6) if i else 0)
            res = minimize(self._nll, p0, method="L-BFGS-B", bounds=[(np.log(0.03), np.log(2.0))] + [(np.log(1e-3), np.log(3.0))] * 4 + [(np.log(0.002), np.log(1.0))])
            if best is None or res.fun < best.fun:
                best = res
        self.params = best.x
        K = self.kernel(self.params, self.X_phi, self.X_b, self.X_p, self.X_phi, self.X_b, self.X_p)
        K[np.diag_indices_from(K)] += np.exp(self.params[5]) ** 2 + self.extra_var + 1e-8
        self.L = np.linalg.cholesky(K)
        self.alpha = np.linalg.solve(self.L.T, np.linalg.solve(self.L, self.y))
        return self

    def predict(self, phi, b, p, include_noise: bool = True):
        Ks = self.kernel(self.params, np.asarray(phi, float), np.asarray(b), np.asarray(p), self.X_phi, self.X_b, self.X_p)
        mean = Ks @ self.alpha
        v = np.linalg.solve(self.L, Ks.T)
        prior = self.kernel(self.params, np.asarray(phi, float), np.asarray(b), np.asarray(p), np.asarray(phi, float), np.asarray(b), np.asarray(p)).diagonal()
        var = np.maximum(prior - (v**2).sum(axis=0), 1e-10)
        if include_noise:
            var = var + np.exp(self.params[5]) ** 2
        return mean, np.sqrt(var)


def _training_arrays(df: pd.DataFrame, target: str):
    prop = TARGET_PROPERTY[target]
    d = df[df["model_property"] == prop].copy()
    if d.empty:
        return d, None
    d["physics"] = [physics_value(r, target) for _, r in d.iterrows()]
    d = d[d["physics"] > 0]
    d["y"] = np.log(d["value_si"] / d["physics"])
    rel = (d["std_si"] / d["value_si"]).fillna(0.0).clip(upper=0.5)
    d["extra_var"] = np.log1p(rel) ** 2
    return d, prop


def fit_gp(d: pd.DataFrame) -> GP:
    return GP(
        params=None, X_phi=d["phi"].to_numpy(float), X_b=d["binder_key"].to_numpy(), X_p=d["process_key"].to_numpy(),
        y=d["y"].to_numpy(float), extra_var=d["extra_var"].to_numpy(float),
        s_ref=float(np.clip(np.sqrt(np.mean(d["y"].to_numpy(float) ** 2)), 0.01, 1.5)),
    ).fit()


def _errors(measured, predicted):
    measured, predicted = np.asarray(measured), np.asarray(predicted)
    return np.abs(predicted - measured) / measured


def leave_one_study_out(df: pd.DataFrame, target: str) -> dict | None:
    """Each source predicted by a GP fitted on the other sources only."""
    d, _ = _training_arrays(df, target)
    if d is None or len(d) < MIN_POINTS or d["source_id"].nunique() < 2:
        return None
    rows = []
    for sid in sorted(d["source_id"].unique()):
        train, test = d[d["source_id"] != sid], d[d["source_id"] == sid]
        if len(train) < 3:
            continue
        gp = fit_gp(train)
        mu, sd = gp.predict(test["phi"], test["binder_key"], test["process_key"])
        sd_total = np.sqrt(sd**2 + test["extra_var"].to_numpy())
        hybrid = test["physics"].to_numpy() * np.exp(mu)
        within = np.abs(np.log(test["value_si"].to_numpy() / hybrid)) <= 1.645 * sd_total
        for (_, r), h, w in zip(test.iterrows(), hybrid, within):
            rows.append({"source_id": sid, "measured": r["value_si"], "physics": r["physics"], "hybrid": h, "within90": bool(w)})
    if not rows:
        return None
    res = pd.DataFrame(rows)
    by_source = {
        sid: {
            "n": int(len(g)),
            "physics_mape": round(float(_errors(g["measured"], g["physics"]).mean()), 4),
            "hybrid_mape": round(float(_errors(g["measured"], g["hybrid"]).mean()), 4),
        }
        for sid, g in res.groupby("source_id")
    }
    return {
        "n": int(len(res)),
        "sources": int(res["source_id"].nunique()),
        "physics_mape": round(float(_errors(res["measured"], res["physics"]).mean()), 4),
        "hybrid_mape": round(float(_errors(res["measured"], res["hybrid"]).mean()), 4),
        "physics_median_ape": round(float(np.median(_errors(res["measured"], res["physics"]))), 4),
        "hybrid_median_ape": round(float(np.median(_errors(res["measured"], res["hybrid"]))), 4),
        "coverage90": round(float(res["within90"].mean()), 3),
        "by_source": by_source,
    }


def leave_one_mix_out(df: pd.DataFrame, target: str) -> dict | None:
    """Each tested mix (study × binder × process × filler level) predicted from all other rows.

    This is how the simulator is used: an untested mix of a material system that has been tested.
    """
    d, _ = _training_arrays(df, target)
    if d is None or len(d) < MIN_POINTS:
        return None
    d = d.assign(mix=d["source_id"] + "|" + d["binder_key"] + "|" + d["process_key"] + "|" + d["wt"].round(0).astype(str))
    rows = []
    for mix in d["mix"].unique():
        train, test = d[d["mix"] != mix], d[d["mix"] == mix]
        if len(train) < 3:
            continue
        gp = fit_gp(train)
        mu, sd = gp.predict(test["phi"], test["binder_key"], test["process_key"])
        sd_total = np.sqrt(sd**2 + test["extra_var"].to_numpy())
        hybrid = test["physics"].to_numpy() * np.exp(mu)
        within = np.abs(np.log(test["value_si"].to_numpy() / hybrid)) <= 1.645 * sd_total
        z = np.abs(np.log(test["value_si"].to_numpy() / hybrid)) / sd_total
        rows += [{"measured": r["value_si"], "physics": r["physics"], "hybrid": h, "within90": bool(w), "z": float(zz)} for (_, r), h, w, zz in zip(test.iterrows(), hybrid, within, z)]
    if not rows:
        return None
    res = pd.DataFrame(rows)
    return {
        "n": int(len(res)),
        "mixes": int(d["mix"].nunique()),
        "physics_mape": round(float(_errors(res["measured"], res["physics"]).mean()), 4),
        "hybrid_mape": round(float(_errors(res["measured"], res["hybrid"]).mean()), 4),
        "physics_median_ape": round(float(np.median(_errors(res["measured"], res["physics"]))), 4),
        "hybrid_median_ape": round(float(np.median(_errors(res["measured"], res["hybrid"]))), 4),
        "coverage90": round(float(res["within90"].mean()), 3),
        # Factor that widens the ± band until 90% of held-out mixes fall inside it (never narrows it).
        "calibration": round(float(max(1.0, np.quantile(res["z"], 0.9) / 1.645)), 3),
    }


@dataclass
class EvidenceModel:
    gps: dict  # target -> GP
    training: dict  # target -> DataFrame used
    validation: dict  # target -> LOSO metrics

    @classmethod
    def train(cls, path=MEASUREMENTS) -> "EvidenceModel":
        df = usable_measurements(path)
        gps, training, validation = {}, {}, {}
        for target in TARGET_PROPERTY:
            d, _ = _training_arrays(df, target)
            if d is None or len(d) < MIN_POINTS:
                continue
            gps[target] = fit_gp(d)
            training[target] = d
            loso, lomo = leave_one_study_out(df, target), leave_one_mix_out(df, target)
            validation[target] = {"new_study": loso, "new_mix": lomo}
        return cls(gps, training, validation)

    def calibration(self, target: str) -> float:
        v = (self.validation.get(target) or {}).get("new_mix") or {}
        return v.get("calibration", 1.0)

    def correction(self, target: str, phi: float, binder: str, process: str) -> tuple[float, float]:
        """(mean, std) of δ in log units at one point (0, 0 when the property has no evidence model)."""
        gp = self.gps.get(target)
        if gp is None:
            return 0.0, 0.0
        mu, sd = gp.predict([phi], [binder], [process])
        return float(mu[0]), float(sd[0]) * self.calibration(target)

    def support(self, target: str, phi: float, binder: str, process: str) -> dict:
        d = self.training.get(target)
        if d is None:
            return {"same": 0, "binder": 0}
        near = (d["phi"] - phi).abs() <= 0.08
        same_b = d["binder_key"] == binder
        return {"same": int((near & same_b & (d["process_key"] == process)).sum()), "binder": int((near & same_b).sum())}

    def export_grid(self) -> dict:
        """Correction on a φ grid for every binder × process: the browser interpolates it (and so does Python)."""
        out = {"phi": PHI_GRID.tolist(), "targets": {}}
        for target, gp in self.gps.items():
            table = {}
            for b in BINDERS:
                for p in PROCESSES:
                    mu, sd = gp.predict(PHI_GRID, [b] * len(PHI_GRID), [p] * len(PHI_GRID))
                    sd = sd * self.calibration(target)
                    sup = [self.support(target, float(x), b, p) for x in PHI_GRID]
                    table[f"{b}|{p}"] = {
                        "mean": [round(float(v), 4) for v in mu],
                        "std": [round(float(v), 4) for v in sd],
                        "same": [s["same"] for s in sup],
                        "binder": [s["binder"] for s in sup],
                    }
            ell, s0, sb, sp, sbp, noise = np.exp(gp.params)
            out["targets"][target] = {
                "property": TARGET_PROPERTY[target],
                "n_train": int(len(self.training[target])),
                "calibration": self.calibration(target),
                "validation": self.validation.get(target),
                "sources": sorted(self.training[target]["source_id"].unique().tolist()),
                "hyper": {k: round(float(v), 4) for k, v in zip(("ell", "s_all", "s_binder", "s_process", "s_pair", "noise"), (ell, s0, sb, sp, sbp, noise))},
                "table": table,
            }
        return out


def interpolate(grid: dict, target: str, binder: str, process: str, phi: float) -> tuple[float, float, int, int]:
    """Same linear interpolation the browser uses (frontend/src/lib/engine/evidence.js)."""
    t = grid["targets"].get(target)
    if not t:
        return 0.0, 0.0, 0, 0
    cell = t["table"][f"{binder}|{process}"]
    xs = grid["phi"]
    x = min(max(phi, xs[0]), xs[-1])
    i = min(int((x - xs[0]) / (xs[1] - xs[0])), len(xs) - 2)
    f = (x - xs[i]) / (xs[i + 1] - xs[i])
    lerp = lambda arr: arr[i] * (1 - f) + arr[i + 1] * f
    nearest = i if f < 0.5 else i + 1
    return lerp(cell["mean"]), lerp(cell["std"]), cell["same"][nearest], cell["binder"][nearest]
