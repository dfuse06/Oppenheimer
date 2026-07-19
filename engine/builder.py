import shlex
import shutil
from pathlib import Path

from engine.verifier import verification_commands


FILESYSTEM_OPTIONS = [
    "FAT_FS",
    "VFAT_FS",
    "MSDOS_FS",
    "NLS",
    "NLS_CODEPAGE_437",
    "NLS_ISO8859_1",
]

XBOX_CONTROLLER_OPTIONS = [
    "INPUT",
    "INPUT_JOYDEV",
    "INPUT_EVDEV",
    "HID",
    "HID_GENERIC",
    "HIDRAW",
    "USB_HID",
]

XBOX_XPAD_OPTIONS = [
    "JOYSTICK_XPAD_FF",
    "JOYSTICK_XPAD_LEDS",
]


def quote(value: object) -> str:
    """Return a safely shell-quoted value."""
    return shlex.quote(str(value))


def download_commands(
    workspace_dir: Path,
    source_dir: Path,
    repository: str,
    source_type: str = "git",
    archive_url: str | None = None,
) -> list[str]:
    """Create commands for downloading the kernel source tree."""

    commands = [f"mkdir -p {quote(workspace_dir)}"]

    if source_type == "tarball" and archive_url:
        archive_name = Path(archive_url).name
        archive_path = workspace_dir / archive_name
        extracted_dir = workspace_dir / archive_name.replace('.tar.xz', '').replace('.tar.gz', '')
        commands += [
            (
                f"if [ -f {quote(source_dir / 'Makefile')} ]; then "
                "echo 'Kernel workspace already exists.'; "
                "else "
                f"rm -f {quote(archive_path)} && "
                f"curl -L --fail {quote(archive_url)} -o {quote(archive_path)} && "
                f"rm -rf {quote(source_dir)} && "
                f"mkdir -p {quote(source_dir)} && "
                f"tar -xf {quote(archive_path)} -C {quote(workspace_dir)} && "
                f"cp -a {quote(extracted_dir)}/. {quote(source_dir)} && "
                f"rm -rf {quote(extracted_dir)} {quote(archive_path)}; "
                "fi"
            ),
        ]
    else:
        commands += [
            (
                f"if [ -f {quote(source_dir / 'Makefile')} ]; then "
                "echo 'Kernel workspace already exists.'; "
                "else "
                f"git clone --depth=1 {quote(repository)} {quote(source_dir)} && "
                f"rm -rf {quote(source_dir / '.git')}; "
                "fi"
            ),
        ]

    return commands


def xbox_config_commands(
    source_dir: Path,
    apply_xbox: bool,
    xbox_apply: Path | None = None,
) -> list[str]:
    """Configure Xbox controller support in the kernel."""

    commands: list[str] = []

    if not apply_xbox:
        return [
            f"cd {quote(source_dir)} && "
            "scripts/config --disable JOYSTICK_XPAD"
        ]

    commands.append(
        "echo 'Configuring Xbox controller support...'"
    )

    for option in XBOX_CONTROLLER_OPTIONS:
        commands.append(
            f"cd {quote(source_dir)} && "
            f"scripts/config --enable {quote(option)}"
        )

    # Build the main Xbox controller driver as a module.
    commands.append(
        f"cd {quote(source_dir)} && "
        "scripts/config --module JOYSTICK_XPAD"
    )

    for option in XBOX_XPAD_OPTIONS:
        commands.append(
            f"cd {quote(source_dir)} && "
            f"scripts/config --enable {quote(option)}"
        )

    if xbox_apply is not None:
        python = shutil.which("python3") or "python3"

        commands += [
            (
                f"test -x {quote(xbox_apply)} || "
                f"(echo 'Missing Xbox apply script: "
                f"{quote(xbox_apply)}'; exit 1)"
            ),
            (
                f"{quote(python)} {quote(xbox_apply)} "
                f"--kernel-src {quote(source_dir)}"
            ),
        ]

    return commands


def xbox_verification_commands(
    source_dir: Path,
    apply_xbox: bool,
) -> list[str]:
    """Verify Xbox controller configuration before compilation."""

    if not apply_xbox:
        return [
            (
                f"cd {quote(source_dir)} && "
                "if grep -q '^CONFIG_JOYSTICK_XPAD=' .config; then "
                "echo 'WARNING: JOYSTICK_XPAD remains enabled.'; "
                "else "
                "echo 'Xbox xpad support is disabled.'; "
                "fi"
            )
        ]

    return [
        (
            f"cd {quote(source_dir)} && "
            "grep -q '^CONFIG_JOYSTICK_XPAD=m' .config || "
            "(echo 'ERROR: CONFIG_JOYSTICK_XPAD is not configured "
            "as a module.'; exit 1)"
        ),
        (
            f"cd {quote(source_dir)} && "
            "grep -q '^CONFIG_JOYSTICK_XPAD_FF=y' .config || "
            "(echo 'ERROR: Xbox force feedback is not enabled.'; "
            "exit 1)"
        ),
        (
            f"cd {quote(source_dir)} && "
            "grep -q '^CONFIG_JOYSTICK_XPAD_LEDS=y' .config || "
            "(echo 'ERROR: Xbox controller LED support is not "
            "enabled.'; exit 1)"
        ),
        (
            f"cd {quote(source_dir)} && "
            "grep -q '^CONFIG_INPUT_JOYDEV=y' .config || "
            "(echo 'ERROR: INPUT_JOYDEV is not enabled.'; exit 1)"
        ),
        (
            f"cd {quote(source_dir)} && "
            "grep -q '^CONFIG_HIDRAW=y' .config || "
            "(echo 'ERROR: HIDRAW is not enabled.'; exit 1)"
        ),
        (
            "echo 'Xbox controller configuration verified.'"
        ),
    ]


