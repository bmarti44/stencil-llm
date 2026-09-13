"""The sixteen DEVELOPMENT blocks for the scoped-instruction diagnostic.

Development material only.  Astra's lineage rule for this program: fit or select
on development material only; evaluate once on a separately authored frozen
confirmation set.  These blocks may be inspected, revised and argued with; the
confirmation projects may not.

Each block holds one entering repository and TWO matched applicability cases
that require DIFFERENT executable behaviour from IDENTICAL entering code, so a
block succeeds only if both cases succeed.  `defeats` names the trivial policies
the block is constructed to refute; the gate in `scripts/scoped_gate.py` checks
that it actually does.
"""

from __future__ import annotations

from stencil.scoped_blocks import Block, Case, Event

LOOKUP = "fetch_rate"
BULK = "gather_rates"


def _case(path, kind):
    return Case(name=f"{path}:{kind}", path=path, fn_kind=kind,
                fname=LOOKUP if kind == "lookup" else BULK)


GLOBAL_RAISE = "Across the package, a lookup for a key that isn't in the table" \
               " must raise MissingEntry. No placeholder values."
GLOBAL_NONE = "Across the package, a key that isn't in the table comes back as" \
              " None."
GLOBAL_DEFAULT = "Across the package, a key that isn't in the table comes back" \
                 " as DEFAULT."
NOTE_RULE = "Every public function in the package calls note() with its own" \
            " name as its first statement, so the audit log stays complete."

# --------------------------------------------------------------- family S
# A namespace exception: the newest policy governs inside the namespace, and a
# fresh operation outside it must still follow the older applicable policy.

