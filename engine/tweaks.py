from __future__ import annotations

import re
import shlex


def quote(value: object) -> str:
    return shlex.quote(str(value))


_GOVERNORS = {"schedutil", "performance", "powersave", "ondemand", "conservative"}
_ENERGY_PREFS = {
    "balance_perf.": "balance_performance",
    "performance": "performance",
    "balance_power": "balance_power",
    "power": "power",
}
_COMPRESSIONS = {"zstd", "lz4", "lzo", "lz4hc"}
_SCHEDULERS = {"mq-deadline", "none", "kyber", "bfq"}
_DEVICE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_READ_AHEAD_RE = re.compile(r"^(\d+)\s*KB$", re.IGNORECASE)

SERVICE_PATH = "/etc/systemd/system/dfuse-tweaks.service"
SCRIPT_PATH = "/usr/local/bin/dfuse-tweaks-apply.sh"


class TweakValidationError(ValueError):
    pass


def _validate_state(state: dict) -> dict:
    governor = str(state.get("governor", ""))
    if governor not in _GOVERNORS:
        raise TweakValidationError(f"Unsupported governor: {governor!r}")

    turbo = str(state.get("turbo", ""))
    if turbo not in {"ENABLED", "DISABLED"}:
        raise TweakValidationError(f"Unsupported turbo state: {turbo!r}")

    energy = str(state.get("energy", ""))
    if energy not in _ENERGY_PREFS:
        raise TweakValidationError(f"Unsupported energy preference: {energy!r}")

    try:
        swappiness = int(state.get("swappiness", 10))
    except (TypeError, ValueError) as error:
        raise TweakValidationError("Swappiness must be an integer") from error
    if not 0 <= swappiness <= 200:
        raise TweakValidationError("Swappiness out of range")

    zram = str(state.get("zram", ""))
    if zram not in {"ENABLED", "DISABLED"}:
        raise TweakValidationError(f"Unsupported ZRAM state: {zram!r}")

    compression = str(state.get("compression", ""))
    if compression not in _COMPRESSIONS:
        raise TweakValidationError(f"Unsupported compression algorithm: {compression!r}")

    scheduler = str(state.get("scheduler", ""))
    if scheduler not in _SCHEDULERS:
        raise TweakValidationError(f"Unsupported I/O scheduler: {scheduler!r}")

    read_ahead_match = _READ_AHEAD_RE.match(str(state.get("read_ahead", "")).strip())
    if not read_ahead_match:
        raise TweakValidationError(f"Unsupported read-ahead value: {state.get('read_ahead')!r}")

    device = str(state.get("device", "/dev/sda")).strip()
    device_name = device[len("/dev/"):] if device.startswith("/dev/") else device
    if not _DEVICE_RE.fullmatch(device_name):
        raise TweakValidationError(f"Unsupported storage device: {device!r}")

    return {
        "governor": governor,
        "turbo_enabled": turbo == "ENABLED",
        "energy": _ENERGY_PREFS[energy],
        "swappiness": swappiness,
        "zram_enabled": zram == "ENABLED",
        "compression": compression,
        "scheduler": scheduler,
        "read_ahead_kb": int(read_ahead_match.group(1)),
        "device_name": device_name,
    }


