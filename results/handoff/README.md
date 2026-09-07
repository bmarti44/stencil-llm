# Handoff kit — verified 2026-09-07

Read [the handoff](../HANDOFF-astra.md) first. Both larger runs are complete, frozen and unrescorable. Archived briefs and chains record issued work; none is current launch authority. The old queued/running list is retired.

The kit contains original briefs, issued assembled prompts, preserved scratchpad variants and chain scripts. The missing [larger-test full prompt](briefs/larger-test-full.md) is explicitly marked as a reconstruction from archived inputs; its original issued bytes could not be recovered. Shell variable names for task/full/real outputs are templates, not absent literal brief files. [VERIFICATION.md](VERIFICATION.md) lists every addition and all archive hashes. Four scratchpad briefs differ from their existing archive: check48, check49, check50 and driverfix. The original archive is retained; the corresponding files ending the scratchpad-variant suffix preserve the session version. The assembled full and real prompt files prompts preserve what later chains consumed. No experiment logic has been edited.

## Rebuild after the scratchpad is wiped

Reconstruct files for reading first; do not execute archived chains. They embed the old absolute scratchpad path, wait on ephemeral success strings, and some emit DONE even after a failed command. Several use multi-pattern `ls` for flags, which can return failure despite an existing flag when another pattern is absent. They are historical records, not safe launch templates. Do not manufacture logs, GO files or success sentinels to unlock them.

The following commands create a new private temporary directory and copy the archived documents/scripts; they do not run an agent or experiment:

```bash
cd /home/bmarti44/stencil-llm
HANDOFF_RECOVERY_DIR=$(mktemp -d /tmp/stencil-handoff-recovery.XXXXXX)
cp /home/bmarti44/stencil-llm/results/handoff/briefs/*.md "$HANDOFF_RECOVERY_DIR/"
cp /home/bmarti44/stencil-llm/results/handoff/chains/*.sh "$HANDOFF_RECOVERY_DIR/"
printf '%s\n' "$HANDOFF_RECOVERY_DIR"
# Example: reconstruct an old prompt for inspection only, preserving archived originals.
cat /home/bmarti44/stencil-llm/results/handoff/briefs/post-reboot-common.md \
    /home/bmarti44/stencil-llm/results/handoff/briefs/larger-test-v2-brief.md \
    > "$HANDOFF_RECOVERY_DIR/reconstructed-larger-test-v2.md"
```

The reconstruction is not guaranteed byte-identical to the issued prompt: inspect the archived [actual larger-test-v2 full prompt](briefs/larger-test-v2-full.md) when historical bytes matter. Resolve all referenced brief names using the archive manifest; generated full prompts are not new authorizations. Scratchpad logs, PIDs, worktrees, response data and diagnostic scripts are not recreated by these copies.

For a **new authorized task**, create a new chain rather than replaying the archive:

1. Write the prospective brief, exact input/output paths, lineage, budget, stop-loss and acceptance criteria. Confirm each prerequisite using its saved result and exit evidence, not an old log sentinel. The agreed factorial has no completed implementation/registration yet.
2. Choose a new scratch directory and replace every scratchpad/log/input/output path in the new chain with an absolute path. Rebuild its full prompt from the appropriate common note and new brief. Review the entire resulting prompt for historical instructions that no longer apply.
3. Run the handoff's read-only lock/process/container/GPU checks. Use a recursive RUNNING.flag search and treat any match as blocking. Serial ownership must be established before launch; checking flags is not an atomic reservation, and empty output does not prove the GPU is idle.
4. Preserve individual command exit codes; fail the chain on failure. With pipelines use pipefail. Emit completion only after the actual acceptance checks pass. Run shell syntax checks and a non-launch smoke path before executing any new shell logic.
5. Register the PID of each background job you actually launch immediately in the repository's ignored ownership registry. Do not copy historical PID values into a new registry. Keep the actual GPU workload foreground inside the owner process and use cooperative deadlines. No inherited PID authorizes a signal.

Accuracy/code reviewers are author-disjoint Opus at maximum reasoning effort (request maximum effort in the prompt if no effort dial exists). Record any model substitution and its reason in the review header. Astra result audits are self-audits. The archived fixed model choices are historical.

## Mechanically resolve the four current documents

Repository-root code paths and document-relative Markdown links use different bases. This CPU-only recipe checks Markdown links and explicit path-like code spans, including line locators. It also recognizes bare paths with common file extensions. Command examples are checked separately below; runtime RUNNING.flag conventions are not assertions that a flag should exist. Run from the repository root. Every current artifact reference should name one concrete existing file; brace/elision shorthand has been removed from the four documents.

```python
from pathlib import Path
import re
root = Path.cwd()
docs = [root / p for p in (
    'results/HANDOFF-astra.md', 'results/NEXT-TESTS-PLAN.md',
    'results/CLAIMS-CORRECTIONS.md', 'results/handoff/README.md')]
checked, broken = set(), set()
for doc in docs:
    # Command examples contain prospective/dynamic outputs, not artifact links.
    body = re.sub(r'```.*?```', '', doc.read_text(), flags=re.S)
    refs = [(p, True) for p in re.findall(r'\]\(([^)]+)\)', body)]
    refs += [(p, False) for p in re.findall(r'`([^`\n]+)`', body)
             if re.search(r'\.(?:md|py|sh|jsonl?|npz|safetensors)(?::|$)', p)]
    refs += [(p, False) for p in re.findall(
        r'(?<![\w/])(?:results|src|data|models|scripts|tools)/[\w./-]+\.(?:md|py|sh|jsonl?|npz|safetensors)', body)]
    for ref, link in refs:
        if ref.startswith(('http:', 'https:', '#')):
            continue
        ref = re.sub(r':\d[\d,–-]*$', '', ref.split('#')[0])
        if '$' in ref or '*' in ref:
            raise ValueError('Nonconcrete artifact reference: ' + ref)
        base = doc.parent if link else root
        path = (base / ref).resolve()
        checked.add((str(doc.relative_to(root)), ref, str(path)))
        if not path.is_file():
            broken.add((str(doc.relative_to(root)), ref))
print(f'{len(checked)} unique document/path checks; {len(broken)} broken')
for item in sorted(broken):
    print(item)
assert not broken
```

This checks existence, not semantic truth or bank exposure. Weight/raw-body hashes and kit copy identity are recorded separately in [VERIFICATION.md](VERIFICATION.md). No dependency on an ephemeral validator script is required to repeat the path check.

Command-path verification: all literal input paths in the recovery examples exist; shell globs expand to archived files. The recovery directory and reconstructed prompt are prospective outputs. The handoff's root ownership registry, review lock and Ollama executable were present; runtime flags and container model mounts are conventions rather than asserted repository artifacts. A no-launch recovery smoke copied the kit and rebuilt the example prompt; no archived chain was executed.
