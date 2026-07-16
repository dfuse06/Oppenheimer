#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


PATCH_DIR = Path(__file__).resolve().parent
METADATA_FILE = PATCH_DIR / "metadata.json"


def run(command: list[str]) -> None:
    subprocess.run(
        command,
        check=True,
    )


def main() -> None:
    metadata = json.loads(
        METADATA_FILE.read_text(encoding="utf-8")
    )

    repository = metadata["repository"]
    branch = metadata.get("branch", "master")
    source_subdir = metadata["upstream_source_dir"]
    managed_files = metadata["managed_files"]
    preserve_files = set(metadata.get("preserve_files", []))

    driver_dir = PATCH_DIR / metadata["driver_dir"]
    driver_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="oppenheimer-openrazer-"
    ) as temp_dir:
        clone_dir = Path(temp_dir) / "openrazer"

        print(f"Cloning {repository}...")

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

        source_dir = clone_dir / source_subdir

        if not source_dir.is_dir():
            raise RuntimeError(
                f"Upstream source directory not found: {source_dir}"
            )

        copied = 0

        for filename in managed_files:
            if filename in preserve_files:
                raise RuntimeError(
                    f"Managed file is also marked preserved: {filename}"
                )

            source = source_dir / filename
            destination = driver_dir / filename

            if not source.is_file():
                raise RuntimeError(
                    f"Managed upstream file missing: {source}"
                )

            shutil.copy2(source, destination)
            print(f"Updated: {filename}")
            copied += 1

        print()
        print(f"Razer upstream sync complete: {copied} files updated.")
        print("DFUSE integration files were preserved.")


if __name__ == "__main__":
    main()
