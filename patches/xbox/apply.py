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
        description="Apply DFUSE Xbox controller support to a Linux kernel tree."
    )
    parser.add_argument(
        "--kernel-src",
        required=True,
        help="Path to the Linux kernel source tree.",
    )
    parser.add_argument(
        "--skip-xpad",
        action="store_true",
        help="Do not install the XPAD (USB) driver.",
    )
    parser.add_argument(
        "--skip-xpadneo",
        action="store_true",
        help="Do not install the XPADNEO (Bluetooth) driver.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    install_xpad = not args.skip_xpad
    install_xpadneo = not args.skip_xpadneo

    if not install_xpad and not install_xpadneo:
        print("ERROR: Both --skip-xpad and --skip-xpadneo were given; nothing to install.")
        return 1

    package_dir = Path(__file__).resolve().parent
    metadata_file = package_dir / "metadata.json"

    if not metadata_file.is_file():
        print(f"ERROR: Metadata missing: {metadata_file}")
        return 1

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

    kernel_src = Path(args.kernel_src).expanduser().resolve()
    driver_root = package_dir / metadata.get("driver_dir", "driver")

    required_kernel_files = [
        kernel_src / "Makefile",
        kernel_src / "Kconfig",
        kernel_src / ".config",
        kernel_src / "scripts/config",
    ]

    if install_xpad:
        required_kernel_files += [
            kernel_src / "drivers/input/joystick/Makefile",
            kernel_src / "drivers/input/joystick/Kconfig",
            kernel_src / "drivers/input/joystick/xpad.c",
        ]

    if install_xpadneo:
        required_kernel_files += [
            kernel_src / "drivers/hid/Makefile",
            kernel_src / "drivers/hid/Kconfig",
        ]

    for required_file in required_kernel_files:
        if not required_file.exists():
            print(f"ERROR: Invalid kernel source tree. Missing: {required_file}")
            return 1

    sources = metadata.get("sources", [])

    xpad_source = next(
        (source for source in sources if source.get("id") == "xpad"),
        None,
    )

    xpadneo_source = next(
        (source for source in sources if source.get("id") == "xpadneo"),
        None,
    )

    if install_xpad and xpad_source is None:
        print("ERROR: XPAD source is missing from metadata.")
        return 1

    if install_xpadneo and xpadneo_source is None:
        print("ERROR: XPADNEO source is missing from metadata.")
        return 1

    xpad_config = None

    if install_xpad:
        xpad_src = driver_root / xpad_source["local_dir"] / "xpad.c"
        xpad_dst = kernel_src / xpad_source["destination"] / "xpad.c"

        if not xpad_src.is_file():
            print(f"ERROR: XPAD source missing: {xpad_src}")
            return 1

        print("==> Installing XPAD", flush=True)
        print(f"Source:      {xpad_src}", flush=True)
        print(f"Destination: {xpad_dst}", flush=True)

        shutil.copy2(xpad_src, xpad_dst)

        xpad_config = xpad_source.get(
            "config",
            "JOYSTICK_XPAD",
        )

        run(
            ["scripts/config", "--module", xpad_config],
            cwd=kernel_src,
        )
    else:
        print("==> Skipping XPAD (not selected)", flush=True)

    xpadneo_config = None

    if install_xpadneo:
        xpadneo_src = driver_root / xpadneo_source["local_dir"] / "src"
        xpadneo_dst = kernel_src / xpadneo_source["destination"]

        required_xpadneo_files = [
            xpadneo_src / "Kconfig",
            xpadneo_src / "Makefile",
            xpadneo_src / "xpadneo" / "core.c",
            xpadneo_src / "xpadneo" / "xpadneo.h",
            xpadneo_src / "xpadneo" / "compat.h",
        ]

        for required_file in required_xpadneo_files:
            if not required_file.is_file():
                print(f"ERROR: XPADNEO source incomplete: {required_file}")
                return 1

        print("==> Installing XPADNEO", flush=True)
        print(f"Source:      {xpadneo_src}", flush=True)
        print(f"Destination: {xpadneo_dst}", flush=True)

        if xpadneo_dst.exists():
            shutil.rmtree(xpadneo_dst)

        shutil.copytree(
            xpadneo_src,
            xpadneo_dst,
            ignore=shutil.ignore_patterns(
                "AGENTS.md",
                ".editorconfig",
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

        xpadneo_config = xpadneo_source.get(
            "config",
            "HID_XPADNEO_DFUSE",
        )

        append_once(
            hid_makefile,
            f"obj-$(CONFIG_{xpadneo_config}) += hid-xpadneo/",
        )

        insert_before_endmenu(
            hid_kconfig,
            'source "drivers/hid/hid-xpadneo/Kconfig"',
        )

        run(
            ["scripts/config", "--module", xpadneo_config],
            cwd=kernel_src,
        )
    else:
        print("==> Skipping XPADNEO (not selected)", flush=True)

    run(
        ["make", "olddefconfig"],
        cwd=kernel_src,
    )

    config_text = (kernel_src / ".config").read_text(encoding="utf-8")

    print("==> Xbox driver verification", flush=True)

    if xpad_config is not None:
        expected_xpad = f"CONFIG_{xpad_config}=m"

        if expected_xpad not in config_text:
            print(f"ERROR: Missing config: {expected_xpad}")
            return 1

        print(expected_xpad, flush=True)

    if xpadneo_config is not None:
        expected_xpadneo = f"CONFIG_{xpadneo_config}=m"

        if expected_xpadneo not in config_text:
            print(f"ERROR: Missing config: {expected_xpadneo}")
            return 1

        print(expected_xpadneo, flush=True)

    print("==> DFUSE Xbox Controller Support applied successfully.", flush=True)

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
