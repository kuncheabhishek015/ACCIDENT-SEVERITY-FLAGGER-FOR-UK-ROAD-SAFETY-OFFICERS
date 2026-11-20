"""
Machine Learning Model Training & Comparison Engine
Trains, tunes, and compares 5 Machine Learning models alongside 2 Non-ML baselines
handling class imbalance and saving artifacts for serving.
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
                                
from src.decoder import Stats19Decoder
from src.baselines import MajorityClassBaseline, GroupByRoadTypeBaseline
from src.metrics_evaluation import evaluate_model_performance


class AccidentSeverityModelTrainer:
    """Trains and compares classification models for UK road collision severity prediction."""

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.preprocessor = None
        self.trained_models = {}
        self.evaluation_results = {}

    def prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Loads STATS19 data, decodes target, and splits into train/test sets."""
        decoder = Stats19Decoder(self.data_path)
        self.df = decoder.get_clean_features_df()

        feature_cols = ['road_type', 'weather_conditions', 'light_conditions', 'junction_detail', 'speed_limit']
        # Filter rows with complete features
        clean_df = self.df.dropna(subset=feature_cols + ['is_severe']).copy()

        X = clean_df[feature_cols]
        y = clean_df['is_severe']

        # Stratified Train-Test Split (80% train, 20% test)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        # Define preprocessing pipeline
        categorical_features = ['road_type', 'weather_conditions', 'light_conditions', 'junction_detail']
        numerical_features = ['speed_limit']

        self.preprocessor = ColumnTransformer(
            transformers=[
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
                ('num', StandardScaler(), numerical_features)
            ]
        )

        return self.X_train, self.X_test, self.y_train, self.y_test

    def train_and_evaluate_all(self) -> Dict[str, Any]:
        """Trains 2 Non-ML Baselines + 5 Machine Learning models and benchmarks performance."""
        if self.X_train is None:
            self.prepare_data()

        # 1. Non-ML Baseline 1: Majority Class
        b1 = MajorityClassBaseline()
        b1.fit(self.X_train, self.y_train)
        b1_probs = b1.predict_proba(self.X_test)[:, 1]
        b1_preds = b1.predict(self.X_test)
        self.evaluation_results['Baseline 1: Majority Class'] = evaluate_model_performance(
            'Baseline 1: Majority Class', self.y_test.values, b1_preds, b1_probs
        )

        # 2. Non-ML Baseline 2: Group-By Road Type
        b2 = GroupByRoadTypeBaseline()
        b2.fit(self.X_train, self.y_train)
        b2_probs = b2.predict_proba(self.X_test)[:, 1]
        b2_preds = b2.predict(self.X_test)
        self.evaluation_results['Baseline 2: Group-By Road Type'] = evaluate_model_performance(
            'Baseline 2: Group-By Road Type', self.y_test.values, b2_preds, b2_probs
        )

        # Preprocess features for ML models
        X_train_proc = self.preprocessor.fit_transform(self.X_train)
        X_test_proc = self.preprocessor.transform(self.X_test)

        # 3. Logistic Regression
        lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
        lr.fit(X_train_proc, self.y_train)
        lr_probs = lr.predict_proba(X_test_proc)[:, 1]
        lr_preds = (lr_probs >= 0.5).astype(int)
        self.trained_models['Logistic Regression'] = lr
        self.evaluation_results['Logistic Regression'] = evaluate_model_performance(
            'Logistic Regression', self.y_test.values, lr_preds, lr_probs
        )

        # 4. Decision Tree
        dt = DecisionTreeClassifier(class_weight='balanced', max_depth=8, random_state=42)
        dt.fit(X_train_proc, self.y_train)
        dt_probs = dt.predict_proba(X_test_proc)[:, 1]
        dt_preds = (dt_probs >= 0.5).astype(int)
        self.trained_models['Decision Tree'] = dt
        self.evaluation_results['Decision Tree'] = evaluate_model_performance(
            'Decision Tree', self.y_test.values, dt_preds, dt_probs
        )

        # 5. Bagging Classifier
        bag = BaggingClassifier(
            estimator=DecisionTreeClassifier(max_depth=8, class_weight='balanced'),
            n_estimators=30,
            random_state=42,
            n_jobs=-1
        )
        bag.fit(X_train_proc, self.y_train)
        bag_probs = bag.predict_proba(X_test_proc)[:, 1]
        bag_preds = (bag_probs >= 0.5).astype(int)
        self.trained_models['Bagging Classifier'] = bag
        self.evaluation_results['Bagging Classifier'] = evaluate_model_performance(
            'Bagging Classifier', self.y_test.values, bag_preds, bag_probs
        )

        # 6. AdaBoost Classifier
        ada = AdaBoostClassifier(n_estimators=50, random_state=42)
        ada.fit(X_train_proc, self.y_train)
        ada_probs = ada.predict_proba(X_test_proc)[:, 1]
        ada_preds = (ada_probs >= 0.5).astype(int)
        self.trained_models['AdaBoost Classifier'] = ada
        self.evaluation_results['AdaBoost Classifier'] = evaluate_model_performance(
            'AdaBoost Classifier', self.y_test.values, ada_preds, ada_probs
        )

        # 7. Naive Bayes (GaussianNB)
        nb = GaussianNB()
        nb.fit(X_train_proc, self.y_train)
        nb_probs = nb.predict_proba(X_test_proc)[:, 1]
        nb_preds = (nb_probs >= 0.5).astype(int)
        self.trained_models['Naive Bayes'] = nb
        self.evaluation_results['Naive Bayes'] = evaluate_model_performance(
            'Naive Bayes', self.y_test.values, nb_preds, nb_probs
        )

        return self.evaluation_results

    def save_artifacts(self, output_dir: str = 'models_saved'):
        """Saves trained preprocessor and best model to disk."""
        os.makedirs(output_dir, exist_ok=True)
        joblib.dump(self.preprocessor, os.path.join(output_dir, 'preprocessor.joblib'))
        
        for name, model in self.trained_models.items():
            filename = name.lower().replace(' ', '_') + '.joblib'
            joblib.dump(model, os.path.join(output_dir, filename))
            
        print(f"Saved preprocessor and {len(self.trained_models)} models to {output_dir}/")


if __name__ == '__main__':
    trainer = AccidentSeverityModelTrainer('dft-road-casualty-statistics-collision-2025.csv')
    results = trainer.train_and_evaluate_all()
    trainer.save_artifacts()
    
    print("\n--- MODEL COMPARISON BENCHMARK ---")
    for model_name, res in results.items():
        p25 = res['metrics_at_k']['K_25']['precision_at_k_percent']
        r25 = res['metrics_at_k']['K_25']['recall_at_k_percent']
        print(f"{model_name:<30} | AUC: {res['roc_auc']:.4f} | Precision@25: {p25:.1f}% | Recall@25: {r25:.2f}%")
