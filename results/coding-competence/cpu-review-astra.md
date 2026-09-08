# Coding competence CPU review — round 1

2026-09-08. Reviewer: Astra, xhigh, explicitly requested instead of the
repository's default Opus reviewer. Author-disjoint review; only this review
file was written. No model/GPU calls, data edits or full test suite.

Reviewed snapshots:

- `scripts/coding_competence_dev.py`: SHA-256
  `267aa81bd2e2ba62e7bf3dd347c3a94434f9d43f9ae1a26cdc603d96b132e88f`.
- `tests/test_coding_competence_dev.py`: SHA-256
  `67b9a40135d2fa113fbd96a20e4d066ce1f953b24cf21f6777c17c76e7d36d55`.

Compared with [PROTOCOL.md](PROTOCOL.md), [DATA-CONTRACT.md](DATA-CONTRACT.md)
and [NATIVE-CONTRACT.md](NATIVE-CONTRACT.md). Runtime transport and semantic
acceptance of authored data are separate review units.

**Final round-1 score: 82/100. Verdict: HOLD.** Threshold 90; open findings:
critical 0, high 2, medium 2, low 0. The initial 86/100 assessment with findings
1–3 was extended by the parent-requested overlap probe in finding 4 below.

## Findings

1. **HIGH — unsupported restriction to the current task handle. OPEN.**
   `_validate_rule`, lines 185–186, rejects every effective rule whose scope is
   neither global nor the current request's handle. DATA-CONTRACT permits global
   or any declared task handle; dependent work can retain relevant earlier
   helper-scoped rules. Handle inequality alone does not establish semantic
   inapplicability. Through the actual `public_projection` consumer, changing a
   synthetic fixture's round-1 rule to its other declared handle raises
   `ValidationError: ... is not applicable to the current request` before any
   executable checks. Parent separately reports the same gate on three authored
   projects, with independent semantic confirmation of relevant helper rules.
   Keep declared-scope and visible-source validation; remove this extra equality
   requirement and leave semantic applicability to the registered source review.
   Add a consumer control accepting a declared earlier handle while still
   rejecting an undeclared one. This finding does not endorse every authored rule.

2. **MEDIUM — exported tool schema differs from the frozen native contract.
   OPEN.** `REPLACE_FUNCTION_TOOL`, lines 73–75, adds a `description` inside the
   `source` property. NATIVE-CONTRACT fixes the parameter schema exactly with
   `source: {"type":"string"}` and requires structural equality in the render
   receipt. Direct comparison returns false. The runtime must not inherit two
   competing schema definitions. Remove the extra parameter description, retaining
   the separately permitted fixed function description, and test exact equality
   to the registered argument schema.

3. **MEDIUM — invalid-input CLI receipt loses input provenance. OPEN.**
   `main`, lines 779–787, emits code hashes and an error after validation fails,
   but discards input paths, byte hashes and elapsed time. A direct absolute-path
   CLI invocation from `/tmp`, without `PYTHONPATH`, returned exit 2 and `INVALID`
   for the scope probe; its only keys were `schema_version`, `kind`, `model_calls`,
   `status`, `error`, `code_sha256`. The saved receipt cannot identify the exact
   rejected input bytes. Retain available input path/byte/hash receipts before
   parsing/validation and include them on failure, with elapsed time and explicit
   read errors where bytes are unavailable. Invalid data need not be executed.

4. **HIGH — valid functional-mutant overlap metadata is rejected. OPEN.**
   The control validation around lines 515–519 permits only functional IDs for
   a functional control. DATA-CONTRACT requires at least one listed private
   discriminator of the corresponding kind and explicitly permits functional
   mutants to fail full-output obligation checks. It does not forbid recording
   those additional failures in `expected_failing_check_ids`. Author-03 round 0
   lists one functional and two current obligation IDs on its functional control;
   the validator rejects that structure before executing any checks. An actual
   consumer counterexample confirms the restriction: append
   `private-obligation-alpha-0` to the synthetic fixture's functional control.
   `validate_document` raises `names a non-functional private check`, while
   `_audit_control` executes the same patch and records `named_checks_failed=true`,
   both current obligation checks failed, and `valid=true`. Permit active private
   functional/current obligation IDs, require at least one corresponding-kind
   discriminator, and continue verifying every listed failure. Preserve the
   separate requirement that obligation mutants pass all cumulative private
   functionality. This finding establishes the mechanical restriction and the
   reproduced synthetic behavior, not the correctness of authored mutant code.

