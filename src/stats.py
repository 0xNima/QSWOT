"""Stats helpers: numeric-field discovery, value extraction, correlation,
time-series assembly. Pure functions — no Qt UI.

Time-axis convention
--------------------
SWOT publishes `time` and `time_tai` as seconds since 2000-01-01 00:00:00 UTC
(see SWOT product spec), not Unix epoch. `time_str` is an ISO 8601 string.
`parse_time` handles both: numeric → SWOT epoch, string → ISO 8601.
"""

from datetime import datetime, timedelta, timezone

import numpy as np

from qgis.PyQt.QtCore import QMetaType
from qgis.core import QgsFeatureRequest

from .swot_fields import is_fill_value


NUMERIC_QMETA_TYPES = {
    QMetaType.Type.Double,
    QMetaType.Type.Int,
    QMetaType.Type.LongLong,
    QMetaType.Type.Float,
    QMetaType.Type.UInt,
    QMetaType.Type.ULongLong,
}

SWOT_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


# ---- field introspection ------------------------------------------------

def numeric_field_names(layer):
    """Names of fields whose type is something we can correlate / plot."""
    return [f.name() for f in layer.fields() if f.type() in NUMERIC_QMETA_TYPES]


def all_field_names(layer):
    return [f.name() for f in layer.fields()]


def time_field_candidates(layer):
    """Heuristic: fields whose name suggests a timestamp. Falls back to all
    numeric fields if no obvious time field is present."""
    names = all_field_names(layer)
    preferred = [n for n in names if n in ('time', 'time_tai', 'time_str',
                                           'p_date_t0', 'p_ref_date',
                                           'range_start_time', 'range_end_time',
                                           'ingest_time')]
    return preferred or numeric_field_names(layer)


# ---- value coercion -----------------------------------------------------

def _coerce_float(value):
    if value is None:
        return None
    if hasattr(value, 'isNull') and callable(value.isNull) and value.isNull():
        return None
    if isinstance(value, (int, float)):
        if is_fill_value(value):
            return None
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s or s.lower() in ('no_data', 'na', 'nan', 'null', 'none'):
            return None
        if ';' in s:
            return None
        try:
            v = float(s)
        except ValueError:
            return None
        return None if is_fill_value(v) else v
    return None


_MAX_SWOT_SECONDS = 5e9  # ~158 years from 2000 — anything beyond is fill/junk


def parse_time(value):
    """SWOT epoch seconds (numeric) or ISO 8601 (string) → datetime, or None.

    Returns None for NaN/NULL, NetCDF-style fill values (e.g. 9.96921e+36),
    or strings that don't parse. Never raises."""
    if value is None:
        return None
    if hasattr(value, 'isNull') and callable(value.isNull) and value.isNull():
        return None
    if isinstance(value, (int, float)):
        if is_fill_value(value):
            return None
        v = float(value)
        if abs(v) > _MAX_SWOT_SECONDS:
            return None
        try:
            return SWOT_EPOCH + timedelta(seconds=v)
        except (OverflowError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s or s.lower() in ('no_data', 'na', 'nan'):
            return None
        # Handle trailing 'Z' (UTC indicator) that fromisoformat doesn't accept
        # on older Python versions.
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


# ---- correlation --------------------------------------------------------

def fetch_pair(layer, x_field, y_field, expression=None, only_selected=False):
    """Two parallel numpy float arrays — NULLs / sentinels / unparseable skipped."""
    request = _build_request(layer, [x_field, y_field], expression)
    iterator = _iterate(layer, request, only_selected)

    xs, ys = [], []
    for feat in iterator:
        x = _coerce_float(feat[x_field])
        y = _coerce_float(feat[y_field])
        if x is None or y is None:
            continue
        xs.append(x)
        ys.append(y)
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)


def compute_correlation(xs, ys, method='pearson'):
    """Return (r, p, n). p is NaN if scipy is unavailable; Pearson still works
    via numpy.corrcoef as a fallback."""
    n = len(xs)
    if n < 2:
        return float('nan'), float('nan'), n

    try:
        from scipy import stats as scipy_stats
    except ImportError:
        scipy_stats = None

    if scipy_stats is None:
        if method != 'pearson':
            raise RuntimeError(
                f"{method!r} correlation requires scipy, which isn't installed."
            )
        return float(np.corrcoef(xs, ys)[0, 1]), float('nan'), n

    fns = {
        'pearson': scipy_stats.pearsonr,
        'spearman': scipy_stats.spearmanr,
        'kendall': scipy_stats.kendalltau,
    }
    if method not in fns:
        raise ValueError(f"Unknown correlation method: {method!r}")
    result = fns[method](xs, ys)
    r = float(getattr(result, 'statistic', result[0]))
    p = float(getattr(result, 'pvalue', result[1]))
    return r, p, n


def linear_regression(xs, ys):
    slope, intercept = np.polyfit(xs, ys, 1)
    return float(slope), float(intercept)


# ---- time series --------------------------------------------------------

def fetch_timeseries(layer, value_field, time_field, group_field=None,
                     expression=None, only_selected=False, max_groups=25):
    """Return dict[group_key] -> (times, values), each sorted by time.

    group_key is None if no grouping, otherwise the raw value of group_field
    (a SWORD reach_id, PLD lake_id, river_name, …). If the result would have
    more than `max_groups` groups, only the largest by sample count are kept,
    and the dropped count is reported in the second return value.
    """
    needed = [value_field, time_field]
    if group_field:
        needed.append(group_field)
    request = _build_request(layer, needed, expression)
    iterator = _iterate(layer, request, only_selected)

    groups = {}
    for feat in iterator:
        v = _coerce_float(feat[value_field])
        t = parse_time(feat[time_field])
        if v is None or t is None:
            continue
        key = feat[group_field] if group_field else None
        # QVariant NULL → None for grouping consistency
        if hasattr(key, 'isNull') and callable(key.isNull) and key.isNull():
            key = None
        groups.setdefault(key, []).append((t, v))

    result = {}
    for key, items in groups.items():
        items.sort(key=lambda kv: kv[0])
        result[key] = (
            np.asarray([kv[0] for kv in items]),
            np.asarray([kv[1] for kv in items], dtype=float),
        )

    dropped = 0
    if len(result) > max_groups:
        ranked = sorted(result, key=lambda k: -len(result[k][0]))
        kept_keys = ranked[:max_groups]
        dropped = len(result) - max_groups
        result = {k: result[k] for k in kept_keys}
    return result, dropped


# ---- internal -----------------------------------------------------------

def _build_request(layer, field_names, expression):
    request = QgsFeatureRequest().setSubsetOfAttributes(field_names, layer.fields())
    if expression:
        request.setFilterExpression(expression)
    return request


def _iterate(layer, request, only_selected):
    if only_selected:
        return layer.getSelectedFeatures(request)
    return layer.getFeatures(request)
