import shlex
from pathlib import Path

BOOT_CRITICAL_OPTIONS = {
    "CONFIG_BLK_DEV_INITRD": "y",
    "CONFIG_DEVTMPFS": "y",
    "CONFIG_DEVTMPFS_MOUNT": "y",
    "CONFIG_EFI": "y",
    "CONFIG_EFI_PARTITION": "y",
    "CONFIG_EFIVAR_FS": "y",
    "CONFIG_EXT4_FS": "y",
    "CONFIG_FAT_FS": "y",
    "CONFIG_VFAT_FS": "y",
}

def quote(value: object) -> str:
    return shlex.quote(str(value))

def verification_commands(source_dir: Path, apply_razer: bool) -> list[str]:
    commands = [
        f"test -f {quote(source_dir / '.config')} || "
        "(echo 'Kernel has not been configured.'; exit 1)"
    ]
    for option, expected in BOOT_CRITICAL_OPTIONS.items():
        line = f"{option}={expected}"
        commands.append(
            f"grep -qx {quote(line)} {quote(source_dir / '.config')} || "
            f"(echo 'Missing boot-critical option: {line}'; exit 1)"
        )
    if apply_razer:
        commands += [
            f"grep -qx 'CONFIG_HID_RAZER_DFUSE=m' {quote(source_dir / '.config')} || "
            "(echo 'DFUSE Razer driver is not enabled.'; exit 1)",
            f"grep -qx '# CONFIG_HID_RAZER is not set' {quote(source_dir / '.config')} || "
            "(echo 'Stock Razer driver is still enabled.'; exit 1)",
            f"test -f {quote(source_dir / 'drivers/hid/hid-razer/Kconfig')} || "
            "(echo 'Razer Kconfig is missing from workspace.'; exit 1)",
            f"test -f {quote(source_dir / 'drivers/hid/hid-razer/Makefile')} || "
            "(echo 'Razer Makefile is missing from workspace.'; exit 1)",
        ]
    commands += [
        f"cd {quote(source_dir)} && echo 'Configuration verification passed.'",
        f"cd {quote(source_dir)} && make -s kernelrelease",
    ]
    return commands
