#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="$(python -c 'import json; print(json.load(open("custom_components/ha_inspector/manifest.json"))["version"])')"

CONST_VERSION="$(python -c 'import re, pathlib; t=pathlib.Path("custom_components/ha_inspector/const.py").read_text(); m=re.search(r"^VERSION: Final = \"([^\"]+)\"$", t, re.M); print(m.group(1) if m else "")')"

echo "== Release version =="
echo "$VERSION"

if [[ "$VERSION" != "$CONST_VERSION" ]]; then
    echo "ERROR: manifest version ($VERSION) != const version ($CONST_VERSION)"
    exit 1
fi

if ! grep -Fq "Current version: **$VERSION**" README.md; then
    echo "ERROR: README current version does not match $VERSION"
    exit 1
fi

if ! grep -Fq "Current integration version: **$VERSION**" README.md; then
    echo "ERROR: README integration version does not match $VERSION"
    exit 1
fi

if ! grep -Fq "## $VERSION" CHANGELOG.md; then
    echo "ERROR: CHANGELOG has no $VERSION entry"
    exit 1
fi

echo
echo "== Cleaning package caches =="

find custom_components/ha_inspector \
    -type d -name '__pycache__' \
    -prune -exec rm -rf {} +

find custom_components/ha_inspector \
    -type f \( -name '*.pyc' -o -name '*.pyo' \) \
    -delete

echo
echo "== Building archive =="

mkdir -p dist

ARCHIVE="dist/ha-inspector-${VERSION}.tar.gz"
rm -f "$ARCHIVE"

tar \
    --create \
    --gzip \
    --file "$ARCHIVE" \
    --directory custom_components \
    ha_inspector

echo
echo "== Validating archive =="

python -c '
import json
import sys
import tarfile

archive = sys.argv[1]
expected_version = sys.argv[2]

required = {
    "ha_inspector/__init__.py",
    "ha_inspector/config_flow.py",
    "ha_inspector/const.py",
    "ha_inspector/manifest.json",
    "ha_inspector/sensor.py",
    "ha_inspector/services.yaml",
    "ha_inspector/engine/public_api.py",
}

with tarfile.open(archive, "r:gz") as tar:
    names = set(tar.getnames())

    missing = sorted(required - names)
    if missing:
        raise SystemExit(
            "Archive missing required files: " + ", ".join(missing)
        )

    forbidden = [
        name
        for name in names
        if "__pycache__" in name
        or name.endswith((".pyc", ".pyo"))
    ]

    if forbidden:
        raise SystemExit(
            "Archive contains cache files: " + ", ".join(forbidden)
        )

    manifest_file = tar.extractfile("ha_inspector/manifest.json")
    if manifest_file is None:
        raise SystemExit("Unable to read manifest from archive")

    manifest = json.load(manifest_file)

    if manifest.get("version") != expected_version:
        raise SystemExit(
            "Archive manifest version mismatch: "
            + str(manifest.get("version"))
            + " != "
            + expected_version
        )

print("archive validation: OK")
' "$ARCHIVE" "$VERSION"

echo
echo "== Archive =="
ls -lh "$ARCHIVE"