S1 = Block(
    id="S1", family="scope", precedent="none",
    history=(
        Event("s1a", GLOBAL_RAISE, "set", "*", None, "raise"),
        Event("s1b", "Inside compat.py, missing entries should come back as None"
                     " instead -- the old clients can't handle the exception.",
              "set", "compat", None, "none"),
    ),
    cases=(_case("compat", "lookup"), _case("core", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="Newest applies in compat; the fresh operation in core follows the older"
         " global rule.",
)

S2 = Block(
    id="S2", family="scope", precedent="raise",
    history=(
        Event("s2a", "In core.py a missing entry has to raise MissingEntry --"
                     " the pricing path must not see a silent None.",
              "set", "core", None, "raise"),
        Event("s2b", "Across the package a key that isn't in the table comes back"
                     " as None. core.py keeps its own rule; this is for"
                     " everywhere else.",
              "set", "*", None, "none"),
    ),
    cases=(_case("core", "lookup"), _case("compat", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="The exception is on core rather than compat, and the broad statement"
         " arrives LAST while explicitly preserving it, so the most specific"
         " live rule and the most recent applicable rule disagree.",
)

S3 = Block(
    id="S3", family="scope", precedent="default",
    history=(
        Event("s3a", GLOBAL_NONE, "set", "*", None, "none"),
        Event("s3b", "The bulk gather helpers are the exception: if any requested"
                     " key is missing from the table they must raise MissingEntry,"
                     " because the report sums whatever comes back.",
              "set", "*", "bulk", "raise"),
    ),
    cases=(_case("core", "bulk"), _case("core", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="Scope by OPERATION rather than path: same file, two operations, two"
         " answers.",
)

S4 = Block(
    id="S4", family="scope", precedent="none",
    history=(
        Event("s4a", GLOBAL_NONE, "set", "*", None, "none"),
        Event("s4b", "One exception: the bulk gather in compat.py must raise"
                     " MissingEntry when a key is absent -- that path feeds the"
                     " reconciliation job and cannot skip rows.",
              "set", "compat", "bulk", "raise"),
    ),
    cases=(_case("compat", "bulk"), _case("compat", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="Path AND operation together; both cases are in the same file.",
)

# --------------------------------------------------------------- family G
# A genuine global revision changes a fresh operation, while a narrower live
# rule survives it.

G1 = Block(
    id="G1", family="global", precedent="none",
    history=(
        Event("g1a", GLOBAL_NONE, "set", "*", None, "none"),
        Event("g1b", "For the bulk gather helpers a missing key should come back"
                     " as DEFAULT rather than None -- the report code sums them.",
              "set", "*", "bulk", "default"),
        Event("g1c", "Change of plan for the whole package: a missing entry must"
                     " raise MissingEntry now.",
              "replace", "*", None, "raise"),
    ),
    cases=(_case("core", "lookup"), _case("core", "bulk")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="The revision reaches the fresh lookup; the operation-scoped rule for"
         " bulk survives it.",
)

G2 = Block(
    id="G2", family="global", precedent="raise",
    history=(
        Event("g2a", GLOBAL_DEFAULT, "set", "*", None, "default"),
        Event("g2b", "For the single-key lookups, a missing entry comes back as"
                     " None instead -- callers there already branch on it.",
              "set", "*", "lookup", "none"),
        Event("g2c", "Change of plan for the whole package: a missing entry must"
                     " raise MissingEntry now.",
              "replace", "*", None, "raise"),
    ),
    cases=(_case("core", "bulk"), _case("core", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="Mirror of G1 with the operation scopes swapped.",
)

G3 = Block(
    id="G3", family="global", precedent="raise",
    history=(
        Event("g3a", GLOBAL_RAISE, "set", "*", None, "raise"),
        Event("g3b", "Inside compat.py, missing entries come back as None.",
              "set", "compat", None, "none"),
        Event("g3c", "Change of plan for the whole package, compat included: a"
                     " missing entry comes back as DEFAULT everywhere now.",
              "replace", "*", None, "default", clears=("compat",)),
        Event("g3d", "The legacy corner of compat still needs None for a missing"
                     " entry -- compat/legacy.py only, nothing else.",
              "set", "compat.legacy", None, "none"),
    ),
    cases=(_case("compat.legacy", "lookup"), _case("compat", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="A broad revision that explicitly clears a narrower exception, then a"
         " NEW narrower exception one level deeper.",
)

# --------------------------------------------------------------- family C
# Cancellation: unrelated, quoted, actual-exposing-a-live-default, and
# actual-not-reviving-a-superseded-rule.

C1 = Block(
    id="C1", family="cancel", precedent="default",
    history=(
        Event("c1a", GLOBAL_RAISE, "set", "*", None, "raise"),
        Event("c1b", "Inside compat.py, missing entries come back as None.",
              "set", "compat", None, "none"),
        Event("c1b2", "Actually in compat.py make a missing entry DEFAULT rather"
                      " than None -- None was ending up in the totals.",
              "replace", "compat", None, "default"),
        Event("c1c", "Drop the compat exception -- we're not keeping a special"
                     " missing-entry rule for that namespace any more.",
              "cancel", "compat"),
        Event("c1d", "For the bulk gather helpers a missing key comes back as"
                     " DEFAULT.",
              "set", "*", "bulk", "default"),
    ),
    cases=(_case("compat", "lookup"), _case("core", "bulk")),
    defeats=("always_newest", "always_oldest", "flip_on_cancel", "copy_existing",
             "recency_general"),
    note="Cancelling the compat exception exposes the STILL-LIVE global rule --"
         " not the package baseline, and not the None rule the exception itself"
         " had replaced.",
)

C2 = Block(
    id="C2", family="cancel", precedent="raise", entering_obligations=("note",),
    history=(
        Event("c2z", NOTE_RULE, "obligate", "*", name="note"),
        Event("c2a", GLOBAL_RAISE, "set", "*", None, "raise"),
        Event("c2b", "Inside compat.py, missing entries come back as None.",
              "set", "compat", None, "none"),
        Event("c2c", "Cancel the docstring-style rule -- we're not enforcing the"
                     " one-line summary any more."),
    ),
    cases=(_case("compat", "lookup"), _case("core", "lookup")),
    defeats=("always_newest", "always_oldest", "flip_on_cancel", "copy_existing"),
    note="Cancellation LANGUAGE aimed at an unrelated rule. The missing-entry"
         " policy is untouched, and the note() obligation is untouched too.",
)

C3 = Block(
    id="C3", family="cancel", precedent="raise", entering_obligations=("note",),
    history=(
        Event("c3z", NOTE_RULE, "obligate", "*", name="note"),
        Event("c3a", GLOBAL_DEFAULT, "set", "*", None, "default"),
        Event("c3b", "Inside compat.py, a missing entry must raise MissingEntry.",
              "set", "compat", None, "raise"),
        Event("c3c", "Ignore the message in the other thread about cancelling the"
                     " compat rule -- we talked it over and it stands."),
        Event("c3d", "Stop making note() calls in new code; the audit log moved to"
                     " the gateway. Leave the existing calls where they are.",
              "release", "*", name="note"),
    ),
    cases=(_case("compat", "lookup"), _case("core", "lookup")),
    defeats=("always_newest", "always_oldest", "flip_on_cancel", "copy_existing"),
    note="QUOTED cancellation changes nothing. Separately, an obligation is"
         " released prospectively: new code omits note(), existing code keeps it.",
)

C4 = Block(
    id="C4", family="cancel", precedent="raise",
    history=(
        Event("c4a", GLOBAL_RAISE, "set", "*", None, "raise"),
        Event("c4b", "Change of plan across the package: a missing entry comes"
                     " back as None.",
              "replace", "*", None, "none"),
        Event("c4c", "Cancel the package-wide None rule. We're not specifying"
                     " missing-entry behaviour globally any more; fall back to"
                     " what the package documents.",
              "cancel", "*"),
        Event("c4d", "compat.py keeps returning None for a missing entry.",
              "set", "compat", None, "none"),
    ),
    cases=(_case("core", "lookup"), _case("compat", "bulk")),
    defeats=("always_newest", "always_oldest", "flip_on_cancel", "copy_existing",
             "recency_general"),
    note="Cancelling a REPLACEMENT does not revive what it replaced: core falls to"
         " the documented baseline (DEFAULT), not back to raise.",
)

# --------------------------------------------------------------- family R
# Express reinstatement by reference, with an unrelated obligation and an
# unrelated narrower rule that must survive it.

R1 = Block(
    id="R1", family="restore", precedent="none",
    history=(
        Event("r1a", GLOBAL_RAISE, "set", "*", None, "raise"),
        Event("r1b", "Change of plan: missing entries come back as None across the"
                     " package.",
              "replace", "*", None, "none"),
        Event("r1c", NOTE_RULE, "obligate", "*", name="note"),
        Event("r1d", "Go back to the missing-entry behaviour we had before that"
                     " change.",
              "reinstate", ref="r1a"),
        Event("r1e", "The legacy corner of compat is the exception: a missing"
                     " entry there comes back as DEFAULT.",
              "set", "compat.legacy", None, "default"),
    ),
    cases=(_case("core", "lookup"), _case("compat.legacy", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "rollback",
             "recency_general"),
    note="Reinstatement names no value. The note() obligation added in between"
         " has independent support and survives the restoration.",
)

R2 = Block(
    id="R2", family="restore", precedent="default",
    history=(
        Event("r2a", GLOBAL_DEFAULT, "set", "*", None, "default"),
        Event("r2b", "Change of plan: a missing entry must raise MissingEntry"
                     " across the package.",
              "replace", "*", None, "raise"),
        Event("r2c", "Inside compat.py a missing entry comes back as None.",
              "set", "compat", None, "none"),
        Event("r2d", NOTE_RULE, "obligate", "*", name="note"),
        Event("r2e", "Put the package-wide missing-entry rule back to what it was"
                     " before we switched to raising.",
              "reinstate", ref="r2a"),
    ),
    cases=(_case("core", "lookup"), _case("compat", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "rollback"),
    note="Restoring the GLOBAL rule leaves the narrower compat rule, established"
         " after it, in force.",
)

R3 = Block(
    id="R3", family="restore", precedent="default",
    history=(
        Event("r3a", GLOBAL_RAISE, "set", "*", None, "raise"),
        Event("r3b", "Inside compat.py a missing entry comes back as None.",
              "set", "compat", None, "none"),
        Event("r3c", NOTE_RULE, "obligate", "compat", name="note"),
        Event("r3d", "Drop the compat exception.", "cancel", "compat"),
        Event("r3e", "The legacy corner of compat needs its own rule: a missing"
                     " entry there comes back as DEFAULT.",
              "set", "compat.legacy", None, "default"),
        Event("r3f", "Bring back the compat missing-entry rule we dropped.",
              "reinstate", ref="r3b"),
    ),
    cases=(_case("compat", "lookup"), _case("compat.legacy", "lookup")),
    defeats=("always_newest", "always_oldest", "flip_on_cancel", "copy_existing",
             "rollback"),
    note="Cancelling the compat POLICY never dropped the compat OBLIGATION;"
         " reinstating the policy does not disturb the deeper legacy rule.",
)

# --------------------------------------------------------------- family D
# The applicable rule is far away and never superseded; the nearest
# policy-shaped sentence belongs to another part of the product.

CLI_DECOY = "For the CLI, when a flag is missing just print none and carry on."
DOCS_DECOY = "In the docs, describe the fallback as DEFAULT so the table in the" \
             " README matches the code."

D1 = Block(
    id="D1", family="distance", precedent="none",
    history=(
        Event("d1a", "Inside compat.py, missing entries come back as None.",
              "set", "compat", None, "none"),
        Event("d1b", "Across the package a lookup for a key that isn't in the"
                     " table must raise MissingEntry. compat.py keeps the rule it"
                     " already has; this is for the rest of the package.",
              "set", "*", None, "raise"),
        Event("d1c", "Keep the commit subject lines under seventy characters."),
        Event("d1d", "We're standardising on double quotes in this package."),
        Event("d1e", DOCS_DECOY),
        Event("d1f", "The changelog entry goes in the pull request body."),
    ),
    cases=(_case("core", "lookup"), _case("compat", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="The decoy is the nearest missing-entry sentence and belongs to the docs.",
)

D2 = Block(
    id="D2", family="distance", precedent="raise",
    history=(
        Event("d2a", GLOBAL_NONE, "set", "*", None, "none"),
        Event("d2b", "The bulk gather helpers must raise MissingEntry on a key"
                     " that isn't in the table; the reconciliation job cannot"
                     " silently skip rows.",
              "set", "*", "bulk", "raise"),
        Event("d2c", "Type annotations are optional here; don't add them just for"
                     " style."),
        Event("d2d", "Move the fixtures into tests/data so the suite stops"
                     " reaching into the package directory."),
        Event("d2e", CLI_DECOY),
        Event("d2f", "The release notes live in the milestone, not the repo."),
    ),
    cases=(_case("core", "bulk"), _case("core", "lookup")),
    defeats=("always_newest", "always_oldest", "copy_existing", "recency_general"),
    note="Both applicable rules predate four unrelated messages; the CLI decoy is"
         " the most recent sentence about something being missing.",
)

BLOCKS = (S1, S2, S3, S4, G1, G2, G3, C1, C2, C3, C4, R1, R2, R3, D1, D2)
