"""Static backstop: experiment code must never terminate another process."""
from pathlib import Path

from kill_pattern_scanner import scan_python_path, scan_shell_path

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
        paths = list((ROOT / top).rglob("*.py"))
        paths.extend((ROOT / top).rglob("*.sh"))
        paths.extend((ROOT / top).rglob("*.bash"))
        for path in paths:
            if "archive" in path.parts:
                continue
            scanner = scan_python_path if path.suffix == ".py" else scan_shell_path
            for hit in scanner(path, display_path=path.relative_to(ROOT)):
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


def test_import_alias_watchdogs_are_caught_but_aliased_child_cleanup_passes():
    fixture = ROOT / "tests" / "fixtures" / "watchdog_alias_patterns.py"
    hits = scan_python_path(fixture, display_path=fixture.relative_to(ROOT))
    for scope in (
        "watchdog",
        "watchdog_module_alias",
        "watchdog_kill_alias",
        "watchdog_killpg_alias",
        "watchdog_pthread_alias",
        "watchdog_popen_alias",
    ):
        assert any(_exception_key(hit)[1] == scope for hit in hits), hits
    assert not any(
        _exception_key(hit)[1] == "cleanup_aliased_popen_child" for hit in hits
    ), hits


def test_shell_watchdog_and_python_shell_heredoc_are_caught_but_own_pid_passes():
    shell_fixture = ROOT / "tests" / "fixtures" / "watchdog_patterns.sh"
    shell_hits = scan_shell_path(
        shell_fixture, display_path=shell_fixture.relative_to(ROOT)
    )
    assert any(_exception_key(hit)[1] == "shell_watchdog" for hit in shell_hits), (
        shell_hits
    )
    for scope in ("cleanup_own_child", "cleanup_derived_child"):
        assert not any(
            _exception_key(hit)[1] == scope for hit in shell_hits
        ), shell_hits

    python_fixture = ROOT / "tests" / "fixtures" / "watchdog_shell_heredoc.py"
    python_hits = scan_python_path(
        python_fixture, display_path=python_fixture.relative_to(ROOT)
    )
    assert any(
        _exception_key(hit)[1] == "shell_heredoc_watchdog" for hit in python_hits
    ), python_hits
    assert not any(
        _exception_key(hit)[1] == "shell_heredoc_own_child" for hit in python_hits
    ), python_hits
