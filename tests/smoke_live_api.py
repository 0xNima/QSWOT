"""Optional pre-release smoke test against the live APIs.

Run manually: ``python tests/smoke_live_api.py``. Not collected by pytest
(filename doesn't start with ``test_``). Verifies that each upstream is
reachable and responds with the shape our parser expects. If any of these
fails, the breakage is on the *server* side, not in plugin code — investigate
the response body before changing parsing logic.
"""

import json
import sys
from urllib.request import Request, urlopen


CHECKS = [
    {
        'name': 'PO.DAAC FTS rivers — Rhine',
        'url': 'https://fts.podaac.earthdata.nasa.gov/v1/rivers/Rhine?page_number=1&page_size=5',
        'must_have': ['results'],
    },
    {
        'name': 'Hydrocron timeseries — Reach',
        'url': ('https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries'
                '?feature=Reach&feature_id=23261000181'
                '&start_time=2024-01-01T00:00:00Z&end_time=2024-02-01T00:00:00Z'
                '&fields=reach_id,time_str,wse&output=geojson'),
        'must_have': ['status', 'results'],
    },
    {
        'name': 'swot-lake worker — Caspian',
        'url': 'https://lakes.swot-lake.workers.dev/?q=caspian',
        'must_have': ['results'],
    },
]


def main():
    failures = 0
    for check in CHECKS:
        print(f"[{check['name']}]")
        print(f"  GET {check['url']}")
        try:
            with urlopen(Request(check['url']), timeout=30) as resp:
                body = resp.read().decode('utf-8', 'replace')
                data = json.loads(body)
        except Exception as e:
            print(f"  FAIL: {e}\n")
            failures += 1
            continue
        missing = [k for k in check['must_have'] if k not in data]
        if missing:
            print(f"  FAIL: response missing keys {missing}")
            print(f"  body (truncated): {body[:200]!r}\n")
            failures += 1
        else:
            print(f"  OK: shape includes {check['must_have']}\n")
    return failures


if __name__ == '__main__':
    sys.exit(main())
