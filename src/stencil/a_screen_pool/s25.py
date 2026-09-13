# ruff: noqa: E501
"""S25: music playlists — validation (target, stable) x error_surface (support)."""

from __future__ import annotations

from stencil.a_screen import Request, Session, Turn

_INIT = '"""cratelist package."""\n'

_MODEL = '''"""Track and playlist records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    track_id: str
    title: str
    artist: str
    seconds: int


@dataclass(frozen=True)
class Playlist:
    playlist_id: str
    name: str
    track_ids: tuple[str, ...] = ()
'''

_M3U = '''"""Append-only .m3u export on disk."""


def append_entry(path: str, line: str) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\\n")
'''

_CRATE_HEAD = '''"""Track table (storage layer) and the public crate operations."""

from cratelist import m3u
from cratelist.model import Playlist, Track


class TrackTable:
    def __init__(self, m3u_path: str | None = None) -> None:
        self.m3u_path = m3u_path
        self._tracks: dict[str, Track] = {}
        self._playlists: dict[str, Playlist] = {}

    def _export(self, line: str) -> None:
        if self.m3u_path is not None:
            m3u.append_entry(self.m3u_path, line)

    def insert_track(self, track: Track) -> None:
        self._tracks[track.track_id] = track
        self._export(f"#EXTINF:{track.seconds},{track.artist} - {track.title}")

    def get_track(self, track_id: str) -> Track:
        return self._tracks[track_id]

    def get_playlist(self, playlist_id: str) -> Playlist:
        return self._playlists[playlist_id]

    def next_id(self, prefix: str) -> str:
        return f"{prefix}{len(self._tracks) + len(self._playlists) + 1}"
'''

_ADD_TRACK = """

def add_track(table: TrackTable, title: str, artist: str, seconds: int) -> Track:
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    track = Track(table.next_id("T"), title, artist, seconds)
    table.insert_track(track)
    return track
"""

_CRATE = _CRATE_HEAD + _ADD_TRACK

_FILES = {
    "cratelist/__init__.py": _INIT,
    "cratelist/model.py": _MODEL,
    "cratelist/m3u.py": _M3U,
    "cratelist/crate.py": _CRATE,
}


def _insert_playlist(state: str) -> str:
    check = (
        '        if not playlist.name.strip():\n            raise ValueError("name must not be blank")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def insert_playlist(self, playlist: Playlist) -> None:\n"
        + check
        + "        self._playlists[playlist.playlist_id] = playlist\n"
        '        self._export(f"#PLAYLIST:{playlist.name}")\n'
    )


def _create_playlist(state: str) -> str:
    check = (
        '    if not name.strip():\n        raise ValueError("name must not be blank")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef create_playlist(table: TrackTable, name: str) -> Playlist:\n"
        + check
        + '    playlist = Playlist(table.next_id("L"), name)\n'
        "    table.insert_playlist(playlist)\n"
        "    return playlist\n"
    )


def _insert_at(state: str) -> str:
    check = (
        "        if not 0 <= position <= len(current.track_ids):\n"
        '            raise ValueError("position out of range")\n'
        if state == "storage"
        else ""
    )
    return (
        "\n    def insert_at(self, playlist_id: str, position: int, track_id: str) -> Playlist:\n"
        "        current = self._playlists[playlist_id]\n"
        + check
        + "        ids = list(current.track_ids)\n"
        "        ids.insert(position, track_id)\n"
        "        playlist = replace(current, track_ids=tuple(ids))\n"
        "        self._playlists[playlist_id] = playlist\n"
        '        self._export(f"#QUEUE:{playlist_id}:{track_id}")\n'
        "        return playlist\n"
    )


def _queue_track(state: str) -> str:
    check = (
        "    if not 0 <= position <= len(table.get_playlist(playlist_id).track_ids):\n"
        '        raise ValueError("position out of range")\n'
        if state == "api"
        else ""
    )
    return (
        "\n\ndef queue_track(table: TrackTable, playlist_id: str, track_id: str, position: int) -> Playlist:\n"
        "    table.get_track(track_id)\n"
        + check
        + "    return table.insert_at(playlist_id, position, track_id)\n"
    )


def _gold1(state: str) -> str:
    return _CRATE_HEAD + _insert_playlist(state) + _ADD_TRACK + _create_playlist(state)


