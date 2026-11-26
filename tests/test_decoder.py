"""
Unit Tests for STATS19 Decoder
"""

import pytest
import pandas as pd
import numpy as np
from src.decoder import Stats19Decoder, WEATHER_LOOKUP, LIGHT_LOOKUP, ROAD_TYPE_LOOKUP


def test_decoder_lookups():
    assert WEATHER_LOOKUP[1] == 'Fine no high winds'
    assert LIGHT_LOOKUP[1] == 'Daylight'
    assert ROAD_TYPE_LOOKUP[3] == 'Dual carriageway'


def test_decoder_execution():
    decoder = Stats19Decoder('dft-road-casualty-statistics-collision-2025.csv')
    df = decoder.decode()
    
    assert 'is_severe' in df.columns
    assert 'weather_label' in df.columns
    assert df['is_severe'].isin([0, 1]).all()
    assert len(df) > 10000
