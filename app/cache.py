"""A tiny thread-safe LRU cache so identical reports don't trigger repeat LLM calls."""
import hashlib
from collections import OrderedDict
from threading import Lock

from app.models import SummaryResponse


class ResponseCache:
    def __init__(self, max_size: int = 128) -> None:
        self._max_size = max_size
        self._data: OrderedDict[str, SummaryResponse] = OrderedDict()
        self._lock = Lock()

    @staticmethod
    def make_key(report_xml: str, max_failures: int) -> str:
        raw = f"{max_failures}:{report_xml}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, key: str) -> SummaryResponse | None:
        with self._lock:
            value = self._data.get(key)
            if value is not None:
                self._data.move_to_end(key)  # mark as recently used
            return value

    def set(self, key: str, value: SummaryResponse) -> None:
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self._max_size:
                self._data.popitem(last=False)  # evict least recently used
