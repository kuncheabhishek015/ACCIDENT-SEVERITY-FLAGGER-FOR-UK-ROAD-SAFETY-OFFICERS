"""
Metrics Evaluation & Bootstrapping Engine
Calculates Precision@K, Recall@K, ROC-AUC, F1-Score, and 95% Bootstrapped Confidence Intervals
for evaluating collision risk prioritization under council intervention budget constraints (K).
"""

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, accuracy_score
from typing import Dict, Any, Tuple, List


def calculate_precision_at_k(y_true: np.ndarray, y_probs: np.ndarray, k: int) -> float:
    """Calculates Precision@K: proportion of actual severe cases in top-K highest risk predictions."""
    if len(y_probs) < k:
        k = len(y_probs)
    # Get indices of top K highest predicted probabilities
    top_k_indices = np.argsort(y_probs)[::-1][:k]
    top_k_true = y_true[top_k_indices]
    precision_k = np.sum(top_k_true) / k
    return float(precision_k)


def calculate_recall_at_k(y_true: np.ndarray, y_probs: np.ndarray, k: int) -> float:
    """Calculates Recall@K: proportion of total actual severe cases captured in top-K predictions."""
    total_severes = np.sum(y_true)
    if total_severes == 0:
        return 0.0
    if len(y_probs) < k:
        k = len(y_probs)
    top_k_indices = np.argsort(y_probs)[::-1][:k]
    top_k_true = y_true[top_k_indices]
    recall_k = np.sum(top_k_true) / total_severes
    return float(recall_k)


def calculate_bootstrapped_ci(
    y_true: np.ndarray, 
    y_probs: np.ndarray, 
    k: int = 25, 
    n_bootstraps: int = 1000, 
    alpha: float = 0.05
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Computes 95% Bootstrapped Confidence Intervals for Precision@K and Recall@K
    using percentile resampling.
    """
    np.random.seed(42)
    n = len(y_true)
    precisions = []
    recalls = []

    for _ in range(n_bootstraps):
        indices = np.random.choice(n, size=n, replace=True)
        sample_y_true = y_true[indices]
        sample_y_probs = y_probs[indices]
        
        prec = calculate_precision_at_k(sample_y_true, sample_y_probs, k)
        rec = calculate_recall_at_k(sample_y_true, sample_y_probs, k)
        
        precisions.append(prec)
        recalls.append(rec)

    lower_p = (alpha / 2.0) * 100
    upper_p = (1.0 - alpha / 2.0) * 100

    prec_ci = (float(np.percentile(precisions, lower_p)), float(np.percentile(precisions, upper_p)))
    rec_ci = (float(np.percentile(recalls, lower_p)), float(np.percentile(recalls, upper_p)))

    return prec_ci, rec_ci


def evaluate_model_performance(
    model_name: str, 
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    y_probs: np.ndarray, 
    k_list: List[int] = [20, 25, 30]
) -> Dict[str, Any]:
    """Computes full evaluation suite for a classifier including Precision@K, Recall@K, AUC, F1, and Bootstrapped CIs."""
    roc_auc = float(roc_auc_score(y_true, y_probs))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_true, y_pred))

    metrics_by_k = {}
    for k in k_list:
        prec_k = calculate_precision_at_k(y_true, y_probs, k)
        rec_k = calculate_recall_at_k(y_true, y_probs, k)
        prec_ci, rec_ci = calculate_bootstrapped_ci(y_true, y_probs, k=k, n_bootstraps=200)
        
        metrics_by_k[f"K_{k}"] = {
            'precision_at_k': float(round(prec_k, 4)),
            'precision_at_k_percent': float(round(prec_k * 100, 2)),
            'precision_at_k_ci95': [round(prec_ci[0], 4), round(prec_ci[1], 4)],
            'recall_at_k': float(round(rec_k, 4)),
            'recall_at_k_percent': float(round(rec_k * 100, 2)),
            'recall_at_k_ci95': [round(rec_ci[0], 4), round(rec_ci[1], 4)]
        }

    return {
        'model_name': model_name,
        'accuracy': float(round(accuracy, 4)),
        'precision': float(round(precision, 4)),
        'recall': float(round(recall, 4)),
        'f1_score': float(round(f1, 4)),
        'roc_auc': float(round(roc_auc, 4)),
        'metrics_at_k': metrics_by_k
    }


if __name__ == '__main__':
    y_true = np.random.binomial(1, 0.26, 1000)
    y_probs = np.random.uniform(0, 1, 1000)
    y_pred = (y_probs > 0.5).astype(int)
    results = evaluate_model_performance("TestModel", y_true, y_pred, y_probs)
    print("Test Evaluation Results:", results)
