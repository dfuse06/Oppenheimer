#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parent
METADATA_FILE = PACKAGE_DIR / "metadata.json"


class ApplyError(RuntimeError):
    pass


def load_metadata() -> dict[str, Any]:
    if not METADATA_FILE.is_file():
        raise ApplyError(f"Missing metadata file: {METADATA_FILE}")

    return json.loads(METADATA_FILE.read_text(encoding="utf-8"))


def read_kernel_version(kernel_src: Path) -> tuple[int, int]:
    makefile = kernel_src / "Makefile"

    if not makefile.is_file():
        raise ApplyError(f"Kernel Makefile not found: {makefile}")

    text = makefile.read_text(encoding="utf-8", errors="ignore")

    version_match = re.search(r"^VERSION\s*=\s*(\d+)", text, re.MULTILINE)
    patchlevel_match = re.search(r"^PATCHLEVEL\s*=\s*(\d+)", text, re.MULTILINE)

    if not version_match or not patchlevel_match:
        raise ApplyError(
            f"Could not determine kernel VERSION/PATCHLEVEL from {makefile}"
        )

    return int(version_match.group(1)), int(patchlevel_match.group(1))


def find_patch_files(
    local_dir: Path,
    version: int,
    patchlevel: int,
) -> tuple[str, list[Path]]:
    if not local_dir.is_dir():
        raise ApplyError(
            f"No synced BORE patches found in {local_dir}. "
            "Run sync_upstream.py first (or use the UPDATE button)."
        )

    version_dir_name = f"linux-{version}.{patchlevel}-bore"
    candidates = sorted((local_dir / version_dir_name).glob("*.patch"))

    if candidates:
        return version_dir_name, candidates

    available = sorted(
        entry.name
        for entry in local_dir.iterdir()
        if entry.is_dir() and entry.name.endswith("-bore")
    )

    raise ApplyError(
        f"No BORE patch available for kernel {version}.{patchlevel}. "
        f"Available versions: {', '.join(available) or 'none'}"
    )


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    printable = " ".join(str(part) for part in command)
    print(f"$ {printable}", flush=True)

    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        check=False,
    )


def apply_patch(
    kernel_src: Path,
    version_dir_name: str,
    patch_files: list[Path],
    marker_file: Path,
) -> None:
    if marker_file.is_file():
        applied = json.loads(marker_file.read_text(encoding="utf-8"))

        if applied.get("version_dir") == version_dir_name:
            print(f"BORE patch already applied: {version_dir_name}")
            return

        raise ApplyError(
            f"A different BORE patch ({applied.get('version_dir')}) is "
            "already applied. Revert it first with --revert before "
            "applying another."
        )

    for patch_file in patch_files:
        dry_run = run(
            [
                "patch",
                "-p1",
                "--forward",
                "--fuzz=3",
                "--no-backup-if-mismatch",
                "--dry-run",
                "-i",
                str(patch_file),
            ],
            cwd=kernel_src,
        )

        if dry_run.returncode != 0:
            raise ApplyError(
                f"BORE patch {patch_file.name} does not apply cleanly to "
                f"{kernel_src}. It may not match this kernel version."
            )

    applied_files: list[str] = []

    for patch_file in patch_files:
        result = run(
            [
                "patch",
                "-p1",
                "--forward",
                "--fuzz=3",
                "--no-backup-if-mismatch",
                "-i",
                str(patch_file),
            ],
            cwd=kernel_src,
        )

        if result.returncode != 0:
            raise ApplyError(f"Failed to apply BORE patch: {patch_file.name}")

        applied_files.append(patch_file.name)

    marker_file.write_text(
        json.dumps({"version_dir": version_dir_name, "patches": applied_files}),
        encoding="utf-8",
    )
    print(f"Applied BORE patch set: {version_dir_name} ({len(applied_files)} file(s))")


def revert_patch(kernel_src: Path, local_dir: Path, marker_file: Path) -> None:
    if not marker_file.is_file():
        print("No BORE patch is currently applied; nothing to revert.")
        return

    applied = json.loads(marker_file.read_text(encoding="utf-8"))
    version_dir_name = applied.get("version_dir", "")
    applied_files = applied.get("patches", [])
    version_dir = local_dir / version_dir_name

    for filename in reversed(applied_files):
        patch_file = version_dir / filename

        if not patch_file.is_file():
            raise ApplyError(
                f"Cannot revert: original patch file not found: {patch_file}"
            )

        result = run(
            [
                "patch",
                "-R",
                "-p1",
                "--forward",
                "--fuzz=3",
                "--no-backup-if-mismatch",
                "-i",
                str(patch_file),
            ],
            cwd=kernel_src,
        )

        if result.returncode != 0:
            raise ApplyError(f"Failed to revert BORE patch: {filename}")

    marker_file.unlink()
    print(f"Reverted BORE patch set: {version_dir_name}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply (or revert) the DFUSE BORE scheduler patch on a kernel tree."
    )
    parser.add_argument(
        "--kernel-src",
        required=True,
        help="Path to the Linux kernel source tree.",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="Revert a previously applied BORE patch instead of applying one.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    try:
        metadata = load_metadata()
        kernel_src = Path(args.kernel_src).expanduser().resolve()

        if not (kernel_src / "Makefile").is_file():
            raise ApplyError(f"Kernel source tree not found: {kernel_src}")

        local_dir = PACKAGE_DIR / metadata["local_dir"]
        marker_file = kernel_src / metadata["marker_file"]

        if args.revert:
            revert_patch(kernel_src, local_dir, marker_file)
        else:
            version, patchlevel = read_kernel_version(kernel_src)
            version_dir_name, patch_files = find_patch_files(
                local_dir, version, patchlevel
            )
            apply_patch(kernel_src, version_dir_name, patch_files, marker_file)
    except ApplyError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
