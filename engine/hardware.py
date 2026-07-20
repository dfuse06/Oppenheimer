"""Hardware detection and hardware-tailored kernel configuration.

Detection runs entirely with unprivileged, read-only userspace tools
(`lspci`, `lsusb`, `/proc/cpuinfo`, `/sys`) and never touches the kernel
workspace. The resulting `HardwareProfile` is then turned into a list of
`scripts/config` shell commands that are purely additive (enable/module
only) so an incomplete detection can only skip an optimization - it can
never disable something the machine actually needs to boot.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


def quote(value: object) -> str:
    """Return a safely shell-quoted value."""
    return shlex.quote(str(value))


def _run(command: list[str]) -> str:
    """Run a read-only detection command, returning stdout (empty on failure)."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


@dataclass
class HardwareProfile:
    """A snapshot of the detected hardware on the running machine."""

    cpu_vendor: str = "unknown"
    cpu_model: str = ""
    cpu_threads: int = 1
    gpu_vendors: set[str] = field(default_factory=set)
    network_chipsets: set[str] = field(default_factory=set)
    has_nvme: bool = False
    has_sata: bool = False
    has_bluetooth: bool = False
    is_virtual_machine: bool = False
    is_efi: bool = False


# Kconfig options enabled per detected feature.
CPU_MICROCODE_OPTIONS = {
    "intel": ["MICROCODE_INTEL"],
    "amd": ["MICROCODE_AMD"],
}

GPU_MODULE_OPTIONS = {
    "nvidia": ["DRM_NOUVEAU"],
    "amd": ["DRM_AMDGPU"],
    "intel": ["DRM_I915"],
}

NETWORK_MODULE_OPTIONS = {
    "iwlwifi": ["IWLWIFI", "IWLMVM"],
    "rtw88": ["RTW88", "RTW88_PCI"],
    "rtl8xxxu": ["RTL8XXXU"],
    "brcmfmac": ["BRCMFMAC"],
    "mt76": ["MT76_CORE", "MT7921E"],
    "r8169": ["R8169"],
    "e1000e": ["E1000E"],
    "tg3": ["TIGON3"],
    "virtio_net": ["VIRTIO_NET"],
}

STORAGE_OPTIONS = {
    "nvme": ["BLK_DEV_NVME"],
    "sata": ["SATA_AHCI"],
    "virtio": ["VIRTIO_BLK", "VIRTIO_PCI"],
}

BLUETOOTH_OPTIONS = ["BT", "BT_HCIBTUSB"]


def detect_hardware() -> HardwareProfile:
    """Probe the local machine's hardware using standard userspace tools."""

    profile = HardwareProfile()
    profile.cpu_threads = os.cpu_count() or 1

    cpuinfo = _run(["cat", "/proc/cpuinfo"])
    vendor_match = re.search(r"vendor_id\s*:\s*(\S+)", cpuinfo)
    model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo)
    if vendor_match:
        vendor = vendor_match.group(1)
        if vendor == "GenuineIntel":
            profile.cpu_vendor = "intel"
        elif vendor == "AuthenticAMD":
            profile.cpu_vendor = "amd"
        else:
            profile.cpu_vendor = vendor.lower()
    if model_match:
        profile.cpu_model = model_match.group(1).strip()
    profile.is_virtual_machine = "hypervisor" in cpuinfo

    lspci = _run(["lspci", "-nnk"])
    for line in lspci.splitlines():
        lower_line = line.lower()
        if "vga compatible controller" in lower_line or "3d controller" in lower_line:
            if "nvidia" in lower_line:
                profile.gpu_vendors.add("nvidia")
            elif "amd" in lower_line or "ati" in lower_line:
                profile.gpu_vendors.add("amd")
            elif "intel" in lower_line:
                profile.gpu_vendors.add("intel")
        if "network controller" in lower_line:
            if "intel" in lower_line:
                profile.network_chipsets.add("iwlwifi")
            elif "realtek" in lower_line:
                profile.network_chipsets.add("rtl8xxxu")
            elif "broadcom" in lower_line:
                profile.network_chipsets.add("brcmfmac")
            elif "mediatek" in lower_line:
                profile.network_chipsets.add("mt76")
        if "ethernet controller" in lower_line:
            if "intel" in lower_line:
                profile.network_chipsets.add("e1000e")
            elif "realtek" in lower_line:
                profile.network_chipsets.add("r8169")
            elif "broadcom" in lower_line:
                profile.network_chipsets.add("tg3")
            elif "red hat" in lower_line or "virtio" in lower_line:
                profile.network_chipsets.add("virtio_net")
        if "non-volatile memory controller" in lower_line:
            profile.has_nvme = True
        if "sata controller" in lower_line or "ahci" in lower_line:
            profile.has_sata = True
        if "bluetooth" in lower_line:
            profile.has_bluetooth = True

    if Path("/dev/nvme0").exists() or Path("/dev/nvme0n1").exists():
        profile.has_nvme = True

    usb = _run(["lsusb"])
    if "bluetooth" in usb.lower():
        profile.has_bluetooth = True

    profile.is_efi = Path("/sys/firmware/efi").is_dir()

    return profile


