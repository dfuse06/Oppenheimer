#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path | None = None) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"$ {printable}", flush=True)

    subprocess.run(
        command,
        cwd=cwd,
        check=True,
    )


def append_once(path: Path, line: str) -> None:
    content = path.read_text(encoding="utf-8")

    if line in content:
        return

    with path.open("a", encoding="utf-8") as handle:
        if content and not content.endswith("\n"):
            handle.write("\n")
        handle.write(line + "\n")


def insert_before_endmenu(path: Path, line: str) -> None:
    content = path.read_text(encoding="utf-8")

    if line in content:
        return

    lines = content.splitlines()
    insert_at = None

    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip() == "endmenu":
            insert_at = index
            break

    if insert_at is None:
        lines.append(line)
    else:
        lines.insert(insert_at, line)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply the DFUSE Razer HID driver to a Linux kernel tree."
    )

    parser.add_argument(
        "--kernel-src",
        required=True,
        help="Path to the Linux kernel source tree.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    package_dir = Path(__file__).resolve().parent
    metadata_file = package_dir / "metadata.json"

    if not metadata_file.is_file():
        print(f"ERROR: Metadata missing: {metadata_file}")
        return 1

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

    kernel_src = Path(args.kernel_src).expanduser().resolve()
    driver_src = package_dir / metadata.get("driver_dir", "driver")
    destination = metadata.get(
        "destination",
        "drivers/hid/hid-razer",
    )
    driver_dst = kernel_src / destination

    required_kernel_files = [
        kernel_src / "Makefile",
        kernel_src / "Kconfig",
        kernel_src / "scripts/config",
        kernel_src / "drivers/hid/Makefile",
        kernel_src / "drivers/hid/Kconfig",
    ]

    for required_file in required_kernel_files:
        if not required_file.exists():
            print(f"ERROR: Invalid kernel source tree. Missing: {required_file}")
            return 1

    required_driver_files = [
        driver_src / "Kconfig",
        driver_src / "Makefile",
        driver_src / "razer-dfuse-main.c",
        driver_src / "razerkbd_driver.c",
        driver_src / "razermouse_driver.c",
    ]

    for required_file in required_driver_files:
        if not required_file.exists():
            print(f"ERROR: Driver package is incomplete. Missing: {required_file}")
            return 1

    print("==> Applying DFUSE Razer HID driver", flush=True)
    print(f"Kernel source: {kernel_src}", flush=True)
    print(f"Driver source: {driver_src}", flush=True)
    print(f"Destination:   {driver_dst}", flush=True)

    if driver_dst.exists():
        shutil.rmtree(driver_dst)

    shutil.copytree(
        driver_src,
        driver_dst,
        ignore=shutil.ignore_patterns(
            "*.o",
            "*.ko",
            "*.mod",
            "*.mod.c",
            "*.cmd",
            "Module.symvers",
            "modules.order",
            "__pycache__",
        ),
    )

    hid_makefile = kernel_src / "drivers/hid/Makefile"
    hid_kconfig = kernel_src / "drivers/hid/Kconfig"

    append_once(
        hid_makefile,
        "obj-$(CONFIG_HID_RAZER_DFUSE) += hid-razer/",
    )

    insert_before_endmenu(
        hid_kconfig,
        'source "drivers/hid/hid-razer/Kconfig"',
    )

    config_symbol = metadata.get("config", "HID_RAZER_DFUSE")
    replaced_symbol = metadata.get("replaces", "HID_RAZER")

    run(
        ["scripts/config", "--disable", replaced_symbol],
        cwd=kernel_src,
    )

    run(
        ["scripts/config", "--module", config_symbol],
        cwd=kernel_src,
    )

    run(
        ["make", "olddefconfig"],
        cwd=kernel_src,
    )

    config_text = (kernel_src / ".config").read_text(encoding="utf-8")

    expected = f"CONFIG_{config_symbol}=m"
    disabled = f"# CONFIG_{replaced_symbol} is not set"

    if expected not in config_text:
        print(f"ERROR: Expected configuration missing: {expected}")
        return 1

    if disabled not in config_text:
        print(f"ERROR: Stock driver was not disabled: {disabled}")
        return 1

    print("==> Driver verification", flush=True)
    print(expected, flush=True)
    print(disabled, flush=True)
    print("==> DFUSE Razer HID driver applied successfully.", flush=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(
            f"ERROR: Command failed with exit code {error.returncode}",
            file=sys.stderr,
        )
        raise SystemExit(error.returncode)
