import json
from urllib.parse import quote
from qgis.PyQt.QtCore import (
    pyqtSignal, pyqtSlot, QUrl, QUrlQuery, QEventLoop, Qt, QMetaObject,
)
from qgis.PyQt.QtNetwork import (
    QNetworkAccessManager, QNetworkRequest, QNetworkReply,
)
from qgis.core import QgsTask, QgsMessageLog, Qgis
from typing import Optional, Iterable, List, Callable


MAX_CONCURRENT = 8

PAGE_SIZE = 100
PAGE_TIMEOUT_MS = 20000
ITEM_TIMEOUT_MS = 30000

HYDROCRON_URL = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"


def build_request(url, params, timeout_ms):
    qurl = QUrl(url)
    query = QUrlQuery()
    for k, v in params.items():
        query.addQueryItem(str(k), str(v))
    qurl.setQuery(query)
    request = QNetworkRequest(qurl)
    request.setTransferTimeout(timeout_ms)
    return request


def extract_api_error(data):
    if not isinstance(data, dict):
        return None
    msg = data.get('error') or data.get('message')
    if not isinstance(msg, str):
        return None
    # Strip a leading "<digits>: " prefix that just duplicates the HTTP code.
    prefix, sep, rest = msg.partition(': ')
    return rest if sep and prefix.isdigit() else msg


