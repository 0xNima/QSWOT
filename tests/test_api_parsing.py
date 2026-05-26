"""Tests that validate the response-shape assumptions our API code makes,
using captured real responses in tests/fixtures/. No live network calls."""

import json
import os

import pytest

from src.api import extract_api_error
from src.swot_fields import coerce_value


FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


class TestLakesWorkerShape:
    """Mirrors src/api.py HydrocronLakeTask.on_page_reply parsing."""

    def setup_method(self):
        self.data = load_fixture('lakes_worker_caspian.json')

    def test_has_results_key(self):
        assert isinstance(self.data.get('results'), list)

    def test_split_semicolon_joined_ids(self):
        # Replicate the dedup + split logic on a real fixture.
        ids = set()
        for item in self.data['results']:
            for part in str(item['lake_id']).split(';'):
                part = part.strip()
                if part:
                    ids.add(part)
        # 3 standalone + 4 from 2 joined entries, all unique:
        # 7250180012, 2810003512, 2810003522, 2810004162, 2810004152,
        # 2810004212, 2810004052 → 7 total
        assert len(ids) == 7
        assert '2810004162' in ids
        assert '2810004152' in ids

    def test_substring_name_filter_keeps_all_caspian(self):
        # Substring match on lake_name (HydrocronLakeTask.filter_by_name).
        needle = 'caspian'
        for item in self.data['results']:
            assert needle in item['lake_name'].lower()


class TestHydrocronReachShape:
    """Mirrors src/api.py parse_item_reply parsing for a successful 200."""

    def setup_method(self):
        self.data = load_fixture('hydrocron_reach_response.json')

    def test_features_path_exists(self):
        features = self.data['results']['geojson']['features']
        assert len(features) == 2

    def test_extract_api_error_is_none_for_success(self):
        assert extract_api_error(self.data) is None

    def test_fill_value_in_real_feature_is_dropped_by_coerce(self):
        # The second feature has wse = -999.0 (Hydrocron sentinel).
        # coerce_value should turn it into None.
        f2 = self.data['results']['geojson']['features'][1]
        assert coerce_value('wse', f2['properties']['wse']) is None

    def test_real_measurement_is_kept(self):
        f1 = self.data['results']['geojson']['features'][0]
        assert coerce_value('wse', f1['properties']['wse']) == pytest.approx(245.123)


class TestExtractApiError:
    """extract_api_error is shared logic across reach + lake reply parsing."""

    def test_typical_hydrocron_400_body(self):
        body = {"error": "400: Results with the specified Feature ID 99 were not found"}
        # The "400: " prefix that duplicates HTTP status should be stripped.
        assert extract_api_error(body) == (
            "Results with the specified Feature ID 99 were not found"
        )

    def test_missing_error_field(self):
        assert extract_api_error({"status": "200 OK", "hits": 0}) is None

    def test_non_dict_input(self):
        assert extract_api_error("just a string") is None
        assert extract_api_error(None) is None