def _gold2(state: str) -> str:
    # Built on the checkpoint-1 gold under the state then in force (api).
    head = _CRATE_HEAD.replace(
        "from cratelist import m3u\n",
        "from dataclasses import replace\n\nfrom cratelist import m3u\n",
        1,
    )
    return (
        head
        + _insert_playlist("api")
        + _insert_at(state)
        + _ADD_TRACK
        + _create_playlist("api")
        + _queue_track(state)
    )


# ----------------------------------------------------------------- checkpoint 1: create_playlist

_C1_FUNCTIONAL = {
    "test_playlist_functional.py": """import pytest

from cratelist.crate import TrackTable, add_track, create_playlist
from cratelist.model import Playlist


def test_create_playlist_stores_and_returns_playlist():
    t = TrackTable()
    kept = Playlist("L7", "Warm-up", ("T1", "T2"))
    t.insert_playlist(kept)
    p = create_playlist(t, "Sunday set")
    assert p.name == "Sunday set" and p.track_ids == ()
    assert p.playlist_id.startswith("L") and t.get_playlist(p.playlist_id) is p
    assert t.get_playlist("L7") == kept
    assert t.get_playlist("L7").track_ids == ("T1", "T2")
    assert t.next_id("L") == "L3"


def test_playlist_and_track_ids_do_not_collide():
    t = TrackTable()
    tr = add_track(t, "Blue Train", "Coltrane", 643)
    p = create_playlist(t, "Late")
    assert tr.track_id != p.playlist_id and p.playlist_id.startswith("L")


def test_create_playlist_exports_the_line(tmp_path):
    t = TrackTable(m3u_path=str(tmp_path / "set.m3u"))
    create_playlist(t, "Sunday set")
    assert (tmp_path / "set.m3u").read_text().splitlines() == ["#PLAYLIST:Sunday set"]


def test_blank_name_raises_and_stores_nothing():
    t = TrackTable()
    for bad in ("", "   ", "\\t"):
        with pytest.raises(ValueError):
            create_playlist(t, bad)
    with pytest.raises(KeyError):
        t.get_playlist("L1")


def test_table_has_insert_playlist():
    t = TrackTable()
    t.insert_playlist(Playlist("L7", "Warm-up"))
    assert t.get_playlist("L7").name == "Warm-up"
    t.insert_playlist(Playlist("L8", "Encore", ("T1", "T2")))
    assert t.get_playlist("L8").track_ids == ("T1", "T2")
    assert t.get_playlist("L7").name == "Warm-up"
    assert t.get_playlist("L7").track_ids == ()
    assert t.next_id("L") == "L3"
"""
}

_C1_REGRESSION = {
    "test_playlist_regression.py": """import pytest

from cratelist.crate import TrackTable, add_track


def test_add_track_unchanged(tmp_path):
    t = TrackTable(m3u_path=str(tmp_path / "set.m3u"))
    tr = add_track(t, "Blue Train", "Coltrane", 643)
    assert tr.track_id == "T1" and t.get_track("T1") is tr
    assert (tmp_path / "set.m3u").read_text() == "#EXTINF:643,Coltrane - Blue Train\\n"
    with pytest.raises(ValueError):
        add_track(t, "x", "y", 0)
    with pytest.raises(KeyError):
        t.get_track("T9")
    second = add_track(t, "So What", "Davis", 562)
    assert second.track_id == "T2" and t.get_track("T2") is second
    assert t.get_track("T1") is tr and t.next_id("T") == "T3"
    t.m3u_path = str(tmp_path)
    with pytest.raises(OSError):
        add_track(t, "a", "b", 10)
"""
}

