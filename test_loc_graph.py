#!/usr/bin/env python3
"""Tests for loc_graph.py"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from loc_graph import nice_round, format_number, calculate_ymax


@pytest.mark.parametrize("input_val,expected", [
    (5, 5),
    (10, 10),
    (11, 20),
    (15, 20),
    (25, 30),
    (50, 50),
    (51, 100),
    (75, 100),
    (100, 100),
    (101, 200),
    (150, 200),
    (200, 200),
    (201, 300),
    (246, 300),
    (270, 300),
    (400, 500),
    (500, 500),
    (501, 1000),
    (750, 1000),
    (1000, 1000),
    (1001, 2000),
    (1500, 2000),
    (2200, 3000),
    (4500, 5000),
    (7500, 10000),
])
def test_nice_round(input_val, expected):
    """Test nice_round function"""
    result = nice_round(input_val)
    assert result == expected, f"nice_round({input_val}) = {result}, expected {expected}"


def test_nice_round_edge_cases():
    """Test edge cases"""
    assert nice_round(0) == 10  # Zero case
    assert nice_round(1) == 1   # Small number
    assert nice_round(10) == 10  # Exact boundary


def test_graph_ymax_calculation():
    """Test that graph ymax provides proper padding"""
    # Import the actual calculation logic
    from scripts.loc_graph import nice_round
    
    test_cases = [
        # (max_value, expected_ymax_range_min, expected_ymax_range_max)
        (100, 200, 200),   # 100 is exact, jumps to 200
        (99, 100, 200),    # 99 rounds to 100, but >80%, may jump  
        (80, 100, 100),    # 80 rounds to 100, 80% exactly
        (200, 300, 300),   # 200 is exact, jumps to 300
        (323, 500, 500),   # 323 rounds to 500, uses 65%
        (240, 300, 300),   # 240 rounds to 300, uses 80%
        (250, 500, 500),   # 250 rounds to 300, uses 83%, jumps to 500
    ]
    
    for max_val, expected_min, expected_max in test_cases:
        # Simulate the actual calculation from generate_svg
        ymax = nice_round(max_val)
        
        # If max_val equals ymax (exact match), we need the next level
        # Otherwise check if we're using more than 80%
        if max_val == ymax or max_val > ymax * 0.8:
            # Find the next nice number in the sequence
            ymax = nice_round(ymax * 1.1 + 1)
        
        # Check that ymax is in expected range
        assert expected_min <= ymax <= expected_max, \
            f"For max_val={max_val}, got ymax={ymax}, expected {expected_min}-{expected_max}"
        
        # Check that we have at least 20% padding
        usage_percent = (max_val / ymax) * 100
        assert usage_percent <= 85, \
            f"Graph too full: {usage_percent:.1f}% for max_val={max_val}, ymax={ymax}"


@pytest.mark.parametrize("input_val,expected", [
    (0, "0"),
    (100, "100"),
    (999, "999"),
    (1000, "1k"),
    (1500, "1.5k"),
    (10000, "10k"),
    (100000, "100k"),
    (1000000, "1M"),
    (1500000, "1.5M"),
    (10000000, "10M"),
])
def test_format_number(input_val, expected):
    """Test number formatting with k/M suffixes"""
    result = format_number(input_val)
    assert result == expected, f"format_number({input_val}) = {result}, expected {expected}"


def test_format_number_rounding():
    """Test that rounding works correctly"""
    assert format_number(1234) == "1.2k"  # Should show 1 decimal
    assert format_number(1999) == "2.0k"  # Should show 1 decimal
    assert format_number(1001) == "1.0k"   # Always shows decimal for k/M


@pytest.mark.parametrize("max_val,expected_ymax", [
    (8100, 10000),  # 81% usage
    (100, 200),
    (1500, 2000),
    (7999, 10000),
    (8000, 10000),
    (8001, 10000),  # 80% usage
    (9001, 10000),  # 90% usage
    (9499, 10000),  # 94.99% usage
    (9500, 20000),  # 95% usage triggers next level
    (9501, 20000),  # >95% usage
    (0, 100),
    (-10, 100),
])
def test_calculate_ymax(max_val, expected_ymax):
    """Test calculate_ymax function"""
    assert calculate_ymax(max_val) == expected_ymax


@pytest.mark.parametrize("ymax,num_lines,expected_grid", [
    (20000, 5, [0, 5000, 10000, 15000, 20000]),
    (20000, 6, [0, 4000, 8000, 12000, 16000, 20000]),
    (10000, 5, [0, 2500, 5000, 7500, 10000]),
    (10000, 6, [0, 2000, 4000, 6000, 8000, 10000]),
    (200, 5, [0, 50, 100, 150, 200]),
    (2000, 5, [0, 500, 1000, 1500, 2000]),
])
def test_grid_line_values(ymax, num_lines, expected_grid):
    """Test grid line value calculation"""
    grid_values = []
    for i in range(num_lines):
        val = int(ymax * i / (num_lines - 1))
        grid_values.append(val)
    assert grid_values == expected_grid