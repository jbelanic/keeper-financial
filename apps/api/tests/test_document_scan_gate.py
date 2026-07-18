from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from keeper_api.services.document_scan_gate import ProcessLocalDocumentScanGate


def test_process_local_document_scan_gate_bounds_concurrent_expensive_work() -> None:
    gate = ProcessLocalDocumentScanGate(maximum_concurrent=2)
    release = threading.Event()
    two_started = threading.Event()
    lock = threading.Lock()
    active = 0
    peak = 0

    def work() -> None:
        nonlocal active, peak
        with gate.slot():
            with lock:
                active += 1
                peak = max(peak, active)
                if active == 2:
                    two_started.set()
            assert release.wait(timeout=5)
            with lock:
                active -= 1

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(work) for _ in range(6)]
        assert two_started.wait(timeout=5)
        assert peak == 2
        release.set()
        for future in futures:
            future.result(timeout=5)

    assert peak == 2
