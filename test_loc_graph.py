#!/usr/bin/env python3
"""Tests for loc_graph.py"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from loc_graph import nice_round, format_number


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