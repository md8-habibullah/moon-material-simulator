"""Random Forest that predicts seven composite properties from a composition.

Hybrid design:
1. The forest learns composition -> room-temperature properties, as log-ratios to the pure binder
   (so binder scale and temperature don't swamp subtler effects like regolith type and grain size).
2. Temperature is applied afterwards with explicit physics (`temperature_factors`): NASA's measured
   77 K ratios on the cold side, softening around the predicted max service temperature on the hot.

Each tree's output goes through both steps before averaging, so the spread across trees is a
rough uncertainty band in real units. `export()` writes the same forest as JSON for the browser.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from config import DATA_PATH, RANDOM_SEED
from utils.data_processor import FEATURE_COLUMNS, TARGET_COLUMNS, encode_frame, encode_rows
from utils.materials import binder_baseline, temperature_factors

FOREST_PARAMS = {"n_estimators": 28, "max_depth": 12, "min_samples_leaf": 5, "random_state": RANDOM_SEED, "n_jobs": -1}


def _baselines(binders) -> np.ndarray:
    """Pure-binder room-temperature values, shape (n_rows, n_targets)."""
    return np.array([[binder_baseline(b)[t] for t in TARGET_COLUMNS] for b in binders])


@dataclass
class PropertyModel:
    forest: RandomForestRegressor
    z_mean: np.ndarray
    z_std: np.ndarray
    metrics: dict = field(default_factory=dict)
    training_rows: int = 0

    @classmethod
    def train(cls, data_path=DATA_PATH) -> "PropertyModel":
        df = pd.read_csv(data_path)
        X = encode_frame(df)
        base = _baselines(df["binder"])
        y = np.log(df[TARGET_COLUMNS].to_numpy() / base)
        idx_train, idx_test = train_test_split(np.arange(len(df)), test_size=0.2, random_state=RANDOM_SEED)

        z_mean, z_std = y[idx_train].mean(axis=0), y[idx_train].std(axis=0)
        forest = RandomForestRegressor(**FOREST_PARAMS)
        forest.fit(X[idx_train], (y[idx_train] - z_mean) / z_std)
        model = cls(forest=forest, z_mean=z_mean, z_std=z_std, training_rows=len(idx_train))

        y_true = df[TARGET_COLUMNS].to_numpy()[idx_test]
        y_pred = model._room_temperature(X[idx_test], base[idx_test]).mean(axis=0)
        model.metrics = {
            target: {
                "r2": round(float(r2_score(y_true[:, i], y_pred[:, i])), 4),
                "mae": round(float(mean_absolute_error(y_true[:, i], y_pred[:, i])), 4),
            }
            for i, target in enumerate(TARGET_COLUMNS)
        }
        return model

    def _room_temperature(self, X: np.ndarray, base: np.ndarray) -> np.ndarray:
        """Per-tree room-temperature predictions, shape (n_trees, n_rows, n_targets)."""
        z = np.stack([tree.predict(X) for tree in self.forest.estimators_])
        return np.exp(z * self.z_std + self.z_mean) * base

    def predict_many(self, rows: list[dict]) -> list[dict]:
        """Rows need binder, regolith, regolith_wt, fiber_wt, particle_size and temperature."""
        per_tree = self._room_temperature(encode_rows(rows), _baselines(r["binder"] for r in rows))
        hdt_col = TARGET_COLUMNS.index("max_service_temp")
        for j, row in enumerate(rows):
            for k in range(per_tree.shape[0]):
                factors = temperature_factors(row["binder"], per_tree[k, j, hdt_col], row["temperature"])
                per_tree[k, j] *= [factors[t] for t in TARGET_COLUMNS]
        mean, std = per_tree.mean(axis=0), per_tree.std(axis=0)
        return [
            {
                "properties": {t: round(float(mean[j, i]), 4) for i, t in enumerate(TARGET_COLUMNS)},
                "uncertainty": {t: round(float(std[j, i]), 4) for i, t in enumerate(TARGET_COLUMNS)},
            }
            for j in range(len(rows))
        ]

    def feature_importance(self) -> dict:
        return {name: round(float(v), 4) for name, v in zip(FEATURE_COLUMNS, self.forest.feature_importances_)}

    def export(self) -> dict:
        """Compact JSON form of the forest for the browser engine (frontend/src/lib/engine)."""
        trees = []
        for est in self.forest.estimators_:
            t = est.tree_
            n_leaves = 0
            features, thresholds, left, right, values = [], [], [], [], []
            for node in range(t.node_count):
                if t.children_left[node] == -1:
                    features.append(-1)
                    thresholds.append(0)
                    left.append(n_leaves)
                    right.append(-1)
                    values.extend(round(float(v), 5) for v in t.value[node][:, 0])
                    n_leaves += 1
                else:
                    features.append(int(t.feature[node]))
                    # Full float64 precision: sklearn compares float32(x) <= threshold.
                    thresholds.append(float(t.threshold[node]))
                    left.append(int(t.children_left[node]))
                    right.append(int(t.children_right[node]))
            trees.append({"f": features, "t": thresholds, "l": left, "r": right, "v": values})
        return {
            "version": 3,
            "features": FEATURE_COLUMNS,
            "targets": TARGET_COLUMNS,
            "transform": {
                "type": "log-ratio-to-binder, standardized",
                "mean": [round(float(v), 10) for v in self.z_mean],
                "std": [round(float(v), 10) for v in self.z_std],
            },
            "trees": trees,
        }