def prepare_commands(
    source_dir: Path,
    config: Path,
    local_version: str,
    apply_razer: bool,
    razer_apply: Path,
    apply_xbox: bool = False,
    xbox_apply: Path | None = None,
) -> list[str]:
    """Prepare the kernel configuration and apply optional patches."""

    commands = [
        (
            f"test -f {quote(source_dir / 'Makefile')} || "
            "(echo 'Kernel workspace is missing. "
            "Download it first.'; exit 1)"
        ),
        (
            f"test -f {quote(config)} || "
            f"(echo 'Selected config is missing: "
            f"{quote(config)}'; exit 1)"
        ),
        f"cp {quote(config)} {quote(source_dir / '.config')}",
        (
            f"cd {quote(source_dir)} && "
            f"scripts/config --set-str LOCALVERSION "
            f"{quote(local_version)}"
        ),
        (
            f"cd {quote(source_dir)} && "
            "scripts/config --disable LOCALVERSION_AUTO"
        ),
        (
            f"cd {quote(source_dir)} && "
            "scripts/config --set-str DEFAULT_HOSTNAME dfuse"
        ),
    ]

    for option in FILESYSTEM_OPTIONS:
        commands.append(
            f"cd {quote(source_dir)} && "
            f"scripts/config --enable {quote(option)}"
        )

    if apply_razer:
        python = shutil.which("python3") or "python3"

        commands += [
            (
                f"test -x {quote(razer_apply)} || "
                f"(echo 'Missing Razer apply script: "
                f"{quote(razer_apply)}'; exit 1)"
            ),
            (
                f"{quote(python)} {quote(razer_apply)} "
                f"--kernel-src {quote(source_dir)}"
            ),
        ]
    else:
        commands.append(
            f"cd {quote(source_dir)} && "
            "scripts/config --disable HID_RAZER_DFUSE"
        )

    commands += xbox_config_commands(
        source_dir=source_dir,
        apply_xbox=apply_xbox,
        xbox_apply=xbox_apply,
    )

    commands += [
        (
            f"cd {quote(source_dir)} && "
            "scripts/config --disable LOCALVERSION_AUTO"
        ),
        f"cd {quote(source_dir)} && make olddefconfig",
        (
            f"cd {quote(source_dir)} && "
            "echo 'Kernel release:' && make -s kernelrelease"
        ),
        (
            f"cd {quote(source_dir)} && "
            "grep -E "
            "'HID_RAZER|JOYSTICK_XPAD|INPUT_JOYDEV|"
            "HIDRAW|LOCALVERSION|DEFAULT_HOSTNAME|"
            "FAT_FS|VFAT_FS|EXT4_FS|EFI' "
            ".config || true"
        ),
    ]

    return commands


def compile_commands(
    source_dir: Path,
    jobs: int,
    apply_xbox: bool = False,
) -> list[str]:
    """Compile the kernel and verify its primary build artifacts."""

    commands = [
        f"cd {quote(source_dir)} && make -j{jobs}",
        (
            f"test -s "
            f"{quote(source_dir / 'arch/x86/boot/bzImage')} || "
            "(echo 'ERROR: bzImage was not created.'; exit 1)"
        ),
        (
            f"test -s {quote(source_dir / 'System.map')} || "
            "(echo 'ERROR: System.map was not created.'; exit 1)"
        ),
        (
            f"test -s {quote(source_dir / 'Module.symvers')} || "
            "(echo 'ERROR: Module.symvers was not created.'; exit 1)"
        ),
    ]

    if apply_xbox:
        commands += [
            (
                f"test -s "
                f"{quote(source_dir / 'drivers/input/joystick/xpad.ko')} "
                "|| "
                "(echo 'ERROR: Xbox xpad module was not built.'; "
                "exit 1)"
            ),
            (
                f"echo 'Xbox driver built successfully: "
                f"{quote(source_dir / 'drivers/input/joystick/xpad.ko')}'"
            ),
        ]

    commands.append(
        f"cd {quote(source_dir)} && "
        "echo 'Built kernel release:' && make -s kernelrelease"
    )

    return commands


def build_commands(
    source_dir: Path,
    mode: str,
    jobs: int,
    config: Path,
    local_version: str,
    apply_razer: bool,
    razer_apply: Path,
    apply_xbox: bool = False,
    xbox_apply: Path | None = None,
) -> list[str]:
    """Generate the full kernel build command sequence."""

    commands: list[str] = []

    if mode == "Deep Clean (mrproper)":
        commands.append(
            f"cd {quote(source_dir)} && make mrproper"
        )

        commands += prepare_commands(
            source_dir=source_dir,
            config=config,
            local_version=local_version,
            apply_razer=apply_razer,
            razer_apply=razer_apply,
            apply_xbox=apply_xbox,
            xbox_apply=xbox_apply,
        )

        commands += verification_commands(
            source_dir,
            apply_razer,
        )

        commands += xbox_verification_commands(
            source_dir,
            apply_xbox,
        )

    else:
        commands += verification_commands(
            source_dir,
            apply_razer,
        )

        commands += xbox_verification_commands(
            source_dir,
            apply_xbox,
        )

        if mode == "Clean Build":
            commands.append(
                f"cd {quote(source_dir)} && make clean"
            )

    commands += compile_commands(
        source_dir=source_dir,
        jobs=jobs,
        apply_xbox=apply_xbox,
    )

    return commands
