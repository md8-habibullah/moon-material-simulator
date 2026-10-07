"""Random Forest model that predicts composite properties from a composition.

The model trains from data/regolith_composites.csv at startup (about a second), so no
binary model file is committed and nothing is unpickled from disk.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from config import DATA_PATH, RANDOM_SEED
from utils.data_processor import FEATURE_COLUMNS, TARGET_COLUMNS, encode_frame, encode_one


@dataclass
class PropertyModel:
    forest: RandomForestRegressor
    metrics: dict = field(default_factory=dict)
    training_rows: int = 0

    @classmethod
    def train(cls, data_path=DATA_PATH) -> "PropertyModel":
        df = pd.read_csv(data_path)
        X = encode_frame(df)
        y = df[TARGET_COLUMNS].to_numpy()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)

        forest = RandomForestRegressor(n_estimators=150, min_samples_leaf=2, random_state=RANDOM_SEED, n_jobs=-1)
        forest.fit(X_train, y_train)

        y_pred = forest.predict(X_test)
        metrics = {
            target: {
                "r2": round(float(r2_score(y_test[:, i], y_pred[:, i])), 4),
                "mae": round(float(mean_absolute_error(y_test[:, i], y_pred[:, i])), 3),
            }
            for i, target in enumerate(TARGET_COLUMNS)
        }
        return cls(forest=forest, metrics=metrics, training_rows=len(X_train))

    def predict(self, regolith_wt: float, regolith_type: str, polymer_type: str, temperature: float) -> dict:
        """Mean prediction plus the spread across trees as a rough uncertainty band."""
        x = encode_one(regolith_wt, regolith_type, polymer_type, temperature)
        per_tree = np.stack([tree.predict(x)[0] for tree in self.forest.estimators_])
        mean, std = per_tree.mean(axis=0), per_tree.std(axis=0)
        return {
            "properties": {t: round(float(mean[i]), 2) for i, t in enumerate(TARGET_COLUMNS)},
            "uncertainty": {t: round(float(std[i]), 2) for i, t in enumerate(TARGET_COLUMNS)},
        }

    def feature_importance(self) -> dict:
        return {name: round(float(v), 4) for name, v in zip(FEATURE_COLUMNS, self.forest.feature_importances_)}
