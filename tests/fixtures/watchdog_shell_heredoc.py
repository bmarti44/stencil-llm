"""Synthetic Python-embedded shell fixtures; this module is never executed."""

SHELL = r"""
shell_heredoc_watchdog() {
    kill "$1"
}

shell_heredoc_own_child() {
    worker &
    kill $!
}
"""
