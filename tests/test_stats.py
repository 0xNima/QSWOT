"""Pure-function tests for src/stats.py — time parsing, value coercion,
correlation. No QGIS / Qt required (see conftest.py)."""

from datetime import datetime, timezone

import numpy as np
import pytest

from src.stats import (
    parse_time,
    _coerce_float,
    compute_correlation,
    linear_regression,
)


SWOT_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


class TestParseTime:
    def test_swot_epoch_zero(self):
        assert parse_time(0) == SWOT_EPOCH

    def test_swot_epoch_offset(self):
        # 86400 seconds = 1 day after the SWOT epoch
        assert parse_time(86400) == datetime(2000, 1, 2, tzinfo=timezone.utc)

    def test_iso_string_with_z(self):
        result = parse_time('2024-01-15T12:30:00Z')
        assert result == datetime(2024, 1, 15, 12, 30, tzinfo=timezone.utc)

    def test_iso_string_without_tz(self):
        result = parse_time('2024-01-15T12:30:00')
        assert result.year == 2024 and result.month == 1 and result.day == 15

    @pytest.mark.parametrize("v", [-999, -99999999, 9.96921e+36,
                                   float('nan'), float('inf')])
    def test_sentinels_return_none(self, v):
        assert parse_time(v) is None

    @pytest.mark.parametrize("v", ['no_data', 'NaN', '', 'not a date'])
    def test_bad_strings_return_none(self, v):
        assert parse_time(v) is None

    def test_out_of_range_seconds(self):
        # Absurd magnitude that would overflow datetime arithmetic
        assert parse_time(1e15) is None
        assert parse_time(-1e15) is None

    def test_none(self):
        assert parse_time(None) is None


class TestCoerceFloat:
    @pytest.mark.parametrize("v", [12.5, 0, -1, 1e29])
    def test_real_values(self, v):
        assert _coerce_float(v) == float(v)

    @pytest.mark.parametrize("v", [-999, -999.0, 9.96921e+36, float('nan')])
    def test_fill_values_dropped(self, v):
        assert _coerce_float(v) is None

    def test_string_numeric(self):
        assert _coerce_float('12.5') == 12.5
        assert _coerce_float('  -3.14  ') == -3.14

    def test_string_fill_dropped(self):
        assert _coerce_float('-999') is None
        assert _coerce_float('no_data') is None
        assert _coerce_float('76;1') is None  # joined merged value

    def test_none(self):
        assert _coerce_float(None) is None


class TestComputeCorrelation:
    def test_perfect_positive(self):
        xs = np.array([1, 2, 3, 4, 5], dtype=float)
        ys = np.array([2, 4, 6, 8, 10], dtype=float)
        r, p, n = compute_correlation(xs, ys, 'pearson')
        assert r == pytest.approx(1.0)
        assert n == 5

    def test_perfect_negative(self):
        xs = np.array([1, 2, 3, 4, 5], dtype=float)
        ys = np.array([5, 4, 3, 2, 1], dtype=float)
        r, _, _ = compute_correlation(xs, ys, 'pearson')
        assert r == pytest.approx(-1.0)

    def test_too_few_points(self):
        r, p, n = compute_correlation(np.array([1.0]), np.array([2.0]))
        assert np.isnan(r) and np.isnan(p) and n == 1

    def test_unknown_method_raises(self):
        try:
            from scipy import stats  # noqa: F401
        except ImportError:
            pytest.skip("scipy not available — method validation is skipped")
        with pytest.raises(ValueError):
            compute_correlation(np.array([1.0, 2.0]),
                                np.array([3.0, 4.0]),
                                method='nonsense')


class TestLinearRegression:
    def test_known_line(self):
        xs = np.array([0.0, 1.0, 2.0, 3.0])
        ys = 2 * xs + 1.0  # slope=2, intercept=1
        slope, intercept = linear_regression(xs, ys)
        assert slope == pytest.approx(2.0)
        assert intercept == pytest.approx(1.0)
