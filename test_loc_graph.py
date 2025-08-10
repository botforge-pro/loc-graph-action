#!/usr/bin/env python3
"""Tests for loc_graph.py"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from loc_graph import nice_round, format_number


@pytest.mark.parametrize("input_val,max_expected", [
    (5, 10),
    (10, 10),
    (15, 20),
    (25, 50),
    (50, 50),
    (75, 100),
    (100, 100),
    (150, 200),
    (200, 250),
    (246, 300),  # 246 * 1.1 = 270.6
    (270, 300),
    (400, 500),
    (500, 600),
    (750, 1000),
    (1000, 1200),
    (1500, 2000),
    (2200, 2500),
    (4500, 5000),
    (7500, 10000),
])
def test_nice_round_with_multiplier(input_val, max_expected):
    """Test nice_round with 1.1 multiplier as used in real code"""
    result = nice_round(input_val * 1.1)
    assert result <= max_expected, f"nice_round({input_val} * 1.1) = {result}, expected <= {max_expected}"
    assert result >= input_val, f"nice_round({input_val} * 1.1) = {result}, should be >= {input_val}"


def test_nice_round_edge_cases():
    """Test edge cases"""
    assert nice_round(0) == 10  # Zero case
    assert nice_round(1) == 10  # Minimum
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
    assert format_number(1234) == "1.2k"  # Should round down
    assert format_number(1999) == "2k"    # Should round up
    assert format_number(1001) == "1k"    # Should round down