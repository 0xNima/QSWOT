# QSWOT tests

Pure-Python unit tests with **no QGIS dependency**. They cover the parts of
the plugin where bugs have actually hidden — value coercion, fill-value
detection, time parsing, response-shape parsing.

QGIS / Qt modules are stubbed in `conftest.py` so tests run under any plain
Python environment. The matplotlib dialog, the async `QgsTask` event-loop
machinery, and live HTTP are **not** covered here.

## Running

```bash
# From the plugin root
pip install pytest numpy   # one-time, into any Python env
pytest tests/
```

`scipy` is optional; tests that need it (Spearman / Kendall correlation)
are skipped automatically when it's absent.

## Layout

```
tests/
├── conftest.py               # Stubs qgis / Qt so src/* can be imported
├── test_swot_fields.py       # is_fill_value, coerce_value, field_type
├── test_stats.py             # parse_time, _coerce_float, compute_correlation
├── test_api_parsing.py       # extract_api_error + fixture-driven shape tests
├── fixtures/
│   ├── README.md             # Source URL + capture date for every fixture
│   ├── lakes_worker_caspian.json
│   └── hydrocron_reach_response.json
└── smoke_live_api.py         # OPTIONAL: hits real APIs. Not run by pytest.
```

## Adding tests

- **For a pure-function bug**: extend `test_swot_fields.py` or `test_stats.py`
  with a failing assertion that reproduces the bug, then fix the source.
- **For an API shape change**: refetch the fixture (URL is in `fixtures/README.md`),
  save in place, and update the assertions in `test_api_parsing.py`.
- **Don't write tests that hit the live network from inside `pytest`.** Add a
  check to `smoke_live_api.py` instead and run it manually before releases.

## Smoke test (manual, pre-release)

```bash
python tests/smoke_live_api.py
```

Hits PO.DAAC FTS, Hydrocron, and the lakes worker once each. If anything fails
here, investigate the response body before changing parsing logic — it
usually means an upstream API drifted.
