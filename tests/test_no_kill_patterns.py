"""Static backstop: experiment code must never terminate another process."""
from pathlib import Path

from kill_pattern_scanner import scan_python_path

ROOT = Path(__file__).resolve().parent.parent
AUDITED_OWN_CHILD_EXCEPTIONS = {
    # run_matrix.launch creates the Popen at line 436 and passes only that object
    # through this cleanup chain; no PID is discovered or supplied externally.
    ("scripts/run_matrix.py", "_stop_process"),
    ("scripts/run_matrix.py", "_watch_process"),
    ("scripts/run_matrix.py", "launch"),
}


def _exception_key(hit):
    path, _, scope = hit.rsplit(":", 2)
    return path, scope


def test_no_kill_or_cross_process_watchdog_patterns():
    hits = []
    for top in ("scripts", "src", "tools"):
        for path in (ROOT / top).rglob("*.py"):
            if "archive" in path.parts:
                continue
            for hit in scan_python_path(path, display_path=path.relative_to(ROOT)):
                if _exception_key(hit) not in AUDITED_OWN_CHILD_EXCEPTIONS:
                    hits.append(hit)
    assert not hits, f"process-termination patterns are forbidden: {hits}"


def test_multiline_watchdog_fixture_is_caught_but_own_child_cleanup_passes():
    fixture = ROOT / "tests" / "fixtures" / "watchdog_patterns.py"
    hits = scan_python_path(fixture, display_path=fixture.relative_to(ROOT))
    assert any("watchdog_other_pid" in hit for hit in hits), hits
    assert any("kill_literal_pid" in hit for hit in hits), hits
    assert any("kill_pid_parsed_from_nvidia_smi" in hit for hit in hits), hits
    assert not any("cleanup_own_child" in hit for hit in hits), hits
    assert not any("cleanup_forked_child" in hit for hit in hits), hits