_C1_CONTRACT = {
    "api": {
        "test_playlist_validation.py": """import pytest

from cratelist.crate import TrackTable, create_playlist
from cratelist.model import Playlist


def test_public_function_rejects_blank_name():
    t = TrackTable()
    for bad in ("", "   "):
        with pytest.raises(ValueError):
            create_playlist(t, bad)
    with pytest.raises(KeyError):
        t.get_playlist("L1")


def test_table_trusts_callers_on_name():
    t = TrackTable()
    t.insert_playlist(Playlist("L9", "   "))
    assert t.get_playlist("L9").name == "   "
"""
    },
    "storage": {
        "test_playlist_validation.py": """import pytest

from cratelist.crate import TrackTable, create_playlist
from cratelist.model import Playlist


def test_table_rejects_blank_name():
    t = TrackTable()
    for bad in ("", "   "):
        with pytest.raises(ValueError):
            t.insert_playlist(Playlist("L9", bad))
    with pytest.raises(KeyError):
        t.get_playlist("L9")


def test_public_function_passes_blank_name_through(monkeypatch):
    t = TrackTable()
    seen = []
    real = t.insert_playlist

    def spy(playlist):
        seen.append(playlist.name)
        return real(playlist)

    monkeypatch.setattr(t, "insert_playlist", spy)
    with pytest.raises(ValueError):
        create_playlist(t, "   ")
    assert seen == ["   "]
"""
    },
}

_C1_SUPPORT = {
    "test_playlist_errors.py": """import pytest

from cratelist.crate import TrackTable, create_playlist


def test_export_failure_propagates_raw_oserror(tmp_path):
    t = TrackTable(m3u_path=str(tmp_path))  # a directory: appending raises OSError
    with pytest.raises(OSError) as ei:
        create_playlist(t, "Sunday set")
    assert type(ei.value).__module__ == "builtins"
"""
}

_REQ1 = Request(
    text=(
        "Add playlists. Give TrackTable an `insert_playlist(playlist)` method that stores "
        "a Playlist under its playlist_id and exports the line `#PLAYLIST:<name>`, and add "
        "a public function `create_playlist(table, name)` that mints an id with prefix "
        '"L", stores an empty playlist with that name and returns it. A blank name (empty '
        "or only whitespace) is invalid and must raise ValueError."
    ),
    target="cratelist/crate.py",
    functional_tests=_C1_FUNCTIONAL,
    regression_tests=_C1_REGRESSION,
    contract_tests=_C1_CONTRACT,
    support_tests=_C1_SUPPORT,
    gold={"api": _gold1("api"), "storage": _gold1("storage")},
)

# ----------------------------------------------------------------- checkpoint 2: queue_track

_C2_FUNCTIONAL = {
    "test_queue_functional.py": """import pytest

from cratelist.crate import TrackTable, add_track, create_playlist, queue_track


def _setup(path=None):
    t = TrackTable(m3u_path=path)
    a = add_track(t, "Blue Train", "Coltrane", 643)
    b = add_track(t, "So What", "Davis", 562)
    p = create_playlist(t, "Late")
    q = create_playlist(t, "Early")
    return t, a, b, p, q


def test_queue_track_appends_and_returns_playlist():
    t, a, b, p, q = _setup()
    out = queue_track(t, p.playlist_id, a.track_id, 0)
    assert out.track_ids == (a.track_id,) and out.name == "Late"
    out = queue_track(t, p.playlist_id, b.track_id, 1)
    assert out.track_ids == (a.track_id, b.track_id)
    assert t.get_playlist(p.playlist_id).track_ids == (a.track_id, b.track_id)
    assert t.get_playlist(q.playlist_id) == q and q.track_ids == ()
    assert t.next_id("L") == "L5"


def test_queue_track_inserts_at_front():
    t, a, b, p, q = _setup()
    queue_track(t, p.playlist_id, a.track_id, 0)
    out = queue_track(t, p.playlist_id, b.track_id, 0)
    assert out.track_ids == (b.track_id, a.track_id)
    assert t.get_playlist(q.playlist_id).track_ids == ()
    assert t.next_id("L") == "L5"


def test_queue_track_exports_the_line(tmp_path):
    t, a, _, p, q = _setup(str(tmp_path / "set.m3u"))
    queue_track(t, p.playlist_id, a.track_id, 0)
    lines = (tmp_path / "set.m3u").read_text().splitlines()
    assert lines[-1] == f"#QUEUE:{p.playlist_id}:{a.track_id}"


def test_queue_unknown_track_or_playlist_raises_keyerror():
    t, a, _, p, q = _setup()
    with pytest.raises(KeyError):
        queue_track(t, p.playlist_id, "T99", 0)
    with pytest.raises(KeyError):
        queue_track(t, "L99", a.track_id, 0)


def test_position_out_of_range_raises_and_changes_nothing():
    t, a, _, p, q = _setup()
    for bad in (-1, 1, 5):
        with pytest.raises(ValueError):
            queue_track(t, p.playlist_id, a.track_id, bad)
    assert t.get_playlist(p.playlist_id).track_ids == ()
    assert t.get_playlist(q.playlist_id).track_ids == ()
    assert t.next_id("L") == "L5"


def test_table_has_insert_at():
    t, a, _, p, q = _setup()
    out = t.insert_at(p.playlist_id, 0, a.track_id)
    assert out.track_ids == (a.track_id,)
    assert t.get_playlist(q.playlist_id) == q
    assert t.next_id("L") == "L5"


def test_queue_track_leaves_other_playlists_and_tracks_alone():
    t, a, b, p, q = _setup()
    kept = queue_track(t, q.playlist_id, b.track_id, 0)
    before = t.next_id("L")
    out = queue_track(t, p.playlist_id, a.track_id, 0)
    assert out.track_ids == (a.track_id,) and out.name == "Late"
    assert t.next_id("L") == before
    assert t.get_playlist(q.playlist_id) == kept
    assert t.get_playlist(q.playlist_id).track_ids == (b.track_id,)
    assert t.get_playlist(q.playlist_id).name == "Early"
    assert t.get_track(a.track_id) is a and t.get_track(b.track_id) is b
"""
}

