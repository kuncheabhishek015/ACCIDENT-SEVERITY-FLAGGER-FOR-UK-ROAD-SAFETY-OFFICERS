"""
Unit Tests for Statistical Analysis Module
"""

import pytest
import pandas as pd
import numpy as np
from src.statistical_analysis import run_chi_square_test, run_full_statistical_analysis


def test_chi_square_calculation():
    # Synthetic test dataframe
    np.random.seed(42)
    df = pd.DataFrame({
        'weather_conditions': np.random.choice([1, 2, 5], 500),
        'weather_label': np.random.choice(['Fine', 'Rain', 'High Wind'], 500),
        'light_conditions': np.random.choice([1, 4, 6], 500),
        'light_label': np.random.choice(['Daylight', 'Lit', 'Dark'], 500),
        'road_type': np.random.choice([1, 3, 6], 500),
        'road_type_label': np.random.choice(['Roundabout', 'Dual', 'Single'], 500),
        'junction_detail': np.random.choice([0, 3, 6], 500),
        'junction_label': np.random.choice(['None', 'T-Junction', 'Crossroads'], 500),
        'is_severe': np.random.binomial(1, 0.25, 500)
    })

    res = run_chi_square_test(df, 'weather_conditions', 'weather_label')
    assert 'chi2_statistic' in res
    assert 'p_value' in res
    assert 'cramers_v' in res
    assert 'degrees_of_freedom' in res
    assert res['degrees_of_freedom'] > 0
    assert 0.0 <= res['cramers_v'] <= 1.0


def test_full_statistical_suite():
    np.random.seed(42)
    df = pd.DataFrame({
        'weather_conditions': np.random.choice([1, 2], 200),
        'weather_label': ['Fine'] * 100 + ['Rain'] * 100,
        'light_conditions': np.random.choice([1, 4], 200),
        'light_label': ['Daylight'] * 100 + ['Lit'] * 100,
        'road_type': np.random.choice([1, 3], 200),
        'road_type_label': ['Roundabout'] * 100 + ['Dual'] * 100,
        'junction_detail': np.random.choice([0, 3], 200),
        'junction_label': ['None'] * 100 + ['T-Junction'] * 100,
        'is_severe': np.random.binomial(1, 0.25, 200)
    })

    full_res = run_full_statistical_analysis(df)
    assert 'weather_conditions' in full_res['tests']
    assert 'light_conditions' in full_res['tests']
