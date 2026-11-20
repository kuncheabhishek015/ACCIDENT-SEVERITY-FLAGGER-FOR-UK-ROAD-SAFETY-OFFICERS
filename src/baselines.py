"""
Non-ML Baseline Models
Provides benchmark non-ML baseline classifiers for comparison against machine learning models:
1. Predict-Majority-Class Baseline
2. Group-By Road-Type Majority Baseline
"""

import numpy as np
import pandas as pd


class MajorityClassBaseline:
    """Baseline 1: Always predicts the overall majority class (Slight / 0)."""

    def __init__(self):
        self.majority_class = 0

    def fit(self, X: pd.DataFrame, y: pd.Series):
        # Identify majority class in training set
        counts = y.value_counts()
        self.majority_class = int(counts.idxmax())

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(len(X), self.majority_class)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        # Returns probability matrix [P(0), P(1)]
        proba_1 = 1.0 if self.majority_class == 1 else 0.0
        probas = np.zeros((len(X), 2))
        probas[:, self.majority_class] = 1.0
        return probas


class GroupByRoadTypeBaseline:
    """Baseline 2: Predicts severity based on group-by road type historical severity majority rate."""

    def __init__(self, threshold: float = 0.25):
        self.threshold = threshold
        self.road_type_rates = {}
        self.global_default_rate = 0.26

    def fit(self, X: pd.DataFrame, y: pd.Series):
        df = X.copy()
        df['target'] = y
        self.global_default_rate = float(y.mean())
        
        rates = df.groupby('road_type')['target'].mean().to_dict()
        self.road_type_rates = rates

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        road_types = X['road_type'] if 'road_type' in X.columns else X.iloc[:, 0]
        
        probas_1 = road_types.map(self.road_type_rates).fillna(self.global_default_rate).values
        probas_0 = 1.0 - probas_1
        
        return np.column_stack([probas_0, probas_1])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        probas = self.predict_proba(X)
        return (probas[:, 1] >= self.threshold).astype(int)


if __name__ == '__main__':
    from decoder import Stats19Decoder
    decoder = Stats19Decoder('dft-road-casualty-statistics-collision-2025.csv')
    df = decoder.decode()
    
    X = df[['road_type', 'weather_conditions', 'light_conditions', 'speed_limit']]
    y = df['is_severe']
    
    b1 = MajorityClassBaseline()
    b1.fit(X, y)
    preds1 = b1.predict(X)
    print("Baseline 1 majority class predictions sum:", preds1.sum())
    
    b2 = GroupByRoadTypeBaseline()
    b2.fit(X, y)
    preds2 = b2.predict(X)
    print("Baseline 2 road-type majority predictions severe count:", preds2.sum())
