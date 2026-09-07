"""CPU-only saved-response replay; isolated frozen SLAB v1 consumer."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FREEZE = '184cb321'
TOLERANCES = ('trailing_closer', 'lift_report', 'test_path', 'strip_leading_fence')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        if '/data/bench' in str(Path(os.fsdecode(args[0])).absolute()):
            raise RuntimeError('forbidden benchmark access')
    if event in ('os.kill', 'os.killpg', 'socket.connect'):
        raise RuntimeError('signals and network forbidden')


def normalized(value):
    return json.loads(json.dumps(value))


def install_tolerance(slab):
    original = slab.parse_envelope

    def parse(output, tolerances=None):
        text = output.lstrip(' \t\r\n')
        opening = re.match(r'```(?:json)?\r?\n', text)
        if not opening:
            return original(output, tolerances)
        interior = text[opening.end():].rstrip(' \t\r\n')
        closing = re.search(r'\r?\n[ \t]*```$', interior)
        if closing:
            interior = interior[:closing.start()]
        # Fence markers inside JSON strings are content; only structural extra
        # fences/prose fail via the frozen raw decoder and trailing-data check.
        pending = []
        payload = original(interior, pending)
        if tolerances is not None:
            tolerances.append(dict(tolerance='strip_leading_fence', closed=bool(closing)))
            tolerances.extend(pending)
        return payload

    slab.parse_envelope = parse


def load_rows():
    baseline = json.loads((ROOT/'results/quick-checks/check47/moe-baseline.json').read_text())
    paths = ['results/quick-checks/check47/records.jsonl', *baseline['source_files']]
    groups = {'dense': {}, 'moe': {}}
    for index, name in enumerate(paths):
        path = ROOT/name
        for line, raw in enumerate(path.read_text().splitlines(), 1):
            row = json.loads(raw)
            d = row['oracle_checker_results'][0]
            if d['arm'] != 'R' or d['episode'] not in ('slab-dev-00', 'slab-dev-01'):
                continue
            trunk = 'dense' if index == 0 else 'moe'
            key = (d['episode'], d['round'])
            assert key not in groups[trunk], (name, key)
            groups[trunk][key] = (row, name, line)
    assert all(len(g) == 32 for g in groups.values())
    assert set(groups['dense']) == set(groups['moe'])
    return groups, {name: sha(ROOT/name) for name in paths}


def replay(slab, groups, directory, verify):
    records = []
    for trunk, group in groups.items():
        for episode_id in ('slab-dev-00', 'slab-dev-01'):
            episode = slab.generate_episode('dev', int(episode_id.rsplit('-', 1)[1]))
            workspace = directory/trunk/episode_id
            slab.materialize(episode, workspace)
            executor = slab.Executor(workspace, json.loads((workspace/'public_tests.json').read_text()))
            for turn in range(16):
                row, source, line = group[(episode_id, turn)]
                execution = executor.run(row['output'])
                outcome = slab.check(episode, turn, row['output'], executor, truncated=row['truncated'])
                execution.pop('wall_seconds')
                hashes = executor.hashes()
                saved = row['oracle_checker_results'][0]
                if verify:
                    assert normalized(outcome) == saved['outcome'], (trunk, turn, 'outcome')
                    for key in ('executed', 'results', 'tolerances'):
                        assert normalized(execution[key]) == saved['execution'][key], (trunk, turn, key)
                    assert hashes == saved['artifact_hashes'], (trunk, turn, 'hashes')
                edits = [c for c in execution['executed'] if c['op'] in ('edit', 'replace')]
                widths = [w for c in edits for w in slab.indent_widths(c['code'])]
                records.append(dict(trunk=trunk, episode=episode_id, round=turn,
                    source=source, source_line=line, output=row['output'],
                    output_sha256=hashlib.sha256(row['output'].encode()).hexdigest(),
                    saved_prompt_sha256=hashlib.sha256(row['rendered_messages'].encode()).hexdigest(),
                    matched_prompt=groups['dense'][(episode_id, turn)][0]['rendered_messages'] ==
                        groups['moe'][(episode_id, turn)][0]['rendered_messages'],
                    truncated=row['truncated'], eos=row['eos'], execution=execution,
                    outcome=outcome, artifact_hashes=hashes, indent_widths=widths,
                    expected_indent=int(dict(episode.turns[turn].live)['indent']),
                    indent_compliant=bool(edits) and bool(widths) and
                        all(w == int(dict(episode.turns[turn].live)['indent']) for w in widths)))
    return records


def boundary_tests(slab, root):
    episode = slab.generate_episode('dev', 0)
    body = slab.reference(episode, 0)
    cases = [(body, True, 0), ('```json\n'+body, True, 1),
        (' \n```\n'+body+'\n``` \n', True, 1),
        ('```json\r\n'+body+'\r\n```', True, 1),
        ('```json\n'+body[:-1], False, 0),
        ('prose\n```json\n'+body+'\n```', False, 0),
        ('```json\n'+body+'\n```\n```json\n'+body+'\n```', False, 0),
        ('```json\n'+body+'\n```\nprose', False, 0)]
    for index, (text, accepted, count) in enumerate(cases):
        workspace = root/str(index)
        slab.materialize(episode, workspace)
        executor = slab.Executor(workspace, json.loads((workspace/'public_tests.json').read_text()))
        feedback = executor.run(text)
        result = slab.check(episode, 0, text, executor)
        assert bool(feedback['executed']) == accepted
        assert result['success'] == accepted, (index, result)
        assert sum(t['tolerance'] == 'strip_leading_fence' for t in feedback['tolerances']) == count
    return len(cases)


def summarize(rows):
    return dict(rounds=len(rows), executed=sum(bool(r['execution']['executed']) for r in rows),
        caps=sum(r['truncated'] for r in rows),
        final_episodes=sum(r['round'] == 15 for r in rows),
        final_success=sum(r['outcome']['success'] for r in rows if r['round'] == 15),
        successful_rounds=sum(r['outcome']['success'] for r in rows),
        violations={k: sum(r['outcome']['violations'][k] for r in rows) for k in rows[0]['outcome']['violations']},
        indent_compliant=sum(r['indent_compliant'] for r in rows),
        tolerance_replies={t: sum(any(e['tolerance'] == t for e in r['execution']['tolerances']) for r in rows) for t in TOLERANCES},
        tolerance_events={t: sum(e['tolerance'] == t for r in rows for e in r['execution']['tolerances']) for t in TOLERANCES})


def main():
    sys.addaudithook(guard)
    groups, inputs = load_rows()
    with tempfile.TemporaryDirectory(prefix='check47-replay-') as temp:
        root = Path(temp)
        snapshot = root/'frozen'
        snapshot.mkdir()
        archive = subprocess.check_output(['git', '-C', str(ROOT), 'archive', FREEZE, 'src', 'scripts'])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(snapshot, filter='data')
        reg = json.loads((ROOT/'results/quick-checks/check47/registration.json').read_text())
        sources = {}
        for name, digest in reg['source_hashes'].items():
            if name.startswith(('src/', 'scripts/')):
                assert sha(snapshot/name) == digest, name
                sources[name] = digest
        sys.path.insert(0, str(snapshot/'src'))
        from stencil.focus import slab
        assert Path(slab.__file__).is_relative_to(snapshot)
        original = replay(slab, groups, root/'original', True)
        install_tolerance(slab)
        tests = boundary_tests(slab, root/'tests')
        rows = replay(slab, groups, root/'tolerated', False)
    assert sum(r['matched_prompt'] for r in rows) == 4
    for old, new in zip(original, rows, strict=True):
        if new['trunk'] == 'moe':
            assert old == new, 'MoE replay changed under fence tolerance'
    fences = [e for r in rows for e in r['execution']['tolerances']
              if e['tolerance'] == 'strip_leading_fence']
    assert len(fences) == 32 and sum(e['closed'] for e in fences) == 13
    summary = dict(freeze=FREEZE, registration_commit='97ca5c5b', cpu_only=True,
        source_hashes=sources, input_hashes=inputs, original_exact_replays=len(original),
        boundary_tests=tests, replayed_replies=len(rows), matched_pairs=2,
        summary={scope: {trunk: summarize([r for r in rows if r['trunk'] == trunk and predicate(r)])
            for trunk in groups} for scope, predicate in (
                ('all32_descriptive', lambda r: True),
                ('matched_round0', lambda r: r['matched_prompt']),
                ('unmatched_round1_15', lambda r: not r['matched_prompt']))})
    content = ''.join(json.dumps(r, sort_keys=True)+'\n' for r in rows)
    assert len(content.encode()) <= 10_000_000
    (OUT/'records.jsonl').write_text(content)
    summary['records_sha256'] = sha(OUT/'records.jsonl')
    summary['records_bytes'] = (OUT/'records.jsonl').stat().st_size
    summary['replay_script_sha256'] = sha(Path(__file__))
    (OUT/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
