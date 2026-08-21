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
import pathlib
import sys
import tarfile

archive = pathlib.Path(sys.argv[1])
expected_version = sys.argv[2]
source_root = pathlib.Path("custom_components/ha_inspector")

required = {
    "ha_inspector/__init__.py",
    "ha_inspector/config_flow.py",
    "ha_inspector/const.py",
    "ha_inspector/manifest.json",
    "ha_inspector/sensor.py",
    "ha_inspector/services.yaml",
    "ha_inspector/engine/public_api.py",
}

forbidden_parts = {
    "__pycache__",
    ".git",
    ".venv",
    "dist",
    "test",
    "tests",
}

with tarfile.open(archive, "r:gz") as tar:
    members = tar.getmembers()
    names = {member.name for member in members}

    missing = sorted(required - names)
    if missing:
        raise SystemExit(
            "Archive missing required files: " + ", ".join(missing)
        )

    forbidden = sorted(
        member.name
        for member in members
        if (
            any(part in forbidden_parts for part in pathlib.PurePosixPath(member.name).parts)
            or member.name.endswith((".pyc", ".pyo"))
        )
    )

    if forbidden:
        raise SystemExit(
            "Archive contains forbidden files: " + ", ".join(forbidden)
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

    source_files = {
        path.relative_to(source_root).as_posix(): path
        for path in source_root.rglob("*")
        if path.is_file()
    }

    archive_files = {
        pathlib.PurePosixPath(member.name).relative_to("ha_inspector").as_posix(): member
        for member in members
        if member.isfile()
        and pathlib.PurePosixPath(member.name).parts
        and pathlib.PurePosixPath(member.name).parts[0] == "ha_inspector"
    }

    source_names = set(source_files)
    archive_names = set(archive_files)

    missing_from_archive = sorted(source_names - archive_names)
    extra_in_archive = sorted(archive_names - source_names)

    if missing_from_archive:
        raise SystemExit(
            "Archive missing source files: "
            + ", ".join(missing_from_archive)
        )

    if extra_in_archive:
        raise SystemExit(
            "Archive contains unexpected files: "
            + ", ".join(extra_in_archive)
        )

    mismatched = []

    for relative_name, source_path in source_files.items():
        archived = tar.extractfile(archive_files[relative_name])
        if archived is None:
            mismatched.append(relative_name)
            continue

        if archived.read() != source_path.read_bytes():
            mismatched.append(relative_name)

    if mismatched:
        raise SystemExit(
            "Archive content differs from source: "
            + ", ".join(sorted(mismatched))
        )

print("archive validation: OK")
print(f"archive/source integrity: OK ({len(source_files)} files)")
' "$ARCHIVE" "$VERSION"

echo
echo "== Archive =="
ls -lh "$ARCHIVE"