_C2_REGRESSION = {
    "test_queue_regression.py": """import pytest

from cratelist.crate import TrackTable, add_track, create_playlist


def test_tracks_and_playlists_unchanged(tmp_path):
    t = TrackTable(m3u_path=str(tmp_path / "set.m3u"))
    tr = add_track(t, "Blue Train", "Coltrane", 643)
    p = create_playlist(t, "Late")
    assert t.get_track(tr.track_id) is tr and t.get_playlist(p.playlist_id) is p
    lines = (tmp_path / "set.m3u").read_text().splitlines()
    assert lines == ["#EXTINF:643,Coltrane - Blue Train", "#PLAYLIST:Late"]
    second = add_track(t, "So What", "Davis", 562)
    early = create_playlist(t, "Early")
    assert t.get_track(second.track_id) is second
    assert t.get_playlist(early.playlist_id) is early
    assert t.get_track(tr.track_id) is tr and t.get_playlist(p.playlist_id) is p
    assert t.get_playlist(p.playlist_id).name == "Late"
    assert t.next_id("L") == "L5"
    with pytest.raises(ValueError):
        create_playlist(t, "  ")
    with pytest.raises(ValueError):
        add_track(t, "x", "y", -1)
    t.m3u_path = str(tmp_path)
    with pytest.raises(OSError):
        create_playlist(t, "Early")
"""
}

_C2_CONTRACT = {
    "api": {
        "test_queue_validation.py": """import pytest

from cratelist.crate import TrackTable, add_track, create_playlist, queue_track


def _setup():
    t = TrackTable()
    a = add_track(t, "Blue Train", "Coltrane", 643)
    p = create_playlist(t, "Late")
    return t, a, p


def test_public_function_rejects_position_out_of_range():
    t, a, p = _setup()
    for bad in (-1, 1):
        with pytest.raises(ValueError):
            queue_track(t, p.playlist_id, a.track_id, bad)
    assert t.get_playlist(p.playlist_id).track_ids == ()


def test_table_trusts_callers_on_position():
    t, a, p = _setup()
    out = t.insert_at(p.playlist_id, -1, a.track_id)
    assert out.track_ids == (a.track_id,)
    out = t.insert_at(p.playlist_id, 7, a.track_id)
    assert out.track_ids == (a.track_id, a.track_id)
"""
    },
    "storage": {
        "test_queue_validation.py": """import pytest

from cratelist.crate import TrackTable, add_track, create_playlist, queue_track


def _setup():
    t = TrackTable()
    a = add_track(t, "Blue Train", "Coltrane", 643)
    p = create_playlist(t, "Late")
    return t, a, p


def test_table_rejects_position_out_of_range():
    t, a, p = _setup()
    for bad in (-1, 1):
        with pytest.raises(ValueError):
            t.insert_at(p.playlist_id, bad, a.track_id)
    assert t.get_playlist(p.playlist_id).track_ids == ()


def test_public_function_passes_bad_position_through(monkeypatch):
    t, a, p = _setup()
    seen = []
    real = t.insert_at

    def spy(playlist_id, position, track_id):
        seen.append(position)
        return real(playlist_id, position, track_id)

    monkeypatch.setattr(t, "insert_at", spy)
    with pytest.raises(ValueError):
        queue_track(t, p.playlist_id, a.track_id, 5)
    assert seen == [5]
"""
    },
}

