# Releasing timeSpace

The ordering below is deliberate. Zenodo only archives GitHub releases created
**after** its webhook is enabled, so a release cut before Zenodo is turned on
mints no DOI.

## 0. One-time: enable Zenodo (before the first DOI release)

1. Sign in at [zenodo.org](https://zenodo.org) (GitHub SSO is fine).
2. Go to **Settings → GitHub** (`zenodo.org/account/settings/github/`) and
   **Sync now** if `MDunitz/timeSpace` is not listed.
3. Flip the toggle **ON** for `MDunitz/timeSpace`. This installs the webhook.
   Nothing is archived retroactively.

## 1. Prepare the version (a PR, merged before tagging)

1. Bump `[project].version` in `pyproject.toml`.
2. Set the same value in `CITATION.cff` `version:` and set `date-released:`
   to the planned release date. `tests/test_version_consistency.py` enforces
   that the two match.
3. Move the `## [Unreleased]` items in `CHANGELOG.md` under the new version
   heading with the date.
4. Run the gate: `black --check . && flake8 . && pytest -q`.

## 2. Cut the release (mints the DOI)

1. GitHub → **Releases → Draft a new release**.
2. **Choose a tag → type `vX.Y.Z` → "Create new tag on publish"**, target `main`.
3. Title `vX.Y.Z`; paste the CHANGELOG section as the body.
4. **Publish release.** Within ~a minute Zenodo mints a DOI and archives the
   release. A DOI badge appears on the Zenodo record.
5. Copy the **concept DOI** (the "Cite all versions" one) and paste it into the
   `identifiers:` block in `CITATION.cff` (currently commented out), then into
   `paper.md` once it exists. Commit via a follow-up PR.

## 3. Publish to PyPI (independent of the DOI)

```
python -m build
python -m twine upload dist/timespace-X.Y.Z*
```

Keeping PyPI in step with the tagged release is preferred but not a JOSS
requirement.

## Notes

- 0.1.0 was published to PyPI (2026-04-18) but has no matching public commit;
  see `CHANGELOG.md`. Do not create a retroactive `v0.1.0` tag.
- JOSS requires a Zenodo DOI, a GitHub release, and six months of public
  availability (the clock started ~2026-04-25).
