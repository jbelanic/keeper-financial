from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TypeVar

T = TypeVar("T")


class ProcessLocalDocumentScanGate:
    """Bound expensive validation/scanning within one API worker process."""

    def __init__(self, maximum_concurrent: int) -> None:
        if maximum_concurrent < 1:
            raise ValueError("maximum_concurrent must be positive")
        self.maximum_concurrent = maximum_concurrent
        self._semaphore = threading.BoundedSemaphore(maximum_concurrent)

    @contextmanager
    def slot(self) -> Iterator[None]:
        self._semaphore.acquire()
        try:
            yield
        finally:
            self._semaphore.release()

    def run(self, operation: Callable[[], T]) -> T:
        with self.slot():
            return operation()
