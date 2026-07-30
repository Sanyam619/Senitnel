# Git hygiene — environment/repo

The shipped repo (`environment/repo/`) HEAD is the **source of truth**. Fix git metadata;
**never edit tracked source files**.

## Pre-submission checklist

Run inside `environment/repo/`:

```bash
git rev-parse --verify HEAD                   # HEAD resolves
git rev-parse HEAD                            # must match base_commit_sha in task.toml
git rev-list --all --not HEAD                 # MUST be empty (no leaked commits)
git remote                                    # MUST be empty
git config --local --get-regexp '^filter\.'   # MUST be empty
git status --porcelain                        # MUST be empty
test ! -d .git/logs                           # reflog must not exist
du -sh .git | awk '{ if ($1+0 >= 100) exit 1 }'  # < 100 MB
git apply --check ../../tests/tests.patch     # from repo dir
```

Or: `./scripts/git-hygiene.sh tasks/active/<task>`

## Common issues and fixes

| Issue | Fix |
|-------|-----|
| `.git` missing from zip | Use `zip -rX` (not `-D`, not GUI compress) |
| HEAD ≠ base_commit_sha | Realign `task.toml` to HEAD (HEAD wins) OR checkout declared base |
| Commits/branches/tags beyond HEAD | Delete refs until `git rev-list --all --not HEAD` empty |
| Remote configured | `git remote remove <name>` for each |
| filter.* in config | Remove from `.git/config` |
| Dirty working tree | Commit or discard until clean |
| Reflog present | `git reflog expire --expire=now --all && git gc --prune=now`; remove `.git/logs` |
| .git > 100 MB | `git gc --aggressive`; strip blobs or fresh single-commit history |
| tests.patch won't apply | Fix HEAD/base alignment first; regenerate patch against base |

## tests.patch regeneration

```bash
cd environment/repo
git stash -u 2>/dev/null || true
git checkout "$(grep base_commit_sha ../../task.toml | sed 's/.*"\([^"]*\)".*/\1/')"
# Ensure test files are in ORIGINAL state (f2p not already baked in)
# Apply your test additions manually, then:
git add -A
git diff --cached -- <test-file-paths> > ../../tests/tests.patch
git checkout .
git apply --check ../../tests/tests.patch
```

## Never modify pass-to-pass tests

Pre-existing test files must be **byte-identical** to base commit. Add new test
functions or new files via `tests.patch` only.
