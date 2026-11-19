"""
Probabilistic & Bayesian Risk Engine
Calculates conditional probabilities P(Severe | Conditions), Bayesian risk multipliers,
and queries historical evidence counts from the STATS19 database.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


class ProbabilisticRiskEngine:
    """Computes exact Bayesian conditional probabilities and historical evidence matching queried road conditions."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.prior_p_severe = float(df['is_severe'].mean()) if 'is_severe' in df.columns else 0.26

    def get_historical_evidence(self, query_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters dataframe matching query conditions and computes exact historical collision metrics.
        Query keys can include: road_type, junction_detail, weather_conditions, light_conditions, speed_limit.
        """
        filtered_df = self.df.copy()
        
        for col, val in query_conditions.items():
            if val is not None and col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col] == val]
                
        total_matched = len(filtered_df)
        
        if total_matched == 0:
            # Fallback to broader match (e.g. ignoring speed limit or minor features)
            fallback_df = self.df.copy()
            for col in ['road_type', 'weather_conditions', 'light_conditions']:
                if query_conditions.get(col) is not None and col in fallback_df.columns:
                    fallback_df = fallback_df[fallback_df[col] == query_conditions[col]]
            total_matched = len(fallback_df)
            filtered_df = fallback_df

        if total_matched > 0:
            severe_count = int(filtered_df['is_severe'].sum())
            slight_count = total_matched - severe_count
            fatal_count = int((filtered_df['collision_severity'] == 1).sum()) if 'collision_severity' in filtered_df.columns else 0
            serious_count = int((filtered_df['collision_severity'] == 2).sum()) if 'collision_severity' in filtered_df.columns else 0
            posterior_p_severe = float(severe_count / total_matched)
        else:
            severe_count = 0
            slight_count = 0
            fatal_count = 0
            serious_count = 0
            posterior_p_severe = self.prior_p_severe

        risk_multiplier = float(posterior_p_severe / self.prior_p_severe) if self.prior_p_severe > 0 else 1.0

        return {
            'total_historical_collisions': total_matched,
            'severe_collisions_count': severe_count,
            'fatal_collisions_count': fatal_count,
            'serious_collisions_count': serious_count,
            'slight_collisions_count': slight_count,
            'historical_p_severe': float(round(posterior_p_severe, 4)),
            'historical_p_severe_percent': float(round(posterior_p_severe * 100, 2)),
            'overall_prior_p_severe': float(round(self.prior_p_severe, 4)),
            'risk_multiplier': float(round(risk_multiplier, 2))
        }

    def generate_prioritized_shortlist(self, top_k: int = 25) -> List[Dict[str, Any]]:
        """
        Generates top-K prioritized road/condition combinations sorted by severe collision frequency and probability.
        Used by Council Officers for funding allocation interventions.
        """
        group_cols = ['road_type_label', 'weather_label', 'light_label', 'speed_limit']
        # Filter valid columns present in df
        cols = [c for c in group_cols if c in self.df.columns]
        
        grouped = self.df.groupby(cols).agg(
            total_collisions=('is_severe', 'count'),
            severe_collisions=('is_severe', 'sum'),
            severe_rate=('is_severe', 'mean')
        ).reset_index()
        
        # Filter combinations with at least 15 historical occurrences for statistical relevance
        stat_valid = grouped[grouped['total_collisions'] >= 15].copy()
        
        # Sort by severe_rate descending and severe_collisions count
        sorted_shortlist = stat_valid.sort_values(by=['severe_rate', 'severe_collisions'], ascending=[False, False]).head(top_k)
        
        shortlist_list = []
        for idx, row in sorted_shortlist.iterrows():
            shortlist_list.append({
                'rank': len(shortlist_list) + 1,
                'road_type': str(row.get('road_type_label', 'N/A')),
                'weather_condition': str(row.get('weather_label', 'N/A')),
                'light_condition': str(row.get('light_label', 'N/A')),
                'speed_limit': f"{row.get('speed_limit', 'N/A')} mph" if row.get('speed_limit') is not None else 'N/A',
                'total_collisions': int(row['total_collisions']),
                'severe_collisions': int(row['severe_collisions']),
                'severe_risk_rate_percent': float(round(row['severe_rate'] * 100, 2)),
                'risk_multiplier': float(round(row['severe_rate'] / self.prior_p_severe, 2))
            })
            
        return shortlist_list


if __name__ == '__main__':
    from decoder import Stats19Decoder
    decoder = Stats19Decoder('dft-road-casualty-statistics-collision-2025.csv')
    df = decoder.decode()
    engine = ProbabilisticRiskEngine(df)
    sample_query = {'road_type': 3, 'weather_conditions': 1, 'light_conditions': 6}
    evidence = engine.get_historical_evidence(sample_query)
    print("Sample Evidence:", evidence)
    shortlist = engine.generate_prioritized_shortlist(top_k=5)
    print("Top 5 Shortlist:", shortlist)