## Verification and limits

The targeted suite independently passed: **8 tests, 2.42 seconds**. Ruff passed
on both files. Both SHA-256 values were rechecked unchanged after the probes.

The actual safe consumer retained a valid-but-wrong function unchanged in the
applied module, recorded both failing public checks, and preserved the following
target definitions exactly. Empty check results cannot pass `_all_pass`.
Existing targeted controls passed for byte-zero source, compile-before-apply,
public/private projection isolation, type-sensitive case equality, cumulative
functionality/current-only obligations, and mutant checks. References and
mutants use `consume_action` and the accepted fresh-process seccomp check path;
the upcoming runtime must use these same interfaces.

A fresh import from `/tmp` passed with audit hooks rejecting subprocess launch,
network connection and file writes. The direct CLI failure above also confirms
standalone import/path handling beyond `--help`.

The public projection contains the complete public episode; the runtime still
must expose only the appropriate source history and current request. Dependency
name detection and nonempty user source IDs are structural checks, not proof of
actual dependency use or user adoption. The code correctly labels public-rule
invariance as requiring independent semantic review and reference token sizes as
provisional. No additional framework or data rewriting is requested.

## Round 2 — fixed snapshot re-verification

2026-09-08. Same author-disjoint Astra xhigh reviewer and CPU-only scope.
The round-1 findings and their original severities above are preserved as
history; their current dispositions follow.

Reviewed replacement snapshots:

- `scripts/coding_competence_dev.py`: SHA-256
  `695e9e6228d6ed540d0235442ec3aa515ff1f00b6f3ad303ba76354feaa407a0`.
- `tests/test_coding_competence_dev.py`: SHA-256
  `2c324652613360e2e9bb386d20c52d62f5e874ac8780e8ba45ecfdd0b95cb0ed`.

**Score: 96/100. Verdict: ACCEPT for the CPU consumer/validator unit.**
Threshold 90; open critical/high/medium/low findings: 0/0/0/0.

1. **HIGH — RESOLVED.** Declared scopes are accepted independently of the current
   task handle. The actual `public_projection` regression accepts the earlier
   declared handle and still rejects an undeclared handle. Visible-source
   validation remains; semantic applicability is not inferred from handle equality.
2. **MEDIUM — RESOLVED.** The exported argument schema now equals the fixed
   NATIVE-CONTRACT schema exactly. Its equality assertion passed; the separate
   function description remains present.
3. **MEDIUM — RESOLVED.** Input receipts survive read, parse and document-validation
   errors, with paths, available byte counts/hashes, explicit read/parse errors
   and elapsed time. The targeted direct-CLI test covers malformed and missing
   files. Additional actual CLI probes from `/tmp`, without `PYTHONPATH`, covered
   a readable schema-invalid document and a three-input sequence of malformed,
   missing and later-readable files. Both returned exit 2/`INVALID`, retained all
   input paths and available exact byte hashes, and reported elapsed time.
4. **HIGH — RESOLVED.** Expected failure IDs may span active cumulative private
   functionality and current obligations, with at least one discriminator of
   the declared control kind. The actual `_audit_control` regression accepts
   mixed functional/obligation failures and records overlap. It still rejects
   missing same-kind discrimination, a listed check that actually passes, and
   an obligation mutant that damages private stable functionality.

Independent validation: **10 targeted tests passed in 2.69 seconds; Ruff passed**
for both files. The original source/compile/state/projection/cumulative checks
remain in this passing suite. No data or runtime code was edited; no authored-bank
preflight or worker inference was run in this re-review.
This acceptance does not accept authored semantics, establish actual native
server compatibility, or authorize worker inference.
