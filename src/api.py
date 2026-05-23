import json
from urllib.parse import quote
from qgis.PyQt.QtCore import (
    pyqtSignal, pyqtSlot, QUrl, QUrlQuery, QEventLoop, Qt,
)
from qgis.PyQt.QtNetwork import (
    QNetworkAccessManager, QNetworkRequest, QNetworkReply,
)
from qgis.core import QgsTask, QgsMessageLog, Qgis
from typing import Optional, Iterable, List, Callable


MAX_CONCURRENT = 8

PAGE_SIZE = 100
PAGE_TIMEOUT_MS = 20000
REACH_TIMEOUT_MS = 30000

FTS_URL = "https://fts.podaac.earthdata.nasa.gov/v1/rivers/{name}"
HYDROCRON_URL = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"


def _build_request(url, params, timeout_ms):
    qurl = QUrl(url)
    query = QUrlQuery()
    for k, v in params.items():
        query.addQueryItem(str(k), str(v))
    qurl.setQuery(query)
    request = QNetworkRequest(qurl)
    request.setTransferTimeout(timeout_ms)
    return request


def _extract_api_error(data):
    if not isinstance(data, dict):
        return None
    msg = data.get('error') or data.get('message')
    if not isinstance(msg, str):
        return None
    # Strip a leading "<digits>: " prefix that just duplicates the HTTP code.
    prefix, sep, rest = msg.partition(': ')
    return rest if sep and prefix.isdigit() else msg