class HydrocronBaseTask(QgsTask):
    """Async Hydrocron fetch task.

    All network I/O is driven by a QNetworkAccessManager + QEventLoop that live
    on the task's worker thread. No nested event loops, no thread pool — so
    cancellation (including QGIS shutdown) unwinds promptly: aborting in-flight
    QNetworkReplies makes the single event loop exit cleanly.

    Subclasses configure the feature type via class attributes:
      FEATURE_TYPE     Hydrocron `feature` query value ('Reach', 'PriorLake', ...)
      ID_FIELD         property key carrying the feature's ID in responses
      NAME_FIELD       property key carrying the parent name (for filtering)
      FTS_URL_TEMPLATE PO.DAAC FTS URL with a `{name}` placeholder for
                       paginating the IDs that belong to a given name.
    """

    # Emitted (queued to the main thread) each time a feature batch arrives,
    # so the UI can stream them into a QGIS layer incrementally.
    features_ready = pyqtSignal(list)

    # Subclass configuration -------------------------------------------------
    FEATURE_TYPE: str = ""
    ID_FIELD: str = ""
    NAME_FIELD: str = ""
    FTS_URL_TEMPLATE: str = ""

    def __init__(
            self,
            description: str,
            name: str,
            fields: List[str],
            start_time: str,
            end_time: str,
            ids: Optional[Iterable] = None,
            callback: Optional[Callable] = None,
            limit: int = -1,
    ):
        super().__init__(description, QgsTask.CanCancel)
        self.name = name
        self.ids = set(ids) if ids else set()
        self.callback = callback
        self.collected_features = []
        self.exception = None
        self.fields = fields or []
        self.start_time = start_time
        self.end_time = end_time
        self.limit = limit

        # Created in run() on the worker thread so they have correct affinity.
        self._nam = None
        self._loop = None

        # Pagination state
        self._page_ids = set()
        self._page_raw_count = 0
        self._page_no = 0

        # Per-item state
        self._item_pending = []
        self._item_in_flight = {}  # QNetworkReply -> id
        self._item_total = 0
        self._item_completed = 0
        self._success = 0
        self._empty = 0
        self._failure = 0
        self._filtered_features = 0
        self._first_failure = None  # (id, err) of first failed item

    # ---- public API ------------------------------------------------------

    def cancel(self):
        # Defer the actual abort to the worker thread (which owns the replies)
        # via a queued slot invocation.
        if self._loop is not None:
            QMetaObject.invokeMethod(self, "handle_cancel", Qt.QueuedConnection)
        super().cancel()

    def run(self):
        QgsMessageLog.logMessage(
            f"[{self.FEATURE_TYPE}] task starting "
            f"(name={self.name!r}, preset_ids={len(self.ids)})",
            level=Qgis.Info,
        )
        try:
            self._nam = QNetworkAccessManager()
            self._loop = QEventLoop()

            if self.ids:
                self.start_item_phase()
            elif self.name:
                self.fetch_page(1)
            else:
                self.exception = f"No {self.ID_FIELD}s or {self.NAME_FIELD} provided."
                QgsMessageLog.logMessage(
                    f"[{self.FEATURE_TYPE}] {self.exception}",
                    level=Qgis.Warning,
                )
                return False

            self._loop.exec_()

            QgsMessageLog.logMessage(
                f"[{self.FEATURE_TYPE}] loop exited "
                f"(cancelled={self.isCanceled()}, "
                f"in_flight={len(self._item_in_flight)}, "
                f"pending={len(self._item_pending)}, "
                f"completed={self._item_completed}/{self._item_total})",
                level=Qgis.Info,
            )

            if self.isCanceled():
                return False
            return True
        except Exception as e:
            self.exception = str(e)
            QgsMessageLog.logMessage(
                f"[{self.FEATURE_TYPE}] run() raised: {e}",
                level=Qgis.Critical,
            )
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
            QgsMessageLog.logMessage(
                f"Hydrocron Task Failed ({self.FEATURE_TYPE}): {msg}",
                level=Qgis.Warning,
            )

    # ---- cancellation ---------------------------------------------------

    @pyqtSlot()
    def handle_cancel(self):
        # Runs on the worker thread (where _loop lives).
        self._item_pending = []
        for reply in list(self._item_in_flight.keys()):
            reply.abort()
        if not self._item_in_flight and self._loop is not None:
            self._loop.quit()

    # ---- pagination phase -----------------------------------------------

    def fetch_page(self, page_no):
        if self.isCanceled():
            self._loop.quit()
            return
        self._page_no = page_no
        self.setProgress(min(page_no * 2, 25))

        url = self.FTS_URL_TEMPLATE.format(name=quote(self.name))
        params = {'page_number': page_no, 'page_size': PAGE_SIZE}
        reply = self._nam.get(build_request(url, params, PAGE_TIMEOUT_MS))
        reply.finished.connect(lambda r=reply: self.on_page_reply(r))

    def on_page_reply(self, reply):
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
                fid = item.get(self.ID_FIELD)
                if fid:
                    self._page_ids.add(fid)

            done = (
                not results
                or len(results) < PAGE_SIZE
                or (0 < self.limit <= len(self._page_ids))
            )
            if done:
                QgsMessageLog.logMessage(
                    f"Fetched {len(self._page_ids)} unique {self.ID_FIELD}s for "
                    f"{self.name!r} (from {self._page_raw_count} raw record(s) "
                    f"across {self._page_no} page(s))",
                    level=Qgis.Info,
                )
                self.ids = self._page_ids
                if not self.ids:
                    self.exception = f"No {self.ID_FIELD}s found."
                    self._loop.quit()
                    return
                self.start_item_phase()
            else:
                self.fetch_page(self._page_no + 1)
        finally:
            reply.deleteLater()

    # ---- per-item phase -------------------------------------------------

    def start_item_phase(self):
        self._item_pending = list(self.ids)
        self._item_total = len(self._item_pending)
        self.setProgress(10)
        for _ in range(min(MAX_CONCURRENT, len(self._item_pending))):
            self.submit_item()
        if not self._item_in_flight:
            self.finish_item_phase()

    def submit_item(self):
        if self.isCanceled() or not self._item_pending:
            return
        fid = self._item_pending.pop()
        params = {
            'fields': ",".join(self.fields),
            'feature': self.FEATURE_TYPE,
            'output': 'geojson',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'feature_id': fid,
        }
        reply = self._nam.get(build_request(HYDROCRON_URL, params, ITEM_TIMEOUT_MS))
        self._item_in_flight[reply] = fid
        reply.finished.connect(lambda r=reply, f=fid: self.on_item_reply(r, f))

    def on_item_reply(self, reply, fid):
        try:
            try:
                self.handle_item_reply(reply, fid)
            except Exception as e:
                # Don't let a buggy callback strand the task — log and continue
                # so finish_item_phase still fires when the queue empties.
                self._failure += 1
                if self._first_failure is None:
                    self._first_failure = (fid, f"internal error: {e}")
                QgsMessageLog.logMessage(
                    f"Internal error handling reply for {self.ID_FIELD}={fid}: {e}",
                    level=Qgis.Warning,
                )
                if not self.isCanceled() and self._item_pending:
                    self.submit_item()
                if not self._item_in_flight and not self._item_pending:
                    self.finish_item_phase()
        finally:
            reply.deleteLater()

    def handle_item_reply(self, reply, fid):
        self._item_in_flight.pop(reply, None)

        if reply.error() == QNetworkReply.OperationCanceledError or self.isCanceled():
            if self.isCanceled() and not self._item_in_flight:
                self._loop.quit()
            return

        self._item_completed += 1
        self.setProgress(10 + int(self._item_completed / self._item_total * 90))

        features, err = self.parse_item_reply(reply)
        if err is not None:
            self._failure += 1
            if self._first_failure is None:
                self._first_failure = (fid, err)
        elif not features:
            self._empty += 1
        else:
            raw = len(features)
            features = self.filter_by_name(features)
            self._filtered_features += raw - len(features)
            if not features:
                self._empty += 1
            else:
                self._success += 1
                self.collected_features.extend(features)
                self.features_ready.emit(features)

        if not self.isCanceled() and self._item_pending:
            self.submit_item()

        if not self._item_in_flight and not self._item_pending:
            self.finish_item_phase()

    def finish_item_phase(self):
        summary = (
            f"Hydrocron fetch complete for {self.name!r} ({self.FEATURE_TYPE}): "
            f"{self._success} {self.ID_FIELD}(s) returned data, "
            f"{self._empty} returned no features, {self._failure} failed, "
            f"{self._filtered_features} feature(s) dropped by {self.NAME_FIELD} filter; "
            f"collected {len(self.collected_features)} feature(s) "
            f"from {self._item_total} requested {self.ID_FIELD}(s)."
        )
        if self._first_failure is not None:
            fid, err = self._first_failure
            summary += f" Sample failure on {self.ID_FIELD}={fid}: {err}"
        QgsMessageLog.logMessage(summary, level=Qgis.Info)
        self._loop.quit()

    def parse_item_reply(self, reply):
        net_err = reply.error()
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        url = reply.url().toString()

        try:
            body = bytes(reply.readAll()).decode('utf-8', 'replace')
        except Exception:
            body = ''

        try:
            data = json.loads(body) if body else None
        except Exception:
            data = None

        api_msg = extract_api_error(data)

        if net_err != QNetworkReply.NoError and (status is None or not (200 <= int(status) < 300)):
            if status is None:
                return None, f"request failed: {reply.errorString()} | URL: {url}"
            return None, f"HTTP {status}: {api_msg or reply.errorString()} | URL: {url}"

        if data is None:
            return None, f"non-JSON response (HTTP {status}) | URL: {url}"

        api_status = str(data.get('status', '')).strip()
        if api_status and not api_status.startswith('200'):
            return None, f"{api_status}: {api_msg or 'unknown'} | URL: {url}"

        try:
            return data['results']['geojson']['features'], None
        except (KeyError, TypeError) as e:
            return None, f"unexpected response shape (missing {e}) | URL: {url}"

    # ---- shared helpers --------------------------------------------------

    def filter_by_name(self, features):
        """Drop features whose NAME_FIELD doesn't match self.name. Features
        with a missing / 'no_data' name are accepted."""
        if not self.name:
            return features
        expected = self.name.strip().lower()
        kept = []
        for f in features:
            nm = (f.get('properties') or {}).get(self.NAME_FIELD)
            if nm is None:
                kept.append(f)
                continue
            nm_norm = str(nm).strip().lower()
            if nm_norm in ('', 'no_data') or nm_norm == expected:
                kept.append(f)
        return kept


