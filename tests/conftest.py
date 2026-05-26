"""Stub QGIS modules so pure-function tests (`src/swot_fields.py`,
`src/stats.py`) run under any plain Python environment without needing QGIS
installed. Imported automatically by pytest before any test module loads.

Anything Qt/QGIS-bound (`api.py`, `statistics_dialog.py`, the UI/`uic` loader)
needs a real QGIS environment and is not covered here — keep those for manual
in-QGIS testing or for the optional `smoke_live_api.py` script.
"""

import sys
import types


def _stub(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
    return sys.modules[name]


qgis = _stub('qgis')
qgis_pyqt = _stub('qgis.PyQt')
qgis_qtcore = _stub('qgis.PyQt.QtCore')
qgis_qtnet = _stub('qgis.PyQt.QtNetwork')
qgis_core = _stub('qgis.core')


# --- QtCore stubs -------------------------------------------------------

class _QMetaType:
    class Type:
        QString = 10
        Double = 6
        Int = 2
        LongLong = 4
        Float = 38
        UInt = 3
        ULongLong = 5


class _Qt:
    QueuedConnection = 'QueuedConnection'


def _pyqt_signal(*_a, **_kw):
    return _SignalStub()


def _pyqt_slot(*_a, **_kw):
    return lambda fn: fn


class _SignalStub:
    def emit(self, *_a, **_kw):
        pass

    def connect(self, *_a, **_kw):
        pass

    def disconnect(self, *_a, **_kw):
        pass


qgis_qtcore.QMetaType = _QMetaType
qgis_qtcore.Qt = _Qt
qgis_qtcore.pyqtSignal = _pyqt_signal
qgis_qtcore.pyqtSlot = _pyqt_slot
qgis_qtcore.QUrl = type('QUrl', (), {})
qgis_qtcore.QUrlQuery = type('QUrlQuery', (), {})
qgis_qtcore.QEventLoop = type('QEventLoop', (), {})
qgis_qtcore.QMetaObject = type('QMetaObject', (), {})


# --- QtNetwork stubs ----------------------------------------------------

qgis_qtnet.QNetworkAccessManager = type('QNetworkAccessManager', (), {})
qgis_qtnet.QNetworkRequest = type('QNetworkRequest', (), {})
qgis_qtnet.QNetworkReply = type('QNetworkReply', (), {'NoError': 0,
                                                       'OperationCanceledError': 5})


# --- qgis.core stubs ----------------------------------------------------

class _QgsFeatureRequest:
    """Minimal stand-in so `stats.fetch_pair` / `fetch_timeseries` can be
    imported. Tests that exercise them should pass a fake layer that returns
    feature dicts directly; the request object isn't actually consulted."""

    def setSubsetOfAttributes(self, _names, _fields):
        return self

    def setFilterExpression(self, _expr):
        return self


class _QgsTask:
    CanCancel = 1

    def __init__(self, *_a, **_kw):
        pass

    def setProgress(self, _v):
        pass

    def isCanceled(self):
        return False

    def cancel(self):
        pass


class _QgsMessageLog:
    @staticmethod
    def logMessage(_msg, *_a, **_kw):
        pass


class _Qgis:
    Info = 0
    Warning = 1
    Critical = 2


qgis_core.QgsFeatureRequest = _QgsFeatureRequest
qgis_core.QgsTask = _QgsTask
qgis_core.QgsMessageLog = _QgsMessageLog
qgis_core.Qgis = _Qgis

# Add the plugin root to sys.path so `from src.swot_fields import ...` works
# without an editable install.
import os
PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)
