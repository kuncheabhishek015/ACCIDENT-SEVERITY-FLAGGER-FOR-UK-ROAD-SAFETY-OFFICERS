"""
Flask REST API Server
Exposes endpoints for accident severity risk prediction, statistical chi-square reports,
model benchmarks, top-K shortlist prioritization, and SQLite query audit logging.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.decoder import Stats19Decoder, WEATHER_LOOKUP, LIGHT_LOOKUP, ROAD_TYPE_LOOKUP, JUNCTION_DETAIL_LOOKUP
from src.statistical_analysis import run_full_statistical_analysis
from src.probabilistic_engine import ProbabilisticRiskEngine
from src.model_trainer import AccidentSeverityModelTrainer
from src.explainability import ExplainabilityEngine
from src.database import DatabaseManager
from src.visualization import DataVisualizationEngine

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Global variables for cached pipeline data and models
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dft-road-casualty-statistics-collision-2025.csv'))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models_saved'))

MODEL_REGISTRY = {
    'logistic_regression': 'Logistic Regression (Balanced)',
    'adaboost_classifier': 'AdaBoost Classifier',
    'bagging_classifier': 'Bagging Classifier',
    'decision_tree': 'Decision Tree (Depth=8)',
    'naive_bayes': 'Naive Bayes (GaussianNB)'
}

loaded_models = {}
decoder = None
decoded_df = None
prob_engine = None
db_manager = None
statistical_report = None
model_benchmark_results = None
preprocessor = None
serving_model = None
explainability_engine = None


def initialize_app_data():
    """Initializes STATS19 data, ML models, DB manager, and precomputes statistical reports."""
    global decoder, decoded_df, prob_engine, db_manager, statistical_report
    global model_benchmark_results, preprocessor, serving_model, explainability_engine, loaded_models

    print("Initializing Flask REST Server Data & Pipeline...")

    # Load & Decode Data
    decoder = Stats19Decoder(DATA_PATH)
    decoded_df = decoder.decode()
    clean_df = decoder.get_clean_features_df()

    # Initialize Probabilistic Engine
    prob_engine = ProbabilisticRiskEngine(decoded_df)

    # Initialize SQLite Audit Log DB
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'collision_queries.db'))
    db_manager = DatabaseManager(f'sqlite:///{db_path}')

    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
    chi_path = os.path.join(reports_dir, 'chi_square_report.json')
    benchmark_path = os.path.join(reports_dir, 'model_benchmark.json')
    preproc_path = os.path.join(MODELS_DIR, 'preprocessor.joblib')
    model_path = os.path.join(MODELS_DIR, 'logistic_regression.joblib')

    # Load Statistical Analysis (from cache or compute)
    if os.path.exists(chi_path):
        with open(chi_path, 'r') as f:
            statistical_report = json.load(f)
    else:
        statistical_report = run_full_statistical_analysis(clean_df)
        with open(chi_path, 'w') as f:
            json.dump(statistical_report, f, indent=2)

    # Load or Train ML Models & Preprocessor
    if not (os.path.exists(benchmark_path) and os.path.exists(preproc_path) and os.path.exists(model_path)):
        trainer = AccidentSeverityModelTrainer(DATA_PATH)
        model_benchmark_results = trainer.train_and_evaluate_all()
        trainer.save_artifacts(MODELS_DIR)
        with open(benchmark_path, 'w') as f:
            json.dump(model_benchmark_results, f, indent=2)
    else:
        with open(benchmark_path, 'r') as f:
            model_benchmark_results = json.load(f)

    preprocessor = joblib.load(preproc_path)

    # Load all models into memory for dynamic model selection
    for m_id in MODEL_REGISTRY:
        m_file = os.path.join(MODELS_DIR, f"{m_id}.joblib")
        if os.path.exists(m_file):
            loaded_models[m_id] = joblib.load(m_file)

    serving_model = loaded_models.get('logistic_regression')
    if serving_model is None and os.path.exists(model_path):
        serving_model = joblib.load(model_path)
        loaded_models['logistic_regression'] = serving_model

    # Initialize Explainability Engine with default model
    explainability_engine = ExplainabilityEngine(preprocessor, serving_model)

    print(f"Flask Server Initialization Complete! Loaded {len(loaded_models)} ML Classifiers.")


@app.route('/')
def index():
    """Serve officer dashboard web app."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/reports/visualizations/<path:filename>')
def serve_visualization(filename):
    """Serve generated Matplotlib/Seaborn plot images."""
    viz_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports', 'visualizations'))
    return send_from_directory(viz_dir, filename)


@app.route('/api/collisions/lookups', methods=['GET'])
def get_lookups():
    """Returns STATS19 dictionary lookup tables and available ML models for input forms."""
    return jsonify({
        'weather': [{'code': k, 'label': v} for k, v in WEATHER_LOOKUP.items() if k != -1],
        'light': [{'code': k, 'label': v} for k, v in LIGHT_LOOKUP.items() if k != -1],
        'road_type': [{'code': k, 'label': v} for k, v in ROAD_TYPE_LOOKUP.items() if k != -1],
        'junction_detail': [{'code': k, 'label': v} for k, v in JUNCTION_DETAIL_LOOKUP.items() if k != -1],
        'speed_limits': [20, 30, 40, 50, 60, 70],
        'models': [{'id': k, 'label': v} for k, v in MODEL_REGISTRY.items()]
    })