class HydrocronReachTask(HydrocronBaseTask):
    """Reach (river segment) timeseries from Hydrocron."""

    FEATURE_TYPE = 'Reach'
    ID_FIELD = 'reach_id'
    NAME_FIELD = 'river_name'
    FTS_URL_TEMPLATE = "https://fts.podaac.earthdata.nasa.gov/v1/rivers/{name}"

    def __init__(
            self,
            description: str,
            river_name: str,
            fields: List[str],
            start_time: str,
            end_time: str,
            reach_ids: Optional[Iterable] = None,
            callback: Optional[Callable] = None,
            limit: int = -1,
            **_,
    ):
        super().__init__(
            description=description,
            name=river_name,
            fields=fields,
            start_time=start_time,
            end_time=end_time,
            ids=reach_ids,
            callback=callback,
            limit=limit,
        )


class HydrocronLakeTask(HydrocronBaseTask):
    """PriorLake (PLD lake) timeseries from Hydrocron.

    Lake ID discovery uses a separate single-shot endpoint
    (`https://lakes.swot-lake.workers.dev/?q=<name>`) instead of PO.DAAC FTS,
    so the pagination phase is overridden to do one request.
    """

    FEATURE_TYPE = 'PriorLake'
    ID_FIELD = 'lake_id'
    NAME_FIELD = 'lake_name'
    FTS_URL_TEMPLATE = ""  # unused; fetch_page is overridden

    LAKES_LOOKUP_URL = "https://lakes.swot-lake.workers.dev/"

    def __init__(
            self,
            description: str,
            lake_name: str,
            fields: List[str],
            start_time: str,
            end_time: str,
            lake_ids: Optional[Iterable] = None,
            callback: Optional[Callable] = None,
            limit: int = -1,
            **_,
    ):
        super().__init__(
            description=description,
            name=lake_name,
            fields=fields,
            start_time=start_time,
            end_time=end_time,
            ids=lake_ids,
            callback=callback,
            limit=limit,
        )

    def fetch_page(self, page_no):
        # The lakes worker returns all matches in one response — no pagination.
        if self.isCanceled():
            self._loop.quit()
            return
        self._page_no = page_no
        self.setProgress(15)

        params = {'q': self.name}
        reply = self._nam.get(
            build_request(self.LAKES_LOOKUP_URL, params, PAGE_TIMEOUT_MS)
        )
        reply.finished.connect(lambda r=reply: self.on_page_reply(r))

    def on_page_reply(self, reply):
        try:
            if self.isCanceled() or reply.error() == QNetworkReply.OperationCanceledError:
                self._loop.quit()
                return

            if reply.error() != QNetworkReply.NoError:
                self.exception = (
                    f"Lakes lookup failed for {self.name!r}: {reply.errorString()}"
                )
                self._loop.quit()
                return

            try:
                data = json.loads(bytes(reply.readAll()).decode('utf-8', 'replace'))
            except Exception as e:
                self.exception = f"Lakes lookup failed for {self.name!r}: {e}"
                self._loop.quit()
                return

            items = data.get('results') if isinstance(data, dict) else (data or [])
            self._page_raw_count = len(items)

            for item in items:
                if 0 < self.limit <= len(self._page_ids):
                    break
                if not isinstance(item, dict):
                    continue
                fid = item.get(self.ID_FIELD)
                if fid is None:
                    continue
                # Some entries are merged observations with ';'-joined PLD IDs;
                # split so each is queried as its own Hydrocron feature_id.
                for part in str(fid).split(';'):
                    part = part.strip()
                    if part:
                        self._page_ids.add(part)

            QgsMessageLog.logMessage(
                f"Fetched {len(self._page_ids)} unique {self.ID_FIELD}s for "
                f"{self.name!r} (from {self._page_raw_count} raw record(s))",
                level=Qgis.Info,
            )
            self.ids = self._page_ids
            if not self.ids:
                self.exception = f"No lakes found matching {self.name!r}."
                self._loop.quit()
                return
            self.start_item_phase()
        finally:
            reply.deleteLater()

    def filter_by_name(self, features):
        # The lakes worker matches names by substring (q=caspian → CASPIAN LAKE,
        # CASPIAN SEA, …), so an exact match here would drop everything.
        # Use substring containment instead. Features with missing / 'no_data'
        # names are kept as before.
        if not self.name:
            return features
        needle = self.name.strip().lower()
        kept = []
        for f in features:
            nm = (f.get('properties') or {}).get(self.NAME_FIELD)
            if nm is None:
                kept.append(f)
                continue
            nm_norm = str(nm).strip().lower()
            if nm_norm in ('', 'no_data') or needle in nm_norm:
                kept.append(f)
        return kept
