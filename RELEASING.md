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

## 0b. One-time: let GitHub publish to PyPI

`.github/workflows/release.yml` uploads to PyPI through trusted publishing,
so no token is stored anywhere. PyPI has to be told to trust this workflow:

1. On PyPI, open the `timeSpace` project → **Manage** → **Publishing** →
   **Add a new publisher** → **GitHub**.
2. Owner `MDunitz`, repository `timeSpace`, workflow `release.yml`,
   environment `pypi`.
3. On GitHub, **Settings → Environments → New environment** named `pypi`.
   Under **Deployment branches and tags**, choose **Selected branches** and
   add `prod`, so nothing else can publish. Adding yourself as a required
   reviewer makes every upload wait for one click of approval; leave it
   empty to publish as soon as the build passes.
4. Create the `prod` branch from `main` (**Branches → New branch**). Under
   **Settings → Branches** (or Rulesets), protect it so it only changes
   through pull requests from `main`.

## 1. Prepare the version (a PR into `main`)

1. Bump `[project].version` in `pyproject.toml`.
2. Set the same value in `CITATION.cff` `version:` and set `date-released:`
   to the planned release date. `tests/test_version_consistency.py` enforces
   that the two match.
3. Move the `## [Unreleased]` items in `CHANGELOG.md` under the new version
   heading with the date.
4. Run the gate: `black --check . && flake8 . && pytest -q`.

## 2. Release: open a pull request from `main` into `prod`

Merging it pushes to `prod`, which runs `.github/workflows/release.yml`
(watch it under **Actions → release**). The workflow:

1. Reads `[project].version` from `pyproject.toml`. If `vX.Y.Z` is already
   tagged it publishes nothing and stops with a warning, so a `prod` merge
   without a version bump is harmless. It fails if `CHANGELOG.md` has no
   `## [X.Y.Z]` section.
2. Runs the test suite, builds the sdist and wheel, checks them with
   `twine check --strict`, and runs `tests/test_local_install.py` against
   the wheel in a clean environment.
3. Uploads to PyPI.
4. Tags `vX.Y.Z` on the `prod` commit and publishes a GitHub release whose
   body is the CHANGELOG section. Zenodo archives that release and mints the
   DOI within about a minute.

Then copy the **concept DOI** (the "Cite all versions" one) into the
`identifiers:` block in `CITATION.cff` (currently commented out), and into
`paper.md` once it exists, through a follow-up PR to `main`.

Do not publish releases by hand from the Releases page: the tag would no
longer be the commit PyPI was built from.

PyPI versions are permanent: a version cannot be re-uploaded, even after a
deletion. If an upload fails after PyPI accepted it, bump the version rather
than retrying the same one.

Manual fallback (needs a PyPI API token):

```
python -m build
python -m twine upload dist/timespace-X.Y.Z*
```

## Notes

- 0.1.0 was published to PyPI (2026-04-18) but has no matching public commit;
  see `CHANGELOG.md`. Do not create a retroactive `v0.1.0` tag.
- JOSS requires a Zenodo DOI, a GitHub release, and six months of public
  availability (the clock started ~2026-04-25).
