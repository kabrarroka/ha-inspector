#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Repository state =="

branch="$(git branch --show-current)"

if [[ -z "$branch" ]]; then
    echo "ERROR: detached HEAD is not supported"
    exit 1
fi

echo "branch: $branch"
echo "commit: $(git rev-parse --short HEAD)"

if [[ -n "$(git status --porcelain)" ]]; then
    if [[ "${REQUIRE_CLEAN_TREE:-0}" == "1" ]]; then
        echo "ERROR: working tree is not clean"
        git status --short
        exit 1
    fi

    echo "WARNING: working tree contains local changes"
    git status --short
else
    echo "working tree: clean"
fi

echo
echo "== Version consistency =="

python - <<'PYVERSION'
import json
import pathlib
import re

root = pathlib.Path(".")
manifest = json.loads(
    (root / "custom_components/ha_inspector/manifest.json").read_text()
)
version = manifest["version"]

const_text = (
    root / "custom_components/ha_inspector/const.py"
).read_text()

match = re.search(
    r'^VERSION:\s*Final\s*=\s*"([^"]+)"$',
    const_text,
    re.MULTILINE,
)

if match is None:
    raise SystemExit("ERROR: unable to read VERSION from const.py")

const_version = match.group(1)

if version != const_version:
    raise SystemExit(
        f"ERROR: manifest version {version} != const version {const_version}"
    )

readme = (root / "README.md").read_text()

for marker in (
    f"Current version: **{version}**",
    f"Current integration version: **{version}**",
):
    if marker not in readme:
        raise SystemExit(
            f"ERROR: README version marker missing: {marker}"
        )

changelog = (root / "CHANGELOG.md").read_text()

if f"## {version}" not in changelog:
    raise SystemExit(
        f"ERROR: CHANGELOG has no entry for version {version}"
    )

print(f"version: {version}")
print("version consistency: OK")
PYVERSION

echo
echo "== Public API contracts =="

python - <<'PYAPI'
from custom_components.ha_inspector.engine.capabilities import (
    CAPABILITIES_SCHEMA_VERSION,
)
from custom_components.ha_inspector.engine.public_api import (
    PUBLIC_API_VERSION,
)
from custom_components.ha_inspector.engine.result import (
    RESULT_SCHEMA_VERSION,
)

expected = {
    "public_api": 1,
    "capabilities": 1,
    "result": 2,
}

actual = {
    "public_api": PUBLIC_API_VERSION,
    "capabilities": CAPABILITIES_SCHEMA_VERSION,
    "result": RESULT_SCHEMA_VERSION,
}

if actual != expected:
    raise SystemExit(
        f"ERROR: public API contract mismatch: {actual} != {expected}"
    )

for key, value in actual.items():
    print(f"{key}: {value}")

print("public API contracts: OK")
PYAPI

echo
echo "== Ruff =="
ruff check custom_components/ha_inspector tests

echo
echo "== Mypy =="
python -m mypy

echo
echo "== Pytest and coverage =="
python -m pytest \
    --cov=custom_components.ha_inspector \
    --cov-report=term-missing \
    --cov-fail-under=100

echo
echo "== Diff check =="
git diff --check

echo
echo "== Release archive =="
scripts/build_release.sh

echo
echo "== Release validation =="
echo "release readiness validation: OK"
