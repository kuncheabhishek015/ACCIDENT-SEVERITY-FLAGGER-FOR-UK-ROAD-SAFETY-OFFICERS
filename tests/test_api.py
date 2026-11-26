"""
Unit & Integration Tests for Flask REST API Endpoints
"""

import pytest
import json
from backend.app import app, initialize_app_data


@pytest.fixture(scope='module')
def test_client():
    """Initializes server pipeline data once and yields the Flask test client."""
    initialize_app_data()
    with app.test_client() as client:
        yield client


def test_api_lookups_endpoint(test_client):
    """Verify lookup dictionary endpoint returns valid lookups and models list."""
    response = test_client.get('/api/collisions/lookups')
    assert response.status_code == 200
    data = response.get_json()
    assert 'weather' in data
    assert 'light' in data
    assert 'road_type' in data
    assert 'speed_limits' in data
    assert 'models' in data
    assert len(data['models']) >= 5


def test_api_predict_risk_with_models(test_client):
    """Verify predicting risk with default and specified ML classifier."""
    # Test 1: Logistic Regression
    payload_lr = {
        'model_id': 'logistic_regression',
        'road_type': 3,
        'junction_detail': 0,
        'weather_conditions': 1,
        'light_conditions': 6,
        'speed_limit': 60
    }
    res_lr = test_client.post('/api/collisions/risk', json=payload_lr)
    assert res_lr.status_code == 200
    data_lr = res_lr.get_json()
    assert 'predicted_severe_probability' in data_lr
    assert 'risk_category' in data_lr
    assert data_lr['serving_model_name'] == 'Logistic Regression (Balanced)'
    assert 'risk_explainability_factors' in data_lr
    assert len(data_lr['risk_explainability_factors']) > 0

    # Test 2: Decision Tree
    payload_dt = {
        'model_id': 'decision_tree',
        'road_type': 6,
        'junction_detail': 3,
        'weather_conditions': 2,
        'light_conditions': 1,
        'speed_limit': 30
    }
    res_dt = test_client.post('/api/collisions/risk', json=payload_dt)
    assert res_dt.status_code == 200
    data_dt = res_dt.get_json()
    assert data_dt['serving_model_name'] == 'Decision Tree (Depth=8)'


def test_api_shortlist_budget(test_client):
    """Verify top-K council intervention shortlist returns requested budget count."""
    k_test = 10
    response = test_client.get(f'/api/collisions/shortlist?k={k_test}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'prioritized_shortlist' in data
    assert len(data['prioritized_shortlist']) == k_test
    assert data['council_budget_interventions_k'] == k_test
    # Verify rank ordering
    ranks = [item['rank'] for item in data['prioritized_shortlist']]
    assert ranks == list(range(1, k_test + 1))


def test_api_chi_square_and_benchmarks(test_client):
    """Verify Chi-Square statistics report and ML benchmark endpoints."""
    # Chi-Square endpoint
    chi_res = test_client.get('/api/collisions/chi-square')
    assert chi_res.status_code == 200
    chi_data = chi_res.get_json()
    assert 'tests' in chi_data
    assert 'weather_conditions' in chi_data['tests']
    assert chi_data['tests']['weather_conditions']['is_statistically_significant'] is True

    # Models benchmark endpoint
    models_res = test_client.get('/api/collisions/models')
    assert models_res.status_code == 200
    models_data = models_res.get_json()
    assert 'models_evaluations' in models_data
    assert 'Logistic Regression' in models_data['models_evaluations']


def test_api_audit_logs_history(test_client):
    """Verify SQLite audit log retrieval."""
    response = test_client.get('/api/collisions/history?limit=10')
    assert response.status_code == 200
    data = response.get_json()
    assert 'query_logs' in data
    assert 'total_logged_queries' in data
    assert data['total_logged_queries'] > 0