@app.route('/api/collisions/risk', methods=['POST'])
def predict_risk():
    """
    Evaluates severity risk for given road conditions using the chosen ML model.
    Expects JSON body: {
        "road_type": int,
        "junction_detail": int,
        "weather_conditions": int,
        "light_conditions": int,
        "speed_limit": int,
        "model_id": string (optional, defaults to 'logistic_regression')
    }
    """
    data = request.json or {}
    
    road_type = int(data.get('road_type', 6))
    junction_detail = int(data.get('junction_detail', 0))
    weather_conditions = int(data.get('weather_conditions', 1))
    light_conditions = int(data.get('light_conditions', 1))
    speed_limit = int(data.get('speed_limit', 30))
    chosen_model_id = str(data.get('model_id') or 'logistic_regression').strip().lower()

    # Select active model
    active_model = loaded_models.get(chosen_model_id, serving_model)
    active_model_name = MODEL_REGISTRY.get(chosen_model_id, 'Logistic Regression (Balanced)')

    input_dict = {
        'road_type': road_type,
        'junction_detail': junction_detail,
        'weather_conditions': weather_conditions,
        'light_conditions': light_conditions,
        'speed_limit': speed_limit
    }

    # 1. Machine Learning Prediction Probability
    input_df = pd.DataFrame([input_dict])
    proc_X = preprocessor.transform(input_df)
    ml_prob_severe = float(active_model.predict_proba(proc_X)[0, 1])
    ml_prob_percent = float(round(ml_prob_severe * 100, 2))

    # Determine Risk Category
    if ml_prob_severe < 0.25:
        risk_category = 'Low Risk'
        color = '#10b981' # Emerald Green
    elif ml_prob_severe < 0.40:
        risk_category = 'Moderate Risk'
        color = '#f59e0b' # Amber/Yellow
    elif ml_prob_severe < 0.60:
        risk_category = 'High Risk'
        color = '#f97316' # Orange
    else:
        risk_category = 'Critical Risk'
        color = '#ef4444' # Crimson Red

    # 2. Historical Evidence & Bayesian Conditional Probabilities
    evidence = prob_engine.get_historical_evidence(input_dict)

    # 3. Dynamic SHAP Explainability Risk Factors using the selected model
    dyn_explain_engine = ExplainabilityEngine(preprocessor, active_model)
    explain_factors = dyn_explain_engine.explain_prediction(input_dict)

    # Decoded labels
    road_label = ROAD_TYPE_LOOKUP.get(road_type, f"Code {road_type}")
    junction_label = JUNCTION_DETAIL_LOOKUP.get(junction_detail, f"Code {junction_detail}")
    weather_label = WEATHER_LOOKUP.get(weather_conditions, f"Code {weather_conditions}")
    light_label = LIGHT_LOOKUP.get(light_conditions, f"Code {light_conditions}")

    # 4. Log Transaction to SQLite DB (Software Engineering requirement)
    db_entry = db_manager.log_query({
        'road_type': road_type,
        'road_type_label': road_label,
        'junction_detail': junction_detail,
        'junction_label': junction_label,
        'weather_conditions': weather_conditions,
        'weather_label': weather_label,
        'light_conditions': light_conditions,
        'light_label': light_label,
        'speed_limit': speed_limit,
        'predicted_risk_score': ml_prob_severe,
        'predicted_risk_score_percent': ml_prob_percent,
        'risk_category': risk_category,
        'historical_matches': evidence['total_historical_collisions'],
        'historical_severe_count': evidence['severe_collisions_count'],
        'historical_severe_rate': evidence['historical_p_severe_percent'],
        'serving_model_name': active_model_name
    })

    return jsonify({
        'query_id': db_entry.id,
        'serving_model_name': active_model_name,
        'model_id': chosen_model_id,
        'predicted_severe_probability': ml_prob_severe,
        'predicted_risk_score_percent': ml_prob_percent,
        'risk_category': risk_category,
        'risk_color': color,
        'decoded_conditions': {
            'road_type': road_label,
            'junction_detail': junction_label,
            'weather_condition': weather_label,
            'light_condition': light_label,
            'speed_limit': f"{speed_limit} mph"
        },
        'historical_evidence': evidence,
        'risk_explainability_factors': explain_factors
    })


@app.route('/api/collisions/shortlist', methods=['GET'])
def get_shortlist():
    """Returns top-K prioritized interventions for council budget allocation."""
    k = request.args.get('k', default=25, type=int)
    shortlist = prob_engine.generate_prioritized_shortlist(top_k=k)
    return jsonify({
        'council_budget_interventions_k': k,
        'prioritized_shortlist': shortlist
    })


@app.route('/api/collisions/chi-square', methods=['GET'])
def get_chi_square():
    """Returns Chi-Square Test of Independence statistical outputs."""
    return jsonify(statistical_report)


@app.route('/api/collisions/models', methods=['GET'])
def get_models_benchmark():
    """Returns comparative benchmark results for all 5 ML models and 2 non-ML baselines."""
    return jsonify({
        'models_evaluations': model_benchmark_results,
        'metrics_explained': {
            'precision_at_k': 'Fraction of top-K predicted interventions that are actual severe collisions.',
            'recall_at_k': 'Fraction of total actual severe collisions captured in top-K interventions.',
            'bootstrapped_ci95': '95% Confidence Interval computed via 1,000 bootstrap iterations.'
        }
    })


@app.route('/api/collisions/history', methods=['GET'])
def get_query_history():
    """Returns SQLite query audit log history."""
    limit = request.args.get('limit', default=50, type=int)
    logs = db_manager.get_recent_logs(limit=limit)
    return jsonify({'total_logged_queries': len(logs), 'query_logs': logs})


if __name__ == '__main__':
    initialize_app_data()
    print("Starting Flask REST Server on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)
