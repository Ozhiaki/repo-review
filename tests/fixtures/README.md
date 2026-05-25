# Fixture Provenance

These fixtures support the initial repo-review validators and CLI tests.

No historical repo-review self-review outputs were present in the repository when these fixtures were added. The fixtures are therefore purpose-built from the current prompt contracts and the calibration artifacts under `reviews/repo-review/calibration-2026-05-25/`.

## Pass Frontmatter

- `pass-frontmatter/valid-pass.md` is a minimal valid prompt frontmatter block derived from the required keys used by `01-first-read.md`.
- `pass-frontmatter/invalid-pass.md` intentionally uses malformed values to exercise actionable linter errors.

Validation commands:

```bash
python3 tools/lint_pass_frontmatter.py tests/fixtures/pass-frontmatter/valid-pass.md
python3 tools/lint_pass_frontmatter.py tests/fixtures/pass-frontmatter/invalid-pass.md
```

The second command should fail.

## Pass Output

- `pass-output/first-read-valid.md` is a compact valid `first-read` structured appendix based on the output contract in `01-first-read.md`.
- `pass-output/first-read-invalid.md` intentionally omits required fields and uses invalid enum values.

Validation commands:

```bash
python3 tools/validate_pass_output.py tests/fixtures/pass-output/first-read-valid.md --pass-id first-read
python3 tools/validate_pass_output.py tests/fixtures/pass-output/first-read-invalid.md --pass-id first-read
```

The second command should fail.

## Update Guidance

When real self-review outputs are added, prefer replacing or supplementing the purpose-built fixtures with trimmed real artifacts. Keep at least one valid and one invalid fixture for each validator path, and document which source artifact each fixture came from.
