"""Utility for dealing with sub processes."""

import time

def kill_child_processes(child_processes, timeout=2):
    """Kill all subprocesses if they timeout."""
    start_time = time.time()

    has_pending = True
    while has_pending:
        has_pending = False
        for process in child_processes:
            try:
                if process.poll() is None:
                    has_pending = True
                    process.terminate()
            except OSError:
                # Ignore the error.  The OSError doesn't seem to be documented(?)
                pass

        if not has_pending:
            return

        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            for process in child_processes:
                if process.poll() is None:
                    process.kill()
            return
