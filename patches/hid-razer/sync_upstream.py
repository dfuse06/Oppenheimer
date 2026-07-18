#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


PATCH_DIR = Path(__file__).resolve().parent
METADATA_FILE = PATCH_DIR / "metadata.json"


DFUSE_MODULE_LINES = {
    "razerkbd_driver.c": "module_hid_driver(razer_kbd_driver);",
    "razermouse_driver.c": "module_hid_driver(razer_mouse_driver);",
    "razeraccessory_driver.c": "module_hid_driver(razer_accessory_driver);",
    "razerkraken_driver.c": "module_hid_driver(razer_kraken_driver);",
}


def run(command: list[str]) -> None:
    subprocess.run(
        command,
        check=True,
    )


def apply_dfuse_integration(driver_dir: Path) -> int:
    patched = 0

    for filename, module_line in DFUSE_MODULE_LINES.items():
        path = driver_dir / filename

        if not path.is_file():
            print(f"DFUSE integration skipped: {filename} not downloaded")
            continue

        text = path.read_text(encoding="utf-8")

        if module_line not in text:
            raise RuntimeError(
                f"Expected upstream module declaration not found in {filename}: "
                f"{module_line}"
            )

        replacement = (
            "/* DFUSE: driver registration is handled by "
            "razer-dfuse-main.c */"
        )

        path.write_text(
            text.replace(module_line, replacement, 1),
            encoding="utf-8",
        )

        print(f"DFUSE integration applied: {filename}")
        patched += 1

    return patched


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

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(source, destination)
            print(f"Updated: {filename}")
            copied += 1

        patched = apply_dfuse_integration(driver_dir)

        print()
        print(f"Razer upstream sync complete: {copied} files updated.")
        print(f"DFUSE integration applied to {patched} driver files.")
        print("DFUSE integration files were preserved.")


if __name__ == "__main__":
    main()
