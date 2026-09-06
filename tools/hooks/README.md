# Git size guard

Enable in a checkout with `git config core.hooksPath tools/hooks` (enabled in the
pilot-4 checkout). `pre-commit` rejects added or modified staged blobs larger
than 10,000,000 bytes, inspecting the index rather than the working file.
Keep large artifacts locally and commit a path/byte-size/SHA256 manifest.
Historical large blobs are not rewritten or rejected unless newly staged.

The size-boundary and staged-versus-working-file regression is in
`tests/test_focus_pilot_amendment3.py::test_size_guard_uses_staged_blob`.
