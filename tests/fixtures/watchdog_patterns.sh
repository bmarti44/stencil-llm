#!/usr/bin/env bash

shell_watchdog() {
    while process_is_alive "$1"; do
        sleep 1
    done
    kill "$1"
}

cleanup_own_child() {
    worker &
    kill $!
}

cleanup_derived_child() {
    worker &
    child_pid=$!
    kill "$child_pid"
}
