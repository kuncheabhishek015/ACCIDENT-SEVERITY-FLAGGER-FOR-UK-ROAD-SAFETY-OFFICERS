"""
Master Project Execution Pipeline
Executes end-to-end STATS19 data decoding, Chi-square statistical testing,
ML model training & bootstrapping evaluation, reports export, test suite execution,
and launches the Flask REST server + officer web dashboard.
"""

import os
import sys
import json
import pytest
import subprocess
import pandas as pd

from src.decoder import Stats19Decoder
from src.statistical_analysis import run_full_statistical_analysis
from src.model_trainer import AccidentSeverityModelTrainer
from src.probabilistic_engine import ProbabilisticRiskEngine
from src.visualization import DataVisualizationEngine

DATA_PATH = 'dft-road-casualty-statistics-collision-2025.csv'
REPORTS_DIR = 'reports'
MODELS_DIR = 'models_saved'


def run_pipeline():
    print("=" * 70)
    print("ACCIDENT SEVERITY FLAGGER FOR UK ROAD SAFETY OFFICERS")
    print("      Master Pipeline & Software Execution Engine")
    print("=" * 70)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # STEP 1: Decode Data & Load STATS19 Dataset
    print("\n[STEP 1/5] Loading & Decoding DfT STATS19 Collision Dataset...")
    decoder = Stats19Decoder(DATA_PATH)
    decoded_df = decoder.decode()
    clean_df = decoder.get_clean_features_df()
    print(f"Loaded {len(decoded_df):,} collision records.")
    print(f"Severe Collision Rate: {clean_df['is_severe'].mean() * 100:.2f}% (Fatal/Serious vs. Slight)")

    # STEP 2: Mathematics of Probability & Statistical Independence Tests
    print("\n[STEP 2/5] Running Chi-Square Tests of Independence & Cramer's V...")
    stat_report = run_full_statistical_analysis(clean_df)
    
    with open(os.path.join(REPORTS_DIR, 'chi_square_report.json'), 'w') as f:
        json.dump(stat_report, f, indent=2)
        
    print(f"Weather vs Severity: Chi2 = {stat_report['tests']['weather_conditions']['chi2_statistic']}, p = {stat_report['tests']['weather_conditions']['p_value_formatted']}, Cramer's V = {stat_report['tests']['weather_conditions']['cramers_v']}")
    print(f"Light vs Severity: Chi2 = {stat_report['tests']['light_conditions']['chi2_statistic']}, p = {stat_report['tests']['light_conditions']['p_value_formatted']}, Cramer's V = {stat_report['tests']['light_conditions']['cramers_v']}")
    print(f"Saved Chi-Square statistical report to {REPORTS_DIR}/chi_square_report.json")

    # STEP 2B: Generate Publication-Grade Data Visualizations (Matplotlib & Seaborn)
    print("\n[STEP 2B/5] Generating Data Visualizations (Matplotlib & Seaborn)...")
    viz_engine = DataVisualizationEngine(decoded_df)
    viz_paths = viz_engine.generate_all_visualizations()

    # STEP 3: ML Model Training & Bootstrapped Precision@K Evaluation
    print("\n[STEP 3/5] Training ML Models & Evaluating Precision@K with Bootstrapped CIs...")
    trainer = AccidentSeverityModelTrainer(DATA_PATH)
    eval_results = trainer.train_and_evaluate_all()
    trainer.save_artifacts(MODELS_DIR)

    with open(os.path.join(REPORTS_DIR, 'model_benchmark.json'), 'w') as f:
        json.dump(eval_results, f, indent=2)

    print("\n--- MODEL PERFORMANCE BENCHMARK MATRIX ---")
    print(f"{'Model Name':<32} | {'ROC-AUC':<8} | {'Prec@25 (%)':<12} | {'Prec@25 95% CI':<18}")
    print("-" * 75)
    for model_name, res in eval_results.items():
        p25 = res['metrics_at_k']['K_25']['precision_at_k_percent']
        ci = res['metrics_at_k']['K_25']['precision_at_k_ci95']
        print(f"{model_name:<32} | {res['roc_auc']:<8.4f} | {p25:<12.2f} | [{ci[0]:.4f}, {ci[1]:.4f}]")

    # Export Council Prioritized Shortlist
    prob_engine = ProbabilisticRiskEngine(decoded_df)
    shortlist = prob_engine.generate_prioritized_shortlist(top_k=30)
    shortlist_df = pd.DataFrame(shortlist)
    shortlist_df.to_csv(os.path.join(REPORTS_DIR, 'council_summary.csv'), index=False)
    print(f"\nSaved top-30 prioritized council shortlist to {REPORTS_DIR}/council_summary.csv")

    # STEP 4: Software Engineering Unit Testing
    print("\n[STEP 4/5] Running Pytest Unit Test Suite for Software Quality...")
    test_exit_code = pytest.main(['tests/', '-q'])
    if test_exit_code == 0:
        print("All Unit Tests PASSED successfully!")
    else:
        print(f"Pytest finished with status code {test_exit_code}")

    # STEP 5: Launching Flask Server & Web Dashboard
    print("\n[STEP 5/5] Launching Full-Stack REST API & Officer Dashboard...")
    print("Web App accessible at: http://127.0.0.1:5000")
    print("=" * 70)

    from backend.app import app, initialize_app_data
    initialize_app_data()
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    run_pipeline()
