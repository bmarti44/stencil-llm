"""Synthetic scanner fixtures; this module is inspected, never executed."""

import os
import signal
import subprocess
import time


def is_still_running(pid):
    return bool(pid)


def watchdog_other_pid(pid):
    while is_still_running(pid):
        time.sleep(1)
    subprocess.run(["kill", str(pid)], check=False)


def cleanup_own_child():
    process = subprocess.Popen(["worker"])
    process.terminate()


def kill_literal_pid():
    os.kill(123, signal.SIGTERM)


def kill_pid_parsed_from_nvidia_smi():
    output = subprocess.check_output(["nvidia-smi"])
    pids = [int(value) for value in output.split()]
    for pid in pids:
        os.kill(pid, signal.SIGTERM)


def cleanup_forked_child():
    child_pid = os.fork()
    os.kill(child_pid, signal.SIGTERM)