_C2_SUPPORT = {
    "test_queue_errors.py": """import pytest

from cratelist.crate import TrackTable, add_track, create_playlist, queue_track


def test_export_failure_propagates_raw_oserror(tmp_path):
    t = TrackTable()
    a = add_track(t, "Blue Train", "Coltrane", 643)
    p = create_playlist(t, "Late")
    t.m3u_path = str(tmp_path)  # a directory: appending raises OSError
    with pytest.raises(OSError) as ei:
        queue_track(t, p.playlist_id, a.track_id, 0)
    assert type(ei.value).__module__ == "builtins"
"""
}

_REQ2 = Request(
    text=(
        "Add queueing. Give TrackTable an `insert_at(playlist_id, position, track_id)` "
        "method that replaces the stored playlist with a copy whose track_ids has track_id "
        "inserted at position, exports the line `#QUEUE:<playlist_id>:<track_id>` and "
        "returns the updated playlist (an unknown playlist raises KeyError), and add a "
        "public function `queue_track(table, playlist_id, track_id, position)` that checks "
        "the track exists (an unknown track raises KeyError), applies the insert and "
        "returns the updated Playlist. A position below 0 or above the playlist's current "
        "length is invalid and must raise ValueError."
    ),
    target="cratelist/crate.py",
    functional_tests=_C2_FUNCTIONAL,
    regression_tests=_C2_REGRESSION,
    contract_tests=_C2_CONTRACT,
    support_tests=_C2_SUPPORT,
    gold={"api": _gold2("api"), "storage": _gold2("storage")},
)

# ----------------------------------------------------------------- prefix (16 turns)

