"""SLAB CPython worker. No imports, execution, or resource changes at import time."""


def main():
    import builtins
    import ctypes
    import errno
    import json
    import os
    import resource
    import sys
    import threading

    payload = json.load(sys.stdin)
    # Self-exit is not a signal; the parent never kills a timed-out worker.
    threading.Timer(2.0, lambda: os._exit(124)).start()
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (8, 8))
    lib = ctypes.CDLL("libseccomp.so.2")
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    lib.seccomp_attr_set.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7FFF0000)  # ALLOW, with explicit kernel-enforced denials.
    if not ctx:
        os._exit(125)
    # SCMP_FLTATR_CTL_TSYNC: apply the filter to the existing watchdog too.
    if lib.seccomp_attr_set(ctx, 4, 1):
        os._exit(125)
    denied = (
        "socket socketpair connect bind listen accept accept4 "
        "sendto sendmsg recvfrom recvmsg "
        "open openat openat2 creat unlink unlinkat rename renameat "
        "renameat2 mkdir mkdirat "
        "link linkat symlink symlinkat mount umount2 pivot_root chroot "
        "clone clone3 fork vfork execve execveat kill tkill tgkill pidfd_send_signal "
        "ptrace process_vm_readv process_vm_writev io_uring_setup bpf "
        "chmod fchmod fchmodat fchmodat2 chown fchown lchown fchownat "
        "truncate ftruncate utime utimes futimesat utimensat rmdir mknod mknodat "
        "open_by_handle_at name_to_handle_at pidfd_open pidfd_getfd"
    )
    for name in denied.split():
        number = lib.seccomp_syscall_resolve_name(name.encode())
        if number >= 0 and lib.seccomp_rule_add(ctx, 0x50000 | errno.EPERM, number, 0):
            os._exit(125)
    if lib.seccomp_load(ctx):
        os._exit(125)
    lib.seccomp_release(ctx)
    # Python is real CPython, with ordinary computational builtins. IO/import are
    # not part of the task. Seccomp remains effective even if Python is escaped.
    blocked = {
        "__import__",
        "open",
        "input",
        "print",
        "breakpoint",
        "help",
        "exit",
        "quit",
        "copyright",
        "credits",
        "license",
    }
    env = {
        "__name__": "slab_program",
        "__builtins__": {
            name: getattr(builtins, name)
            for name in dir(builtins)
            if name not in blocked
        },
    }
    try:
        exec(compile(payload["code"], "<slab>", "exec"), env)
        values = [env[name](value) for name, value in payload["cases"]]
        output = json.dumps({"values": values}, allow_nan=False).encode()
        if len(output) > 65536:
            raise ValueError("result bound")
    except BaseException as exc:
        output = json.dumps({"error": type(exc).__name__}).encode()
    os.write(1, output)
    os._exit(0)


if __name__ == "__main__":
    main()
