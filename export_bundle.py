import os
import json
import joblib
import pandas as pd
import numpy as np

from src.decoder import Stats19Decoder, WEATHER_LOOKUP, LIGHT_LOOKUP, ROAD_TYPE_LOOKUP, JUNCTION_DETAIL_LOOKUP
from src.probabilistic_engine import ProbabilisticRiskEngine
from src.database import DatabaseManager

def main():
    data_path = 'dft-road-casualty-statistics-collision-2025.csv'
    decoder = Stats19Decoder(data_path)
    df = decoder.decode()
    prior_p = float(df['is_severe'].mean())

    prob_engine = ProbabilisticRiskEngine(df)
    shortlist_50 = prob_engine.generate_prioritized_shortlist(top_k=50)

    # Read reports
    with open('reports/chi_square_report.json', 'r') as f:
        chi_report = json.load(f)

    with open('reports/model_benchmark.json', 'r') as f:
        model_benchmark = json.load(f)

    # Read audit logs
    db_manager = DatabaseManager('sqlite:///collision_queries.db')
    sample_audit_logs = db_manager.get_recent_logs(limit=50)

    # Load ML models and preprocessor
    models_dir = 'models_saved'
    preprocessor = joblib.load(os.path.join(models_dir, 'preprocessor.joblib'))
    lr_model = joblib.load(os.path.join(models_dir, 'logistic_regression.joblib'))
    dt_model = joblib.load(os.path.join(models_dir, 'decision_tree.joblib'))
    ada_model = joblib.load(os.path.join(models_dir, 'adaboost_classifier.joblib'))
    bag_model = joblib.load(os.path.join(models_dir, 'bagging_classifier.joblib'))
    nb_model = joblib.load(os.path.join(models_dir, 'naive_bayes.joblib'))

    num_scaler = preprocessor.named_transformers_['num']
    speed_mean = float(num_scaler.mean_[0])
    speed_scale = float(num_scaler.scale_[0])

    cat_encoder = preprocessor.named_transformers_['cat']
    feature_names = list(cat_encoder.get_feature_names_out(['road_type', 'weather_conditions', 'light_conditions', 'junction_detail'])) + ['speed_limit']

    lr_coefs = {name: float(w) for name, w in zip(feature_names, lr_model.coef_[0])}
    lr_intercept = float(lr_model.intercept_[0])

    # Unscaled parameters for direct logistic evaluation without standard scaler step
    speed_raw_coef = lr_coefs.get('speed_limit', 0.0)
    unscaled_speed_coef = float(speed_raw_coef / speed_scale)
    adjusted_lr_intercept = float(lr_intercept - (speed_raw_coef * speed_mean / speed_scale))

    # Empirical STATS19 Risk Multipliers for all factors
    clean_df = decoder.get_clean_features_df()
    base_severe_rate = float(clean_df['is_severe'].mean())

    def get_multipliers(col):
        rates = clean_df.groupby(col)['is_severe'].mean()
        return {int(k): round(float(v / base_severe_rate), 4) for k, v in rates.items() if not pd.isna(k)}

    road_mults = get_multipliers('road_type')
    weather_mults = get_multipliers('weather_conditions')
    light_mults = get_multipliers('light_conditions')
    junction_mults = get_multipliers('junction_detail')
    speed_mults = get_multipliers('speed_limit')

    # Pre-aggregate fine-grained evidence and compute model predictions for all combinations
    agg = df.groupby(['road_type', 'junction_detail', 'weather_conditions', 'light_conditions', 'speed_limit']).agg(
        total=('is_severe', 'count'),
        severe=('is_severe', 'sum'),
        fatal=('collision_severity', lambda s: int((s == 1).sum())),
        serious=('collision_severity', lambda s: int((s == 2).sum()))
    ).reset_index()

    # Batch transform and predict for all observed combinations
    comb_input_df = agg[['road_type', 'junction_detail', 'weather_conditions', 'light_conditions', 'speed_limit']].copy()
    proc_X = preprocessor.transform(comb_input_df)

    lr_probs = lr_model.predict_proba(proc_X)[:, 1]
    ada_probs = ada_model.predict_proba(proc_X)[:, 1]
    bag_probs = bag_model.predict_proba(proc_X)[:, 1]
    dt_probs = dt_model.predict_proba(proc_X)[:, 1]
    nb_probs = nb_model.predict_proba(proc_X)[:, 1]

    evidence_map = {}
    predictions_map = {}

    for idx, r in agg.iterrows():
        key = f"{int(r['road_type'])}_{int(r['junction_detail'])}_{int(r['weather_conditions'])}_{int(r['light_conditions'])}_{int(r['speed_limit'])}"
        tot = int(r['total'])
        sev = int(r['severe'])
        rate = round(float(sev / tot) * 100, 2)
        mult = round(float((sev / tot) / prior_p), 2)
        evidence_map[key] = {
            'total_historical_collisions': tot,
            'severe_collisions_count': sev,
            'fatal_collisions_count': int(r['fatal']),
            'serious_collisions_count': int(r['serious']),
            'historical_p_severe_percent': rate,
            'risk_multiplier': mult
        }
        predictions_map[key] = {
            'logistic_regression': round(float(lr_probs[idx]), 4),
            'adaboost_classifier': round(float(ada_probs[idx]), 4),
            'bagging_classifier': round(float(bag_probs[idx]), 4),
            'decision_tree': round(float(dt_probs[idx]), 4),
            'naive_bayes': round(float(nb_probs[idx]), 4)
        }

    # Pre-aggregate fallback evidence
    agg_fb = df.groupby(['road_type', 'weather_conditions', 'light_conditions']).agg(
        total=('is_severe', 'count'),
        severe=('is_severe', 'sum'),
        fatal=('collision_severity', lambda s: int((s == 1).sum())),
        serious=('collision_severity', lambda s: int((s == 2).sum()))
    ).reset_index()

    fallback_map = {}
    for _, r in agg_fb.iterrows():
        key = f"{int(r['road_type'])}_{int(r['weather_conditions'])}_{int(r['light_conditions'])}"
        tot = int(r['total'])
        sev = int(r['severe'])
        rate = round(float(sev / tot) * 100, 2)
        mult = round(float((sev / tot) / prior_p), 2)
        fallback_map[key] = {
            'total_historical_collisions': tot,
            'severe_collisions_count': sev,
            'fatal_collisions_count': int(r['fatal']),
            'serious_collisions_count': int(r['serious']),
            'historical_p_severe_percent': rate,
            'risk_multiplier': mult
        }

    bundle = {
        'lookups': {
            'weather': [{'code': k, 'label': v} for k, v in WEATHER_LOOKUP.items() if k != -1],
            'light': [{'code': k, 'label': v} for k, v in LIGHT_LOOKUP.items() if k != -1],
            'road_type': [{'code': k, 'label': v} for k, v in ROAD_TYPE_LOOKUP.items() if k != -1],
            'junction_detail': [{'code': k, 'label': v} for k, v in JUNCTION_DETAIL_LOOKUP.items() if k != -1],
            'speed_limits': [20, 30, 40, 50, 60, 70],
            'models': [
                {'id': 'logistic_regression', 'label': 'Logistic Regression (Balanced)'},
                {'id': 'adaboost_classifier', 'label': 'AdaBoost Classifier'},
                {'id': 'bagging_classifier', 'label': 'Bagging Classifier'},
                {'id': 'decision_tree', 'label': 'Decision Tree (Depth=8)'},
                {'id': 'naive_bayes', 'label': 'Naive Bayes (GaussianNB)'}
            ]
        },
        'prior_p_severe': prior_p,
        'chi_square_report': chi_report,
        'model_benchmark': model_benchmark,
        'shortlist_50': shortlist_50,
        'sample_audit_logs': sample_audit_logs,
        'evidence_map': evidence_map,
        'fallback_map': fallback_map,
        'predictions_map': predictions_map,
        'scaler': {
            'speed_mean': speed_mean,
            'speed_scale': speed_scale
        },
        'multipliers': {
            'road_type': road_mults,
            'weather': weather_mults,
            'light': light_mults,
            'junction_detail': junction_mults,
            'speed_limit': speed_mults
        },
        'lr_model': {
            'intercept': lr_intercept,
            'adjusted_intercept': adjusted_lr_intercept,
            'unscaled_speed_coef': unscaled_speed_coef,
            'coefficients': lr_coefs
        }
    }

    out_path = os.path.join('frontend', 'js', 'dataset_bundle.js')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('/* Auto-generated precomputed STATS19 dataset and ML model parameters for standalone Firebase live mode */\n')
        f.write('window.DATASET_BUNDLE = ')
        json.dump(bundle, f)
        f.write(';\n')

    print(f"Successfully generated {out_path} (Size: {os.path.getsize(out_path)} bytes)")

if __name__ == '__main__':
    main()
