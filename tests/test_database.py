"""
Unit Tests for Database & Audit Logging System (SQLAlchemy ORM + SQLite)
"""

import pytest
from datetime import datetime
from src.database import DatabaseManager, QueryLog


@pytest.fixture
def in_memory_db():
    """Provides a fresh isolated in-memory SQLite database for testing."""
    return DatabaseManager(db_url='sqlite:///:memory:')


def test_db_initialization_and_logging(in_memory_db):
    """Verify logging a new assessment query persists correctly."""
    query_payload = {
        'road_type': 3,
        'road_type_label': 'Dual carriageway',
        'junction_detail': 0,
        'junction_label': 'Not at junction',
        'weather_conditions': 1,
        'weather_label': 'Fine no high winds',
        'light_conditions': 6,
        'light_label': 'Darkness - no lighting',
        'speed_limit': 60,
        'predicted_risk_score': 0.425,
        'predicted_risk_score_percent': 42.5,
        'risk_category': 'High Risk',
        'historical_matches': 120,
        'historical_severe_count': 51,
        'historical_severe_rate': 42.5,
        'serving_model_name': 'Logistic Regression (Balanced)'
    }

    log_entry = in_memory_db.log_query(query_payload)
    assert log_entry.id is not None
    assert log_entry.id == 1
    assert log_entry.road_type == 3
    assert log_entry.risk_category == 'High Risk'
    assert log_entry.predicted_risk_score_percent == 42.5
    assert log_entry.serving_model_name == 'Logistic Regression (Balanced)'


def test_db_recent_logs_retrieval(in_memory_db):
    """Verify retrieving recent logs ordered descending with limit enforcement."""
    for i in range(5):
        in_memory_db.log_query({
            'road_type': 6,
            'road_type_label': 'Single carriageway',
            'junction_detail': 0,
            'junction_label': 'None',
            'weather_conditions': 1,
            'weather_label': 'Fine',
            'light_conditions': 1,
            'light_label': 'Daylight',
            'speed_limit': 30,
            'predicted_risk_score': 0.20 + (i * 0.05),
            'predicted_risk_score_percent': 20.0 + (i * 5.0),
            'risk_category': 'Low Risk',
            'historical_matches': 500,
            'historical_severe_count': 100,
            'historical_severe_rate': 20.0,
            'serving_model_name': f'Model {i}'
        })

    logs = in_memory_db.get_recent_logs(limit=3)
    assert len(logs) == 3
    # Most recently added log should be first
    assert logs[0]['serving_model_name'] == 'Model 4'
    assert logs[1]['serving_model_name'] == 'Model 3'
    assert logs[2]['serving_model_name'] == 'Model 2'


def test_db_to_dict_serialization(in_memory_db):
    """Verify dictionary serialization contains all expected UI fields."""
    entry = in_memory_db.log_query({
        'road_type': 1,
        'road_type_label': 'Roundabout',
        'junction_detail': 1,
        'junction_label': 'Roundabout',
        'weather_conditions': 2,
        'weather_label': 'Raining',
        'light_conditions': 4,
        'light_label': 'Darkness lit',
        'speed_limit': 30,
        'predicted_risk_score': 0.35,
        'predicted_risk_score_percent': 35.0,
        'risk_category': 'Moderate Risk',
        'historical_matches': 80,
        'historical_severe_count': 28,
        'historical_severe_rate': 35.0,
        'serving_model_name': 'Decision Tree (Depth=8)'
    })

    record = entry.to_dict()
    assert 'id' in record
    assert 'timestamp' in record
    assert record['road_type_label'] == 'Roundabout'
    assert record['risk_category'] == 'Moderate Risk'
    assert record['serving_model_name'] == 'Decision Tree (Depth=8)'