class HydrocronMasterTask(QgsTask):
    """Async fetch task.

    All network I/O is driven by a QNetworkAccessManager + QEventLoop that live
    on the task's worker thread. No nested event loops, no thread pool — so
    cancellation (including QGIS shutdown) unwinds promptly: aborting in-flight
    QNetworkReplies makes the single event loop exit cleanly.
    """

    # Emitted (queued to the main thread) each time a reach's features arrive,
    # so the dialog/layer code can stream them into a QGIS layer incrementally.
    features_ready = pyqtSignal(list)

    def __init__(
            self,
            description: str,
            river_name: str,
            fields: List[str],
            start_time: str,
            end_time: str,
            reach_ids: Optional[Iterable] = None,
            callback: Optional[Callable] = None,
            **kwargs,
    ):
        super().__init__(description, QgsTask.CanCancel)
        self.river_name = river_name
        self.reach_ids = set(reach_ids) if reach_ids else set()
        self.callback = callback
        self.collected_features = []
        self.exception = None
        self.fields = fields or []
        self.start_time = start_time
        self.end_time = end_time
        self.limit = kwargs.get('limit', -1)

        # Created in run() on the worker thread so they have correct affinity.
        self._nam = None
        self._loop = None

        # Pagination state
        self._page_ids = set()
        self._page_raw_count = 0
        self._page_no = 0

        # Per-reach state
        self._reach_pending = []
        self._reach_in_flight = {}  # QNetworkReply -> rid
        self._reach_total = 0
        self._reach_completed = 0
        self._success = 0
        self._empty = 0
        self._failure = 0
        self._filtered_features = 0
        self._first_failure = None  # (rid, err) for the first failed reach

    # ---- public API ------------------------------------------------------

    def cancel(self):
        # Defer the actual abort to the worker thread (which owns the replies)
        # via a queued slot invocation.
        if self._loop is not None:
            from qgis.PyQt.QtCore import QMetaObject
            QMetaObject.invokeMethod(self, "_handle_cancel", Qt.QueuedConnection)
        super().cancel()

    def run(self):
        try:
            self._nam = QNetworkAccessManager()
            self._loop = QEventLoop()

            if self.reach_ids:
                self._start_reach_phase()
            elif self.river_name:
                self._fetch_page(1)
            else:
                self.exception = "No reach IDs or river name provided."
                return False

            self._loop.exec_()

            if self.isCanceled():
                return False
            return True
        except Exception as e:
            self.exception = str(e)
            return False
        finally:
            self._nam = None
            self._loop = None

    def finished(self, result):
        if result:
            if self.callback:
                self.callback(self.collected_features)
        else:
            msg = self.exception or "User cancelled"
            QgsMessageLog.logMessage(f"Hydrocron Task Failed: {msg}", level=Qgis.Warning)

    # ---- cancellation ---------------------------------------------------

    @pyqtSlot()
    def _handle_cancel(self):
        # Runs on the worker thread (where _loop lives).
        self._reach_pending = []
        for reply in list(self._reach_in_flight.keys()):
            reply.abort()
        if not self._reach_in_flight and self._loop is not None:
            self._loop.quit()

    # ---- pagination phase -----------------------------------------------

    def _fetch_page(self, page_no):
        if self.isCanceled():
            self._loop.quit()
            return
        self._page_no = page_no
        self.setProgress(min(page_no * 2, 25))

        url = FTS_URL.format(name=quote(self.river_name))
        params = {'page_number': page_no, 'page_size': PAGE_SIZE}
        reply = self._nam.get(_build_request(url, params, PAGE_TIMEOUT_MS))
        reply.finished.connect(lambda r=reply: self._on_page_reply(r))

    def _on_page_reply(self, reply):
        try:
            if self.isCanceled() or reply.error() == QNetworkReply.OperationCanceledError:
                self._loop.quit()
                return

            if reply.error() != QNetworkReply.NoError:
                self.exception = (
                    f"NASA API Error on page {self._page_no}: {reply.errorString()}"
                )
                self._loop.quit()
                return

            try:
                data = json.loads(bytes(reply.readAll()).decode('utf-8', 'replace'))
            except Exception as e:
                self.exception = f"NASA API Error on page {self._page_no}: {e}"
                self._loop.quit()
                return

            results = data.get('results') or []
            self._page_raw_count += len(results)
            for item in results:
                if 0 < self.limit <= len(self._page_ids):
                    break
                rid = item.get('reach_id')
                if rid:
                    self._page_ids.add(rid)

            done = (
                not results
                or len(results) < PAGE_SIZE
                or (0 < self.limit <= len(self._page_ids))
            )
            if done:
                QgsMessageLog.logMessage(
                    f"Fetched {len(self._page_ids)} unique reach IDs for "
                    f"{self.river_name!r} (from {self._page_raw_count} raw record(s) "
                    f"across {self._page_no} page(s))",
                    level=Qgis.Info,
                )
                self.reach_ids = self._page_ids
                if not self.reach_ids:
                    self.exception = "No reach IDs found."
                    self._loop.quit()
                    return
                self._start_reach_phase()
            else:
                self._fetch_page(self._page_no + 1)
        finally:
            reply.deleteLater()

    # ---- per-reach phase ------------------------------------------------

    def _start_reach_phase(self):
        self._reach_pending = list(self.reach_ids)
        self._reach_total = len(self._reach_pending)
        self.setProgress(10)
        for _ in range(min(MAX_CONCURRENT, len(self._reach_pending))):
            self._submit_reach()
        if not self._reach_in_flight:
            self._finish_reach_phase()

    def _submit_reach(self):
        if self.isCanceled() or not self._reach_pending:
            return
        rid = self._reach_pending.pop()
        params = {
            'fields': ",".join(self.fields),
            'feature': 'Reach',
            'output': 'geojson',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'feature_id': rid,
        }
        reply = self._nam.get(_build_request(HYDROCRON_URL, params, REACH_TIMEOUT_MS))
        self._reach_in_flight[reply] = rid
        reply.finished.connect(lambda r=reply, rd=rid: self._on_reach_reply(r, rd))

    def _on_reach_reply(self, reply, rid):
        try:
            self._reach_in_flight.pop(reply, None)

            if reply.error() == QNetworkReply.OperationCanceledError or self.isCanceled():
                # Don't count cancelled requests; just check if we can exit.
                if self.isCanceled() and not self._reach_in_flight:
                    self._loop.quit()
                return

            self._reach_completed += 1
            self.setProgress(10 + int(self._reach_completed / self._reach_total * 90))

            features, err = self._parse_reach_reply(reply, rid)
            if err is not None:
                self._failure += 1
                if self._first_failure is None:
                    self._first_failure = (rid, err)
            elif not features:
                self._empty += 1
            else:
                raw = len(features)
                features = self._filter_by_river(features)
                self._filtered_features += raw - len(features)
                if not features:
                    self._empty += 1
                else:
                    self._success += 1
                    self.collected_features.extend(features)
                    self.features_ready.emit(features)

            if not self.isCanceled() and self._reach_pending:
                self._submit_reach()

            if not self._reach_in_flight and not self._reach_pending:
                self._finish_reach_phase()
        finally:
            reply.deleteLater()

    def _finish_reach_phase(self):
        summary = (
            f"Hydrocron fetch complete for {self.river_name!r}: "
            f"{self._success} reach(es) returned data, {self._empty} returned no features, "
            f"{self._failure} failed, {self._filtered_features} feature(s) dropped by river_name filter; "
            f"collected {len(self.collected_features)} feature(s) "
            f"from {self._reach_total} requested reach(es)."
        )
        if self._first_failure is not None:
            rid, err = self._first_failure
            summary += f" Sample failure on reach {rid}: {err}"
        QgsMessageLog.logMessage(summary, level=Qgis.Info)
        self._loop.quit()

    def _parse_reach_reply(self, reply, rid):
        net_err = reply.error()
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        try:
            body = bytes(reply.readAll()).decode('utf-8', 'replace')
        except Exception:
            body = ''

        try:
            data = json.loads(body) if body else None
        except Exception:
            data = None

        api_msg = _extract_api_error(data)

        if net_err != QNetworkReply.NoError and (status is None or not (200 <= int(status) < 300)):
            if status is None:
                return None, f"request failed: {reply.errorString()}"
            return None, f"HTTP {status}: {api_msg or reply.errorString()}"

        if data is None:
            return None, f"non-JSON response (HTTP {status})"

        api_status = str(data.get('status', '')).strip()
        if api_status and not api_status.startswith('200'):
            return None, f"{api_status}: {api_msg or 'unknown'}"

        try:
            return data['results']['geojson']['features'], None
        except (KeyError, TypeError) as e:
            return None, f"unexpected response shape (missing {e})"

    # ---- shared helpers --------------------------------------------------

    def _filter_by_river(self, features):
        if not self.river_name:
            return features
        expected = self.river_name.strip().lower()
        kept = []
        for f in features:
            rn = (f.get('properties') or {}).get('river_name')
            if rn is None:
                kept.append(f)
                continue
            rn_norm = str(rn).strip().lower()
            if rn_norm in ('', 'no_data') or rn_norm == expected:
                kept.append(f)
        return kept
