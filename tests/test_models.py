"""
Unit Tests for Machine Learning Models & Metrics Engine
"""

import pytest
import numpy as np
import pandas as pd
from src.metrics_evaluation import calculate_precision_at_k, calculate_recall_at_k, calculate_bootstrapped_ci
from src.baselines import MajorityClassBaseline, GroupByRoadTypeBaseline


def test_precision_recall_at_k():
    y_true = np.array([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
    y_probs = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
    
    # Top 3 predicted probs are indices 0 (y=1), 1 (y=0), 2 (y=1) -> 2 severes out of 3 -> Prec@3 = 2/3 = 0.6667
    prec3 = calculate_precision_at_k(y_true, y_probs, k=3)
    assert abs(prec3 - (2.0 / 3.0)) < 1e-4

    # Total severes in dataset = 3 (indices 0, 2, 4). Top 3 predictions captured 2 -> Recall@3 = 2/3 = 0.6667
    rec3 = calculate_recall_at_k(y_true, y_probs, k=3)
    assert abs(rec3 - (2.0 / 3.0)) < 1e-4

def test_bootstrapping_ci():
    y_true = np.array([1, 0, 1, 0, 1, 0, 0, 0, 0, 0])
    y_probs = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
    prec_ci, rec_ci = calculate_bootstrapped_ci(y_true, y_probs, k=3, n_bootstraps=50)
    assert len(prec_ci) == 2
    assert 0.0 <= prec_ci[0] <= prec_ci[1] <= 1.0
    assert 0.0 <= rec_ci[0] <= rec_ci[1] <= 1.0

def test_baselines():
    X = pd.DataFrame({'road_type': [1, 1, 3, 3, 6, 6]})
    y = pd.Series([0, 0, 1, 1, 0, 0])
    
    b1 = MajorityClassBaseline()
    b1.fit(X, y)
    preds1 = b1.predict(X)
    assert (preds1 == 0).all()

    b2 = GroupByRoadTypeBaseline(threshold=0.5)
    b2.fit(X, y)
    probs2 = b2.predict_proba(X)
    assert probs2.shape == (6, 2)
