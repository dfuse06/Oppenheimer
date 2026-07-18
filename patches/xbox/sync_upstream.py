#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


PATCH_DIR = Path(__file__).resolve().parent
METADATA_FILE = PATCH_DIR / "metadata.json"


class SyncError(RuntimeError):
    pass


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command))

    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise SyncError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(command)}"
        )


def load_metadata() -> dict[str, Any]:
    try:
        return json.loads(
            METADATA_FILE.read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise SyncError(
            f"Missing metadata file: {METADATA_FILE}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SyncError(
            f"Invalid JSON in {METADATA_FILE}: {exc}"
        ) from exc


def verify_managed_paths(
    upstream_dir: Path,
    managed_paths: list[str],
    source_name: str,
) -> None:
    missing = [
        path_name
        for path_name in managed_paths
        if not (upstream_dir / path_name).exists()
    ]

    if missing:
        formatted = "\n".join(
            f"  - {name}"
            for name in missing
        )

        raise SyncError(
            f"{source_name}: upstream managed paths are missing:\n"
            f"{formatted}"
        )


def copy_managed_paths(
    upstream_dir: Path,
    destination_dir: Path,
    managed_paths: list[str],
) -> None:
    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for path_name in managed_paths:
        source = upstream_dir / path_name
        destination = destination_dir / path_name

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if destination.is_dir():
            shutil.rmtree(destination)
        elif destination.exists():
            destination.unlink()

        if source.is_dir():
            shutil.copytree(
                source,
                destination,
            )
        else:
            shutil.copy2(
                source,
                destination,
            )

        print(
            f"Updated: {destination.relative_to(PATCH_DIR)}"
        )


def copy_source_tree(
    upstream_dir: Path,
    destination_dir: Path,
    preserve_files: list[str],
) -> None:
    destination_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    preserved: dict[str, bytes] = {}

    for filename in preserve_files:
        preserved_path = destination_dir / filename

        if preserved_path.is_file():
            preserved[filename] = preserved_path.read_bytes()

    for item in destination_dir.iterdir():
        if item.name in preserve_files:
            continue

        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    for source in upstream_dir.iterdir():
        if source.name in preserve_files:
            continue

        destination = destination_dir / source.name

        if source.is_dir():
            shutil.copytree(
                source,
                destination,
            )
        else:
            shutil.copy2(
                source,
                destination,
            )

        print(
            f"Updated: {destination.relative_to(PATCH_DIR)}"
        )

    for filename, contents in preserved.items():
        preserved_path = destination_dir / filename

        preserved_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        preserved_path.write_bytes(contents)

        print(
            f"Preserved: {preserved_path.relative_to(PATCH_DIR)}"
        )


def sync_source(
    source: dict[str, Any],
    temporary_root: Path,
) -> None:
    source_id = source["id"]
    source_name = source.get("name", source_id)
    repository = source["repository"]
    branch = source.get("branch", "master")
    upstream_source_dir = source.get(
        "upstream_source_dir",
        ".",
    )
    local_dir = source["local_dir"]

    clone_dir = temporary_root / source_id
    destination_dir = (
        PATCH_DIR
        / "driver"
        / local_dir
    )

    print()
    print(f"=== Syncing {source_name} ===")
    print(f"Repository: {repository}")
    print(f"Branch: {branch}")

    run(
        [
            "git",
            "clone",
            "--depth=1",
            "--branch",
            branch,
            repository,
            str(clone_dir),
        ]
    )

    upstream_dir = (
        clone_dir
        / upstream_source_dir
    ).resolve()

    if not upstream_dir.is_dir():
        raise SyncError(
            f"{source_name}: upstream source directory "
            f"does not exist: {upstream_source_dir}"
        )

    managed_files = source.get(
        "managed_files",
        [],
    )
    preserve_files = source.get(
        "preserve_files",
        [],
    )

    if managed_files:
        verify_managed_paths(
            upstream_dir,
            managed_files,
            source_name,
        )

        copy_managed_paths(
            upstream_dir,
            destination_dir,
            managed_files,
        )
    else:
        copy_source_tree(
            upstream_dir,
            destination_dir,
            preserve_files,
        )

    print(f"{source_name}: synchronization complete")


def main() -> int:
    metadata = load_metadata()
    sources = metadata.get("sources")

    if not isinstance(sources, list) or not sources:
        raise SyncError(
            "metadata.json does not contain a valid sources list"
        )

    with tempfile.TemporaryDirectory(
        prefix="oppenheimer-xbox-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)

        for source in sources:
            sync_source(
                source,
                temporary_root,
            )

    print()
    print(
        f"Successfully synchronized "
        f"{len(sources)} Xbox driver sources."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