_PREFIX = [
    Turn(
        "user",
        "I DJ a Sunday afternoon slot at a community radio station and I keep my crate of "
        "tracks and the running orders in a text file that I edit by hand on a Raspberry "
        "Pi in the studio. It works until I fat-finger a line and the player skips a track "
        "on air. I want a small Python package, `cratelist`, that keeps tracks and "
        "playlists in memory and appends an .m3u-style export as I go, so the station's "
        "player can read it and I can diff it afterwards. The export is written by:\n\n```"
        "\ncd ~/radio && python -m cratelist.build --m3u ~/radio/sunday.m3u\n```\n\nA "
        "few hundred tracks, a handful of playlists. No streaming, no metadata lookups, no "
        "GUI; the station has a player already and I just need to feed it a file it "
        "understands. Could you sketch the README scope so nobody at the station thinks "
        "this is a scheduling system? The programme controller already asked if it could "
        "'do the whole week'. The Pi runs headless; I ssh in from a laptop in the studio.",
    ),
    Turn(
        "assistant",
        "Scope in two sentences, a non-goals list, and the smallest usage block that shows "
        "the export path:\n\n```\n## Scope\ncratelist keeps one DJ's tracks and playlists "
        "in memory for a single process and appends an .m3u-style export as records are "
        "added. It is a library for a build script, not a station scheduler or a player."
        "\n\n## Non-goals\n- audio playback or streaming\n- metadata lookup or tagging\n- "
        "week-long station scheduling\n- multi-user editing\n```\n\n```python\nfrom "
        'cratelist.crate import TrackTable, add_track\n\ntable = TrackTable(m3u_path="~/'
        'radio/sunday.m3u")\ntrack = add_track(table, "Blue Train", "Coltrane", 643)\n'
        "print(track)\n```\n\nThe whole-week request is best answered by pointing out that "
        "the player reads any number of .m3u files; someone else can build seven of them. "
        "One README line about the Pi being headless, with the ssh command and where the "
        "export lands, saves whoever covers your slot an afternoon; so does a note that "
        "the export is append-only and safe to diff against last week's.",
    ),
    Turn(
        "user",
        "The export so far is only the `#EXTINF` lines the player understands, one per "
        "track, written from inside `insert_track`. Here is what the file looks like after "
        "a test run:\n\n```\n#EXTINF:643,Coltrane - Blue Train\n#EXTINF:562,Davis - So "
        "What\n#EXTINF:301,Simone - Feeling Good\n```\n\nI am going to add playlist "
        "markers as extra comment lines later; the player ignores comments it does not "
        "know. Durations are whole seconds because that is what `#EXTINF` wants; the "
        "tracks are ripped from vinyl, so the numbers come from the rip and I type them "
        "in. Artists are free text and I do not want any normalisation: `Coltrane` and "
        "`John Coltrane` are allowed to be different. Two questions. Is it wrong that the "
        "table writes the file itself rather than a separate exporter walking the tracks "
        "at the end? And should the export "
        "path be a constructor argument or a module-level setting? I keep going back and "
        "forth because tests want it to be per-instance but the build script only ever "
        "has one.",
    ),
    Turn(
        "assistant",
        "Table-writes-as-it-goes is fine for an append-only export: every mutation passes "
        "through a table method, so no record can be missed, and you get the on-air safety "
        "property you want (the file is always as complete as the table). A single helper "
        "keeps the `None` check in one place:\n\n```python\ndef _export(self, line: str) "
        "-> None:\n    if self.m3u_path is not None:\n        m3u.append_entry(self."
        "m3u_path, line)\n```\n\nConstructor argument, definitely. Per-instance makes tests "
        "trivial (point it at a temp file, read it back) and the build script passing one "
        "path is no burden. Module-level settings are how you end up with a test that "
        "overwrites your real Sunday file. If you later want a full re-export from scratch, "
        "that is a separate function that walks the table and writes a fresh file; it "
        "does not replace the append-as-you-go behaviour, and it can live in the build "
        "script rather than the table. Whole seconds and free-text "
        "artists are both fine; normalising names is a rabbit hole you do not want on a "
        "Sunday afternoon, and the export line carries whatever you typed.",
    ),
    Turn(
        "user",
        "Related: this happened on the Pi when the SD card went read-only, which they do:"
        '\n\n```\nTraceback (most recent call last):\n  File "/home/dj/radio/cratelist/'
        'build.py", line 17, in <module>\n    add_track(table, title, artist, secs)\n  File '
        '"/home/dj/radio/cratelist/crate.py", line 31, in add_track\n    table.insert_track('
        'track)\n  File "/home/dj/radio/cratelist/crate.py", line 19, in insert_track\n    '
        'self._export(f"#EXTINF:{track.seconds},{track.artist} - {track.title}")\n  File '
        '"/home/dj/radio/cratelist/m3u.py", line 5, in append_entry\n    with open(path, '
        '"a", encoding="utf-8") as fh:\nOSError: [Errno 30] Read-only file system: '
        "'/home/dj/radio/sunday.m3u'\n```\n\nThe build script is the only caller and I "
        "run it by hand before the show. Do I need a package exception class, or is that "
        "over-engineering for one file?",
    ),
    Turn(
        "assistant",
        "Over-engineering for one file. The OSError already carries the errno and the path, "
        "which is exactly what you need to know the SD card has gone read-only, and the "
        "build script can catch it in one line:\n\n```python\ntry:\n    main()\nexcept "
        'OSError as exc:\n    sys.exit(f"export failed: {exc}")\n```\n\nA package exception '
        "earns its place when callers must treat several unrelated failures the same way "
        "or when you want to hide an implementation detail; a DJ's crate with one output "
        "file has neither. Wrapping would push the errno one level down in the traceback "
        "for no gain. Leave `m3u.append_entry` to raise, leave `_export` to pass it "
        "through, and revisit only if a second failure source ever appears. One practical "
        "addition for the read-only case: point `m3u_path` at a USB stick for the show and "
        "copy the file over afterwards; the code does not need to know, because the path "
        "is a constructor argument and the build script decides where it goes. Running it "
        "by hand before the show is also the right time to see the error, which is one "
        "more reason not to hide it.",
    ),
    Turn(
        "user",
        "Ids: tracks are T1, T2, ... and playlists will be L1, L2, ... from one shared "
        "counter, so a number never means two things when I'm reading the export on air. "
        "Here's the running-order printer I use in the studio, so you can see how records "
        "get consumed:\n\n```python\nfrom cratelist.crate import TrackTable\n\n\ndef "
        "print_order(table: TrackTable, track_ids: list[str]) -> None:\n    total = 0\n"
        "    for tid in track_ids:\n        tr = table.get_track(tid)\n        total += "
        'tr.seconds\n        print(f"{total // 60:3d}:{total % 60:02d}  {tr.artist} - '
        '{tr.title}")\n```\n\nThe cumulative time is what I actually watch during the show. '
        "Track ids also go on the crate dividers in marker pen, `T14` on the sleeve of Blue "
        "Train, so once minted they are permanent; I will never reuse a number even if a "
        "track is removed. Anything you would change before I build the playlist features "
        "on top of this?",
    ),
    Turn(
        "assistant",
        "The shared counter with a prefix is the right call for reading ids aloud. One "
        "change to the printer: `get_track` raises KeyError for an unknown id, which is "
        "correct for the table, but a running order pasted from last week can reference "
        "a track you deleted, and on air you want the printout to continue:\n\n```python\n"
        'try:\n    tr = table.get_track(tid)\nexcept KeyError:\n    print(f"       ?? {tid} '
        'missing")\n    continue\n```\n\nKeep the tolerance in the studio script, not in '
        "the table; the table raising is what lets the build script fail loudly before "
        "the show. The cumulative-time formatting is fine; if you ever want it in the "
        "export too, `#EXTINF` already carries the seconds. Permanent ids on sleeves means "
        "the counter must never go backwards and removals must not renumber; a `removed` "
        "set in the table later would let `get_track` keep raising for those ids while the "
        "export still lists what was played. The counter as written already guarantees no "
        "reuse within a session, and a persisted counter would carry that across sessions "
        "when you add the JSON dump.",
    ),
    Turn(
        "user",
        "Two conventions to fix before the real features. First, errors: file and I/O "
        "failures from the export propagate raw. No package exception class, no wrapping, "
        "no catching inside `cratelist.crate`; a caller sees the original OSError. That "
        "covers everything the table does, existing and new.",
    ),
    Turn(
        "assistant",
        "Noted: the export's OSError propagates unchanged through every table method and "
        "public function; no exception class, no try/except around the write. New methods "
        "call `self._export(...)` and let failures fall through.",
    ),
    Turn(
        "user",
        "Second, validation: it lives in the public functions. They check their arguments "
        "and raise ValueError before calling the table, the way `add_track` rejects "
        "non-positive seconds today. TrackTable methods trust their callers and do not "
        "validate; they store what they are given and write the export line.",
    ),
    Turn(
        "assistant",
        "Understood: validation belongs to the public functions in `crate.py`, which raise "
        "ValueError up front, and TrackTable methods stay thin and trusting like "
        "`insert_track`. New table methods will store and export only.",
    ),
    Turn(
        "user",
        "For later, not now: a `total_seconds(playlist_id)` on the table so the studio "
        "printer stops summing by hand. Parking it.",
    ),
    Turn(
        "assistant",
        "Parked. It will be a sum over the playlist's track ids looked up in the table; "
        "nothing else changes for it.",
    ),
    Turn(
        "user",
        "For the record, the tests that exist today are just these:\n\n```python\nimport "
        "pytest\n\nfrom cratelist.crate import TrackTable, add_track\n\n\ndef "
        'test_add_track_mints_t1():\n    assert add_track(TrackTable(), "a", "b", 10).'
        'track_id == "T1"\n\n\ndef test_add_track_rejects_zero_seconds():\n    with pytest.'
        'raises(ValueError):\n        add_track(TrackTable(), "a", "b", 0)\n```\n\nI will '
        "paste the current files with each request so you see the real state.",
    ),
    Turn(
        "assistant",
        "Ready. Send the first feature and I will return the complete `crate.py`.",
    ),
]

_EVENT = (
    "Side note before the next one: the station moved my slot to 4pm, so the export on "
    "the Pi is now called sunday-4pm.m3u. Nothing about how we write the code changes."
)


def build() -> Session:
    return Session(
        id="S25",
        project="cratelist",
        target_family="validation",
        support_family="error_surface",
        lifecycle="stable",
        files=_FILES,
        prefix=_PREFIX,
        states=("api", "storage"),
        state_at=("api", "api"),
        event=_EVENT,
        requests=(_REQ1, _REQ2),
        rule_turns=(8, 10),
    )
