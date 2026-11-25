"""
Database & Query Audit Log System
SQLAlchemy ORM models and SQLite persistence for logging officer risk assessment queries.
"""

import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class QueryLog(Base):
    """SQL Database table logging every officer query, inputs, predicted severity risk, and evidence."""

    __tablename__ = 'query_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    road_type = Column(Integer, nullable=False)
    road_type_label = Column(String(100), nullable=True)
    junction_detail = Column(Integer, nullable=False)
    junction_label = Column(String(100), nullable=True)
    weather_conditions = Column(Integer, nullable=False)
    weather_label = Column(String(100), nullable=True)
    light_conditions = Column(Integer, nullable=False)
    light_label = Column(String(100), nullable=True)
    speed_limit = Column(Integer, nullable=False)
    
    # Model Outputs
    predicted_risk_score = Column(Float, nullable=False)
    predicted_risk_score_percent = Column(Float, nullable=False)
    risk_category = Column(String(50), nullable=False)
    historical_matches = Column(Integer, nullable=False)
    historical_severe_count = Column(Integer, nullable=False)
    historical_severe_rate = Column(Float, nullable=False)
    
    # Software Engineering metadata
    client_ip = Column(String(50), default='127.0.0.1')
    serving_model_name = Column(String(100), default='Logistic Regression (Balanced)')

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'road_type_label': self.road_type_label or f"Code {self.road_type}",
            'junction_label': self.junction_label or f"Code {self.junction_detail}",
            'weather_label': self.weather_label or f"Code {self.weather_conditions}",
            'light_label': self.light_label or f"Code {self.light_conditions}",
            'speed_limit': f"{self.speed_limit} mph",
            'predicted_risk_score_percent': self.predicted_risk_score_percent,
            'risk_category': self.risk_category,
            'historical_matches': self.historical_matches,
            'historical_severe_rate': self.historical_severe_rate,
            'serving_model_name': self.serving_model_name
        }


class DatabaseManager:
    """Manages SQLite database connections and logging transactions."""

    def __init__(self, db_url: str = 'sqlite:///collision_queries.db'):
        self.engine = create_engine(db_url, echo=False, connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def log_query(self, query_data: dict) -> QueryLog:
        """Logs a new risk query transaction to SQLite."""
        session = self.SessionLocal()
        try:
            log_entry = QueryLog(
                road_type=query_data['road_type'],
                road_type_label=query_data.get('road_type_label'),
                junction_detail=query_data['junction_detail'],
                junction_label=query_data.get('junction_label'),
                weather_conditions=query_data['weather_conditions'],
                weather_label=query_data.get('weather_label'),
                light_conditions=query_data['light_conditions'],
                light_label=query_data.get('light_label'),
                speed_limit=query_data['speed_limit'],
                predicted_risk_score=query_data['predicted_risk_score'],
                predicted_risk_score_percent=query_data['predicted_risk_score_percent'],
                risk_category=query_data['risk_category'],
                historical_matches=query_data['historical_matches'],
                historical_severe_count=query_data['historical_severe_count'],
                historical_severe_rate=query_data['historical_severe_rate'],
                serving_model_name=query_data.get('serving_model_name', 'Logistic Regression (Balanced)')
            )
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)
            return log_entry
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_recent_logs(self, limit: int = 50) -> list:
        """Retrieves recent query logs ordered by timestamp descending."""
        session = self.SessionLocal()
        try:
            logs = session.query(QueryLog).order_by(QueryLog.timestamp.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]
        finally:
            session.close()


if __name__ == '__main__':
    db = DatabaseManager('sqlite:///test_queries.db')
    print("Database Manager Initialized.")
