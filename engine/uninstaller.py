import re
import shlex


_SAFE_KERNEL_VERSION = re.compile(r"^[A-Za-z0-9._+-]+$")


def quote(value: object) -> str:
    return shlex.quote(str(value))


def uninstall_kernel_commands(
    kernel_version: str,
) -> list[str]:
    if not _SAFE_KERNEL_VERSION.fullmatch(kernel_version):
        raise ValueError(
            f"Unsafe kernel version: {kernel_version!r}"
        )

    script = r'''
set -euo pipefail

kernel="$1"
running_kernel="$(uname -r)"
module_dir="/usr/lib/modules/$kernel"

echo "Selected kernel: $kernel"
echo "Running kernel:  $running_kernel"

if [ "$kernel" = "$running_kernel" ]; then
    echo "ERROR: Refusing to uninstall the running kernel."
    exit 1
fi

if [ ! -d "$module_dir" ]; then
    echo "ERROR: Module directory not found: $module_dir"
    exit 1
fi

package=""

# Arch and Manjaro kernel packages normally own this file.
if [ -f "$module_dir/pkgbase" ]; then
    package="$(
        pacman -Qqo "$module_dir/pkgbase" 2>/dev/null |
        grep -v -- '-headers$' |
        head -n 1 ||
        true
    )"
fi

# Fallback: inspect packaged module files, excluding header trees.
if [ -z "$package" ]; then
    package="$(
        find "$module_dir" \
            -type f \
            ! -path '*/build/*' \
            ! -path '*/source/*' \
            -print0 |
        xargs -0 -r pacman -Qqo 2>/dev/null |
        grep -v -- '-headers$' |
        sort -u |
        head -n 1 ||
        true
    )"
fi

if [ -n "$package" ]; then
    echo "Package-managed kernel detected."
    echo "Kernel package: $package"

    pacman -Rns --noconfirm "$package"
else
    echo "Manually installed kernel detected."
    echo "Removing exact files for: $kernel"

    rm -rf -- "$module_dir"

    for boot_file in \
        "/boot/vmlinuz-$kernel" \
        "/boot/initramfs-$kernel.img" \
        "/boot/initramfs-$kernel-fallback.img" \
        "/boot/System.map-$kernel" \
        "/boot/config-$kernel"
    do
        if [ -e "$boot_file" ]; then
            echo "Removing $boot_file"
            rm -f -- "$boot_file"
        fi
    done
fi

if command -v grub-mkconfig >/dev/null 2>&1; then
    echo "Rebuilding GRUB configuration..."
    grub-mkconfig -o /boot/grub/grub.cfg
else
    echo "WARNING: grub-mkconfig was not found."
fi

echo "Kernel uninstall complete: $kernel"
'''

    return [
        "pkexec /usr/bin/bash -c "
        f"{quote(script)} _ {quote(kernel_version)}"
    ]
