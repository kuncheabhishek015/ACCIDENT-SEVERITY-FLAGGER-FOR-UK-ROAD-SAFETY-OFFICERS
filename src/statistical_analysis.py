"""
Statistical Analysis & Probability Engine
Performs Chi-Square Tests of Independence, contingency table analysis, Cramér's V calculation,
and Bayesian conditional probability estimations for UK STATS19 road collision severity.
"""

import pandas as pd
import numpy as np
from scipy import stats
import json
from typing import Dict, Any


def run_chi_square_test(df: pd.DataFrame, feature_col: str, feature_label_col: str, target_col: str = 'is_severe') -> Dict[str, Any]:
    """
    Performs Chi-Square Test of Independence between a categorical feature and collision severity.
    
    Returns detailed dictionary containing contingency table, chi2 stat, p-value, df, 
    expected frequencies, Cramér's V effect size, and statistical conclusion.
    """
    # Filter out missing/invalid codes (-1)
    clean_df = df[df[feature_col] != -1].copy()
    
    # Cross-tabulation (Observed Frequencies)
    contingency_table = pd.crosstab(clean_df[feature_label_col], clean_df[target_col])
    
    # Perform SciPy Chi-Square Test
    chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
    
    # Calculate Cramér's V
    n = contingency_table.sum().sum()
    r, c = contingency_table.shape
    min_dim = min(r - 1, c - 1)
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0.0
    
    # Interpret Effect Size (Cramér's V)
    if cramers_v < 0.1:
        effect_size_desc = 'Negligible / Weak'
    elif cramers_v < 0.3:
        effect_size_desc = 'Moderate'
    else:
        effect_size_desc = 'Strong'
        
    is_significant = bool(p_val < 0.05)
    
    # Calculate Conditional Probabilities P(Severe | Feature Category)
    grouped = clean_df.groupby(feature_label_col)[target_col].agg(['count', 'sum', 'mean']).reset_index()
    grouped.columns = ['Category', 'Total_Collisions', 'Severe_Collisions', 'P_Severe']
    grouped['P_Severe_Percent'] = (grouped['P_Severe'] * 100).round(2)
    grouped['Slight_Collisions'] = grouped['Total_Collisions'] - grouped['Severe_Collisions']
    
    results = {
        'feature_name': feature_col,
        'feature_label': feature_label_col,
        'chi2_statistic': float(round(chi2, 4)),
        'p_value': float(p_val),
        'p_value_formatted': '< 0.0001' if p_val < 0.0001 else f"{p_val:.4f}",
        'degrees_of_freedom': int(dof),
        'n_samples': int(n),
        'cramers_v': float(round(cramers_v, 4)),
        'effect_size': effect_size_desc,
        'is_statistically_significant': is_significant,
        'conclusion': f"Statistically {'SIGNIFICANT' if is_significant else 'NOT significant'} association (p = {p_val:.4e}, Cramér's V = {cramers_v:.4f}).",
        'contingency_table': contingency_table.to_dict(),
        'expected_frequencies': expected.tolist(),
        'conditional_probabilities': grouped.to_dict(orient='records')
    }
    return results


def run_full_statistical_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Execute chi-square tests for Weather, Light, Road Type, and Junction Type."""
    weather_results = run_chi_square_test(df, 'weather_conditions', 'weather_label')
    light_results = run_chi_square_test(df, 'light_conditions', 'light_label')
    road_type_results = run_chi_square_test(df, 'road_type', 'road_type_label')
    junction_results = run_chi_square_test(df, 'junction_detail', 'junction_label')
    
    # Global sample priors
    overall_p_severe = float(df['is_severe'].mean())
    
    summary = {
        'overall_sample_size': int(len(df)),
        'prior_probability_severe': float(round(overall_p_severe, 4)),
        'tests': {
            'weather_conditions': weather_results,
            'light_conditions': light_results,
            'road_type': road_type_results,
            'junction_detail': junction_results
        }
    }
    return summary


if __name__ == '__main__':
    from decoder import Stats19Decoder
    decoder = Stats19Decoder('dft-road-casualty-statistics-collision-2025.csv')
    df = decoder.decode()
    analysis = run_full_statistical_analysis(df)
    print("Statistical Analysis Completed.")
    print("Weather Chi2:", analysis['tests']['weather_conditions']['chi2_statistic'], "p-val:", analysis['tests']['weather_conditions']['p_value_formatted'])
    print("Light Chi2:", analysis['tests']['light_conditions']['chi2_statistic'], "p-val:", analysis['tests']['light_conditions']['p_value_formatted'])
