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


def sync() -> None:
    metadata = load_metadata()

    repository = metadata["repository"]
    branch = metadata.get("branch", "main")
    upstream_patch_root = metadata["upstream_patch_root"]
    local_dir = metadata["local_dir"]

    destination_dir = PATCH_DIR / local_dir

    with tempfile.TemporaryDirectory(prefix="dfuse-bore-") as temporary_root:
        clone_dir = Path(temporary_root) / "bore-scheduler"

        run(
            [
                "git",
                "clone",
                "--depth=1",
                f"--branch={branch}",
                repository,
                str(clone_dir),
            ]
        )

        upstream_dir = clone_dir / upstream_patch_root

        if not upstream_dir.is_dir():
            raise SyncError(
                f"Upstream patch directory not found in clone: "
                f"{upstream_patch_root}"
            )

        if destination_dir.exists():
            shutil.rmtree(destination_dir)

        shutil.copytree(upstream_dir, destination_dir)

    patch_files = sorted(destination_dir.rglob("*.patch"))

    if not patch_files:
        raise SyncError(
            f"No patch files were found after sync in: {destination_dir}"
        )

    print(f"Synced {len(patch_files)} BORE patch file(s):")

    for patch_file in patch_files:
        print(f"  - {patch_file.relative_to(PATCH_DIR)}")


def main() -> int:
    try:
        sync()
    except SyncError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