def format_profile_report(profile: HardwareProfile) -> str:
    """Render a human-readable summary of a detected hardware profile."""

    storage_bits = []
    if profile.has_nvme:
        storage_bits.append("NVMe")
    if profile.has_sata:
        storage_bits.append("SATA/AHCI")

    lines = [
        "== DETECTED HARDWARE ==",
        f"CPU: {profile.cpu_model or 'unknown'} "
        f"({profile.cpu_vendor}, {profile.cpu_threads} threads)",
        f"GPU vendor(s): {', '.join(sorted(profile.gpu_vendors)) or 'none detected'}",
        "Network chipset(s): "
        f"{', '.join(sorted(profile.network_chipsets)) or 'none detected'}",
        f"Storage: {', '.join(storage_bits) or 'none detected'}",
        f"Bluetooth: {'yes' if profile.has_bluetooth else 'no'}",
        f"Virtual machine: {'yes' if profile.is_virtual_machine else 'no'}",
        f"EFI firmware: {'yes' if profile.is_efi else 'no'}",
    ]
    return "\n".join(lines)


def hardware_config_commands(
    source_dir: Path,
    profile: HardwareProfile,
) -> list[str]:
    """Build additive `scripts/config` commands tailored to detected hardware.

    Every option here is enabled/built as a module - nothing is ever
    disabled - so an incomplete detection can only skip an optimization,
    never break a boot.
    """

    commands: list[str] = [
        "echo 'Tailoring kernel configuration to detected hardware...'"
    ]

    def enable(option: str) -> None:
        commands.append(
            f"cd {quote(source_dir)} && scripts/config --enable {quote(option)}"
        )

    def module(option: str) -> None:
        commands.append(
            f"cd {quote(source_dir)} && scripts/config --module {quote(option)}"
        )

    for option in CPU_MICROCODE_OPTIONS.get(profile.cpu_vendor, []):
        enable(option)

    for vendor in profile.gpu_vendors:
        for option in GPU_MODULE_OPTIONS.get(vendor, []):
            module(option)

    for chipset in profile.network_chipsets:
        for option in NETWORK_MODULE_OPTIONS.get(chipset, []):
            module(option)

    if profile.has_nvme:
        for option in STORAGE_OPTIONS["nvme"]:
            enable(option)
    if profile.has_sata:
        for option in STORAGE_OPTIONS["sata"]:
            enable(option)
    if profile.is_virtual_machine:
        for option in STORAGE_OPTIONS["virtio"]:
            enable(option)
        for option in NETWORK_MODULE_OPTIONS["virtio_net"]:
            module(option)

    if profile.has_bluetooth:
        for option in BLUETOOTH_OPTIONS:
            module(option)

    return commands


def localmodconfig_commands(source_dir: Path) -> list[str]:
    """Trim modules that are not currently loaded, based on `lsmod`.

    WARNING: this can disable module support for hardware that is not
    active right now (e.g. an unplugged USB device, a second GPU). It is
    only meant to run as an explicit, opt-in step on top of the additive
    tailoring above.
    """

    lsmod_file = source_dir / ".dfuse-lsmod.txt"
    return [
        "echo 'Trimming modules not currently in use (localmodconfig)...'",
        f"lsmod > {quote(lsmod_file)}",
        (
            f"cd {quote(source_dir)} && "
            f"yes '' | make LSMOD={quote(lsmod_file)} localmodconfig"
        ),
        f"rm -f {quote(lsmod_file)}",
    ]
