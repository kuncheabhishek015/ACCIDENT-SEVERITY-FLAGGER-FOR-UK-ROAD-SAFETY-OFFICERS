import pandas as pd
import numpy as np

# DfT STATS19 Variable Lookups
WEATHER_LOOKUP = {
    1: 'Fine no high winds',
    2: 'Raining no high winds',
    3: 'Snowing no high winds',
    4: 'Fine + high winds',
    5: 'Raining + high winds',
    6: 'Snowing + high winds',
    7: 'Fog or mist',
    8: 'Other',
    9: 'Unknown',
    -1: 'Data missing or out of range'
}

LIGHT_LOOKUP = {
    1: 'Daylight',
    4: 'Darkness - lights lit',
    5: 'Darkness - lights unlit',
    6: 'Darkness - no lighting',
    7: 'Darkness - lighting unknown',
    -1: 'Data missing or out of range'
}

ROAD_TYPE_LOOKUP = {
    1: 'Roundabout',
    2: 'One way street',
    3: 'Dual carriageway',
    6: 'Single carriageway',
    7: 'Slip road',
    9: 'Unknown',
    -1: 'Data missing or out of range'
}

JUNCTION_DETAIL_LOOKUP = {
    0: 'Not at junction or within 20 metres',
    1: 'Roundabout',
    2: 'Mini-roundabout',
    3: 'T or staggered junction',
    5: 'Slip road',
    6: 'Crossroads',
    7: 'More than 4 arms (not roundabout)',
    8: 'Using private drive or entrance',
    9: 'Other junction',
    13: 'T or staggered junction',
    16: 'Mini-roundabout or crossroads',
    17: 'More than 4 arms',
    18: 'Private drive/entrance',
    19: 'Other junction type',
    99: 'Unknown',
    -1: 'Data missing or out of range'
}

SPEED_LIMIT_LOOKUP = {
    20: '20 mph',
    30: '30 mph',
    40: '40 mph',
    50: '50 mph',
    60: '60 mph',
    70: '70 mph',
    -1: 'Data missing or out of range'
}

SEVERITY_LOOKUP = {
    1: 'Fatal',
    2: 'Serious',
    3: 'Slight'
}


class Stats19Decoder:
    """Utility class to load and decode STATS19 collision datasets."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.raw_df = None
        self.decoded_df = None

    def load_data(self) -> pd.DataFrame:
        """Load raw CSV dataset."""
        self.raw_df = pd.read_csv(self.filepath, low_memory=False)
        return self.raw_df

    def decode(self) -> pd.DataFrame:
        """Decode categorical integer codes to official string labels and create binary target."""
        if self.raw_df is None:
            self.load_data()

        df = self.raw_df.copy()

        # Map lookup dictionaries
        df['weather_label'] = df['weather_conditions'].map(WEATHER_LOOKUP).fillna('Unknown/Other')
        df['light_label'] = df['light_conditions'].map(LIGHT_LOOKUP).fillna('Unknown/Other')
        df['road_type_label'] = df['road_type'].map(ROAD_TYPE_LOOKUP).fillna('Unknown/Other')
        df['junction_label'] = df['junction_detail'].map(JUNCTION_DETAIL_LOOKUP).fillna('Unknown/Other')
        df['severity_label'] = df['collision_severity'].map(SEVERITY_LOOKUP).fillna('Unknown')

        # Create binary severity target: 1 = Severe (Fatal/Serious: 1, 2), 0 = Slight (3)
        # Fatal (1) and Serious (2) represent high-severity accidents
        df['is_severe'] = df['collision_severity'].isin([1, 2]).astype(int)

        self.decoded_df = df
        return df

    def get_clean_features_df(self) -> pd.DataFrame:
        """Extract cleaned dataframe suitable for statistical testing and machine learning."""
        if self.decoded_df is None:
            self.decode()

        cols = [
            'collision_index', 'collision_severity', 'is_severe', 'severity_label',
            'weather_conditions', 'weather_label',
            'light_conditions', 'light_label',
            'road_type', 'road_type_label',
            'junction_detail', 'junction_label',
            'speed_limit', 'number_of_vehicles', 'number_of_casualties'
        ]
        
        # Keep columns present in df
        present_cols = [c for c in cols if c in self.decoded_df.columns]
        clean_df = self.decoded_df[present_cols].copy()
        
        # Clean invalid values (-1 or 9/99 unknown where appropriate)
        clean_df = clean_df[clean_df['collision_severity'].isin([1, 2, 3])].copy()
        return clean_df


if __name__ == '__main__':
    decoder = Stats19Decoder('dft-road-casualty-statistics-collision-2025.csv')
    df = decoder.decode()
    print("Decoded DataFrame Shape:", df.shape)
    print("Severity Distribution (is_severe):\n", df['is_severe'].value_counts(normalize=True))
