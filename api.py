import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsTask, QgsMessageLog, Qgis
from typing import Optional, Iterable, List, Callable


MAX_WORKERS = 8


class HydrocronMasterTask(QgsTask):
    # Emitted (on the main thread, via Qt queued connection) each time a reach's
    # features come back, so the UI can stream them into a layer incrementally.
    features_ready = pyqtSignal(list)

    def __init__(
            self,
            description: str,
            river_name: str,
            fields: List[str],
            start_time: str,
            end_time: str,
            reach_ids: Optional[Iterable]=None,
            callback: Optional[Callable]=None,
            **kwargs
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

    def run(self):
        try:
            if not self.reach_ids and self.river_name:
                self.setProgress(5)  # Visual feedback
                self.reach_ids = self.fetch_paginated_ids()
            if not self.reach_ids:
                self.exception = "No reach IDs found or provided."
                return False

            url = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"
            base_params = {
                'fields': ",".join(self.fields),
                'feature': 'Reach',
                'output': 'geojson',
                'start_time': self.start_time,
                'end_time': self.end_time,
            }
            total = len(self.reach_ids)
            workers = min(MAX_WORKERS, total)

            success = 0
            empty = 0
            failure = 0
            filtered_features = 0

            pool = ThreadPoolExecutor(max_workers=workers)
            try:
                futures = {
                    pool.submit(self._fetch_reach, url, base_params, rid): rid
                    for rid in self.reach_ids
                }
                completed = 0
                for future in as_completed(futures):
                    if self.isCanceled():
                        for f in futures:
                            f.cancel()
                        return False

                    rid = futures[future]
                    features, err = future.result()
                    completed += 1
                    self.setProgress(10 + (completed / total * 90))

                    if err is not None:
                        failure += 1
                        QgsMessageLog.logMessage(
                            f"NASA API Error on reach {rid}: {err}",
                            level=Qgis.Warning,
                        )
                        continue
                    if not features:
                        empty += 1
                        continue

                    raw_count = len(features)
                    features = self._filter_by_river(features)
                    filtered_features += raw_count - len(features)
                    if not features:
                        empty += 1
                        continue
                    success += 1

                    self.collected_features.extend(features)
                    self.features_ready.emit(features)
            finally:
                pool.shutdown(wait=False)

            QgsMessageLog.logMessage(
                f"Hydrocron fetch complete for {self.river_name!r}: "
                f"{success} reach(es) returned data, {empty} returned no features, "
                f"{failure} failed, {filtered_features} feature(s) dropped by river_name filter; "
                f"collected {len(self.collected_features)} feature(s) "
                f"from {total} requested reach(es).",
                level=Qgis.Info,
            )
            return True
        except Exception as e:
            self.exception = str(e)
            return False

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

    @staticmethod
    def _fetch_reach(url, base_params, rid):
        params = dict(base_params, feature_id=rid)
        try:
            resp = requests.get(url, params=params, timeout=30)
        except Exception as e:
            return None, f"request failed: {e}"

        try:
            data = resp.json()
        except Exception:
            data = None

        api_msg = HydrocronMasterTask._extract_api_error(data)

        if not resp.ok:
            return None, f"HTTP {resp.status_code}: {api_msg or resp.reason}"

        if data is None:
            return None, f"non-JSON response (HTTP {resp.status_code})"

        status = str(data.get('status', '')).strip()
        if status and not status.startswith('200'):
            return None, f"{status}: {api_msg or 'unknown'}"

        try:
            return data['results']['geojson']['features'], None
        except (KeyError, TypeError) as e:
            return None, f"unexpected response shape (missing {e})"

    @staticmethod
    def _extract_api_error(data):
        if not isinstance(data, dict):
            return None
        msg = data.get('error') or data.get('message')
        if not isinstance(msg, str):
            return None
        # Strip a leading "<digits>: " prefix that just duplicates the HTTP code.
        prefix, sep, rest = msg.partition(': ')
        return rest if sep and prefix.isdigit() else msg

    def fetch_paginated_ids(self):
        base_url = f"https://fts.podaac.earthdata.nasa.gov/v1/rivers/{self.river_name}"
        ids = set()
        raw_count = 0
        page = 1
        max_page_size = 100

        while True:
            if self.isCanceled():
                return set()

            self.setProgress(min(page * 2, 25))

            params = {'page_number': page, 'page_size': max_page_size}

            try:
                response = requests.get(base_url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                raise Exception(f"NASA API Error on page {page}: {str(e)}")

            results = data.get('results', [])
            if not results:
                break

            raw_count += len(results)
            for item in results:
                if 0 < self.limit <= len(ids):
                    break
                rid = item.get('reach_id')
                if rid:
                    ids.add(rid)

            if len(results) < max_page_size:
                break
            if 0 < self.limit <= len(ids):
                break
            page += 1

        QgsMessageLog.logMessage(
            f"Fetched {len(ids)} unique reach IDs for {self.river_name!r} "
            f"(from {raw_count} raw record(s) across {page} page(s))",
            level=Qgis.Info,
        )
        return ids

    def finished(self, result):
        if result:
            self.callback(self.collected_features)
        else:
            msg = self.exception or "User cancelled"
            QgsMessageLog.logMessage(f"Hydrocron Task Failed: {msg}", level=Qgis.Warning)