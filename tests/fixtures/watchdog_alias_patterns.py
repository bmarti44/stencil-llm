# ruff: noqa: E402, F821
"""Synthetic import-alias fixtures; this module is inspected, never executed."""

from os import kill
from signal import SIGTERM


def watchdog(pid):
    while alive(pid):
        kill(pid, SIGTERM)


import os as o
from os import kill as k
from os import killpg as kg
from signal import pthread_kill
from subprocess import Popen as P


def watchdog_module_alias(pid):
    o.kill(pid, SIGTERM)


def watchdog_kill_alias(pid):
    k(pid, SIGTERM)


def watchdog_killpg_alias(pid):
    kg(pid, SIGTERM)


def watchdog_pthread_alias(pid):
    pthread_kill(pid, SIGTERM)


def watchdog_popen_alias(pid):
    P(["kill", str(pid)])


def cleanup_aliased_popen_child():
    process = P(["worker"])
    process.terminate()
