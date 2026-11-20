"""
SHAP & Feature Explainability Engine
Calculates feature attributions and risk contribution scores for individual collision risk predictions.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List


class ExplainabilityEngine:
    """Computes interpretable risk factor contributions for officer decision-making."""

    def __init__(self, preprocessor, model):
        self.preprocessor = preprocessor
        self.model = model

    def explain_prediction(self, input_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculates feature attributions (SHAP/coefficient based contributions) for the given prediction.
        Input dictionary keys: road_type, weather_conditions, light_conditions, junction_detail, speed_limit.
        """
        input_df = pd.DataFrame([input_dict])
        
        # Transform features
        proc_features = self.preprocessor.transform(input_df)
        
        # Get feature names from preprocessor
        cat_encoder = self.preprocessor.named_transformers_['cat']
        cat_feature_names = cat_encoder.get_feature_names_out(['road_type', 'weather_conditions', 'light_conditions', 'junction_detail'])
        all_feature_names = list(cat_feature_names) + ['speed_limit']
        
        # Model prediction probability
        if hasattr(self.model, 'predict_proba'):
            predicted_prob = float(self.model.predict_proba(proc_features)[0, 1])
        else:
            predicted_prob = 0.26

        # Feature contribution attributions
        contributions = []
        
        # Extract tree feature importances, ensemble importances, or logistic regression coefficients
        if hasattr(self.model, 'coef_'):
            weights = self.model.coef_[0]
        elif hasattr(self.model, 'feature_importances_'):
            weights = self.model.feature_importances_
        elif hasattr(self.model, 'estimators_') and len(self.model.estimators_) > 0 and hasattr(self.model.estimators_[0], 'feature_importances_'):
            weights = np.mean([est.feature_importances_ for est in self.model.estimators_], axis=0)
        else:
            weights = np.ones(len(all_feature_names)) / len(all_feature_names)

        row_vals = proc_features[0]
        
        for name, val, weight in zip(all_feature_names, row_vals, weights):
            if val != 0:
                impact = float(val * weight)
                
                # Human readable feature label formatting
                clean_name = name.replace('cat__', '').replace('num__', '')
                if 'weather_conditions' in clean_name:
                    desc = f"Weather Condition (Code {input_dict.get('weather_conditions')})"
                elif 'light_conditions' in clean_name:
                    desc = f"Light Condition (Code {input_dict.get('light_conditions')})"
                elif 'road_type' in clean_name:
                    desc = f"Road Type (Code {input_dict.get('road_type')})"
                elif 'junction_detail' in clean_name:
                    desc = f"Junction Type (Code {input_dict.get('junction_detail')})"
                elif 'speed_limit' in clean_name:
                    desc = f"Speed Limit ({input_dict.get('speed_limit')} mph)"
                else:
                    desc = clean_name

                contributions.append({
                    'feature': desc,
                    'raw_feature_key': name,
                    'impact_score': float(round(impact, 4)),
                    'risk_direction': 'Increases Risk' if impact > 0 else 'Reduces Risk',
                    'formatted_impact': f"{'+' if impact > 0 else ''}{impact:.2f}"
                })

        # Sort contributions by magnitude
        contributions.sort(key=lambda x: abs(x['impact_score']), reverse=True)
        return contributions[:5]


if __name__ == '__main__':
    print("Explainability Engine Loaded.")
