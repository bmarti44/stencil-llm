#!/usr/bin/env python3
"""Coder scope baseline (NUL-safe; ends the shell whitespace-parsing class).

pre  <manifest>            : snapshot dirty state (status line, kind, digest) as JSON
post <manifest>            : print NUL-separated coder-changed paths (union of
                             currently-dirty and baseline paths; a path is
                             baseline only if status line AND record both match)
"""
import hashlib, json, os, stat, subprocess, sys

def root():
    return subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                          text=True, check=True).stdout.strip()

def status_map(r):
    raw = subprocess.run(["git", "-C", r, "status", "--porcelain=v2", "-z",
                          "--untracked-files=all"], capture_output=True, check=True).stdout
    out = {}
    fields = [f for f in raw.split(b"\x00")]
    i = 0
    while i < len(fields):
        rec = fields[i]
        i += 1
        if not rec:
            continue
        t = rec.decode("utf-8", "surrogateescape")
        if t[0] in "12u?":
            if t[0] == "1":
                path = t.split(" ", 8)[-1]
            elif t[0] == "2":
                # rename/copy: field 9 is the DESTINATION; the SOURCE path is
                # the next NUL field. Record BOTH — discarding the source let
                # a rename hide an out-of-scope original (round-24 exploit).
                path = t.split(" ", 9)[-1]
                if i < len(fields) and fields[i]:
                    src = fields[i].decode("utf-8", "surrogateescape")
                    out[src] = "RENAMED-FROM " + t[:2]
                    i += 1
            elif t[0] == "u":
                path = t.split(" ", 10)[-1]
            else:
                path = t[2:]
            out[path] = t[: len(t) - len(path)].strip()
    return out

def record(r, p):
    fp = os.path.join(r, p)
    try:
        st = os.lstat(fp)
    except OSError:
        return "GONE"
    if stat.S_ISLNK(st.st_mode):
        return "L:" + hashlib.sha256(os.readlink(fp).encode("utf-8", "surrogateescape")).hexdigest()
    if stat.S_ISREG(st.st_mode):
        x = "x" if st.st_mode & stat.S_IXUSR else "-"
        return f"F{x}:" + hashlib.sha256(open(fp, "rb").read()).hexdigest()
    return "OTHER:" + oct(st.st_mode)

def main():
    mode, manifest = sys.argv[1], sys.argv[2]
    r = root()
    if mode == "pre":
        sm = status_map(r)
        json.dump({p: {"stat": s, "rec": record(r, p)} for p, s in sm.items()},
                  open(manifest, "w"))
        return 0
    base = json.load(open(manifest))
    cur = status_map(r)
    changed = []
    for p in sorted(set(base) | set(cur)):
        b = base.get(p)
        if b and p in cur and cur[p] == b["stat"] and record(r, p) == b["rec"]:
            continue  # true baseline: untouched by the coder
        changed.append(p)
    for c in changed:
        # Each path is NUL-TERMINATED (not merely separated): read -d '' in
        # the consumer requires the terminator or it drops the final path.
        sys.stdout.buffer.write(c.encode("utf-8", "surrogateescape") + b"\x00")
    return 0

if __name__ == "__main__":
    sys.exit(main())