_APPLY_SCRIPT_TEMPLATE = """#!/usr/bin/env bash
set -uo pipefail

GOVERNOR="$1"
ENERGY_PREF="$2"
SWAPPINESS="$3"
ZRAM_COMP="$4"
SCHEDULER="$5"
READ_AHEAD_KB="$6"
DEVICE_NAME="$7"

echo "Applying CPU governor: $GOVERNOR"
for governor_file in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor; do
    [ -e "$governor_file" ] && echo "$GOVERNOR" > "$governor_file" 2>/dev/null
done

echo "Applying turbo boost preference"
if [ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
    echo "__TURBO_INTEL__" > /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null
elif [ -f /sys/devices/system/cpu/cpufreq/boost ]; then
    echo "__TURBO_AMD__" > /sys/devices/system/cpu/cpufreq/boost 2>/dev/null
fi

echo "Applying energy performance preference: $ENERGY_PREF"
for epp_file in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/energy_performance_preference; do
    [ -e "$epp_file" ] && echo "$ENERGY_PREF" > "$epp_file" 2>/dev/null
done

echo "Applying vm.swappiness: $SWAPPINESS"
sysctl -w vm.swappiness="$SWAPPINESS" >/dev/null

echo "Applying ZRAM configuration"
__ZRAM_BLOCK__

echo "Applying I/O scheduler: $SCHEDULER for $DEVICE_NAME"
scheduler_file="/sys/block/$DEVICE_NAME/queue/scheduler"
[ -e "$scheduler_file" ] && echo "$SCHEDULER" > "$scheduler_file" 2>/dev/null

echo "Applying read-ahead: ${READ_AHEAD_KB}KB for $DEVICE_NAME"
read_ahead_file="/sys/block/$DEVICE_NAME/queue/read_ahead_kb"
[ -e "$read_ahead_file" ] && echo "$READ_AHEAD_KB" > "$read_ahead_file" 2>/dev/null

echo "Tweaks applied."
"""

_ZRAM_ENABLE_BLOCK = """modprobe zram >/dev/null 2>&1
if [ -f /sys/block/zram0/comp_algorithm ]; then
    echo "$ZRAM_COMP" > /sys/block/zram0/comp_algorithm 2>/dev/null
fi"""

_ZRAM_DISABLE_BLOCK = """swapoff /dev/zram0 >/dev/null 2>&1
if [ -f /sys/block/zram0/reset ]; then
    echo 1 > /sys/block/zram0/reset 2>/dev/null
fi"""


def _build_apply_script(values: dict) -> str:
    script = _APPLY_SCRIPT_TEMPLATE
    script = script.replace("__TURBO_INTEL__", "0" if values["turbo_enabled"] else "1")
    script = script.replace("__TURBO_AMD__", "1" if values["turbo_enabled"] else "0")
    script = script.replace(
        "__ZRAM_BLOCK__",
        _ZRAM_ENABLE_BLOCK if values["zram_enabled"] else _ZRAM_DISABLE_BLOCK,
    )
    return script


def _script_args(values: dict) -> list[str]:
    return [
        values["governor"],
        values["energy"],
        str(values["swappiness"]),
        values["compression"],
        values["scheduler"],
        str(values["read_ahead_kb"]),
        values["device_name"],
    ]


def session_commands(state: dict) -> list[str]:
    """Apply tweaks immediately to the running system (lost on reboot)."""
    values = _validate_state(state)
    script = _build_apply_script(values)
    args = " ".join(quote(arg) for arg in _script_args(values))
    return [
        f"pkexec /usr/bin/bash -c {quote(script)} _ {args}",
    ]


def permanent_commands(state: dict) -> list[str]:
    """Apply tweaks now and persist them via a systemd oneshot unit that
    re-applies them on every boot."""
    values = _validate_state(state)
    apply_script = _build_apply_script(values)
    args = " ".join(quote(arg) for arg in _script_args(values))

    unit = (
        "[Unit]\n"
        "Description=DFUSE Kernel Forge - Persisted Runtime Tweaks\n"
        "After=multi-user.target\n"
        "\n"
        "[Service]\n"
        "Type=oneshot\n"
        "RemainAfterExit=yes\n"
        f"ExecStart={SCRIPT_PATH} {args}\n"
        "\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )

    install_script = (
        "set -euo pipefail\n"
        f"cat > {SCRIPT_PATH} <<'DFUSE_TWEAKS_SCRIPT'\n"
        f"{apply_script}"
        "DFUSE_TWEAKS_SCRIPT\n"
        f"chmod 755 {SCRIPT_PATH}\n"
        f"cat > {SERVICE_PATH} <<'DFUSE_TWEAKS_UNIT'\n"
        f"{unit}"
        "DFUSE_TWEAKS_UNIT\n"
        "systemctl daemon-reload\n"
        "systemctl enable --now dfuse-tweaks.service\n"
    )

    return [
        f"pkexec /usr/bin/bash -c {quote(install_script)}",
    ]
