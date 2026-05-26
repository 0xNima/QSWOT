"""Pure-function tests for src/swot_fields.py — value coercion, fill detection,
field type lookup. No QGIS / Qt required (see conftest.py)."""

import math

import pytest

from src.swot_fields import is_fill_value, coerce_value, field_type, TYPES


class TestIsFillValue:
    @pytest.mark.parametrize("value", [-999, -999.0, -998.7, -999.4,
                                       -99999999, -99999999.0,
                                       -999999999999])
    def test_hydrocron_integer_sentinels(self, value):
        assert is_fill_value(value) is True

    @pytest.mark.parametrize("value", [9.96921e+36, -9.96921e+36, 1e35])
    def test_netcdf_magnitude_fill(self, value):
        assert is_fill_value(value) is True

    def test_nan_and_inf(self):
        assert is_fill_value(float('nan')) is True
        assert is_fill_value(float('inf')) is True
        assert is_fill_value(float('-inf')) is True

    @pytest.mark.parametrize("value", [0, -1, 12.5, 3.14, -998, 1e29])
    def test_real_measurements_are_not_fills(self, value):
        assert is_fill_value(value) is False

    @pytest.mark.parametrize("value", [None, '999', '-999', True, False, [], {}])
    def test_non_numeric_inputs_are_not_fills(self, value):
        # We never want bools, strings, None, or containers to be treated as
        # numeric sentinels — the string '-999' is a string, not the fill.
        assert is_fill_value(value) is False


class TestCoerceValue:
    def test_none_passes_through(self):
        assert coerce_value('wse', None) is None

    def test_string_field_passes_through(self):
        # reach_id defaults to QString; raw value is returned untouched.
        assert coerce_value('reach_id', '73111100013') == '73111100013'
        assert coerce_value('reach_id', '') == ''  # not normalized for strings

    def test_numeric_field_drops_no_data_string(self):
        assert coerce_value('wse', 'no_data') is None
        assert coerce_value('wse', 'NaN') is None
        assert coerce_value('wse', '') is None

    def test_numeric_field_drops_semicolon_joined(self):
        # 'overlap'-style merged-observation values can't coerce to one number.
        assert coerce_value('wse', '76;1') is None

    def test_numeric_field_drops_hydrocron_fills(self):
        # Real value from the layer's perspective: bare float, not string.
        assert coerce_value('wse', -999.0) is None
        assert coerce_value('wse', 9.96921e+36) is None

    def test_numeric_field_keeps_real_values(self):
        assert coerce_value('wse', 12.5) == 12.5
        assert coerce_value('wse', 0) == 0

    def test_string_to_numeric_parse(self):
        # Hydrocron sometimes serializes numbers as strings in JSON.
        assert coerce_value('wse', '12.5') == 12.5
        assert coerce_value('cycle_id', '7') == 7

    def test_string_to_numeric_fill_after_parse(self):
        # A fill arriving as a string still must be stripped.
        assert coerce_value('wse', '-999') is None
        assert coerce_value('wse', '9.96921e+36') is None


class TestFieldType:
    def test_known_numeric_field(self):
        from qgis.PyQt.QtCore import QMetaType
        assert field_type('wse') == QMetaType.Type.Double

    def test_unknown_field_defaults_to_string(self):
        from qgis.PyQt.QtCore import QMetaType
        assert field_type('not_a_swot_field') == QMetaType.Type.QString

    def test_types_dict_is_self_consistent(self):
        # Every value in TYPES should be a QMetaType.Type enum member.
        from qgis.PyQt.QtCore import QMetaType
        valid = {QMetaType.Type.Double, QMetaType.Type.Int,
                 QMetaType.Type.LongLong, QMetaType.Type.QString}
        for name, t in TYPES.items():
            assert t in valid, f"{name} has unexpected type {t!r}"
