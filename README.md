# Pygame Zero

The project is based on:

https://github.com/lordmauve/pgzero

Build instructions:

```bash
python -m build
python -m pip install --upgrade --force-reinstall ./dist/pgzero_mjd-0.0.1-py3-none-any.whl
```

Student installation command for Windows:

```bash
python -m pip install --upgrade --force-reinstall https://github.com/mjdargen/pgzero/releases/latest/download/pgzero_mjd-0.0.1-py3-none-any.whl
```

Student installation command for Mac:

```bash
python3 -m pip install --upgrade --force-reinstall https://github.com/mjdargen/pgzero/releases/latest/download/pgzero_mjd-0.0.1-py3-none-any.whl
```

## Publishing to PyPI

Releases are automated by the GitHub Actions workflow in
`.github/workflows/publish.yml`. Students install the package with
`pip install pgzero-mjd`.

### One-time setup

1. Create a PyPI API token at https://pypi.org/manage/account/token/.
   For the very first upload the token must be scoped to your **entire
   account**, because a token scoped to one project can't create a project
   that doesn't exist on PyPI yet. After the first release you can delete it
   and make a new token scoped to just `pgzero-mjd`.
2. Add the token to this repository as an Actions secret: go to
   https://github.com/mjdargen/pgzero/settings/secrets/actions, click
   **New repository secret**, name it `PYPI_API_TOKEN`, and paste the token
   as the value.

That's all the setup there is.

### How releases happen

Every merge to `main` publishes a new **minor** version: 0.0.1 → 0.1.0 →
0.2.0 → ... The workflow works out the next version from the newest `v*` tag,
writes it into `pyproject.toml`, commits that, tags the commit (for example
`v0.1.0`), uploads the package to PyPI, and creates a GitHub Release for the
tag with the wheel and source tarball attached. You can watch it run on the
Actions tab: https://github.com/mjdargen/pgzero/actions.

### Major version bump by hand

To publish a specific version, for example `1.0.0`, push a tag with that
version number:

```bash
git checkout main
git pull
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

The tag is the version: the workflow publishes exactly `1.0.0`, creates the
GitHub Release, and records the new version in `pyproject.toml` on `main`.
The next merge to `main` continues from there (`v1.1.0`). Tagging the current
head of `main`, as above, is the normal case; a tag on an older commit is
published too, but `pyproject.toml` on `main` is then left alone.

### Publishing by hand

If GitHub Actions is ever unavailable, you can upload a release yourself from
a checkout of the version you want to publish:

```bash
python -m pip install build twine
python -m build
python -m twine upload dist/*
```

When asked to log in, the username is `__token__` and the password is the
PyPI API token. PyPI never accepts the same version number twice, so bump the
`version` line in `pyproject.toml` first if that version is already published.
