import shlex
from pathlib import Path

def quote(value: object) -> str:
    return shlex.quote(str(value))

def install_commands(source_dir: Path) -> list[str]:
    rf = source_dir / ".oppenheimer-kernelrelease"
    return [
        f"test -s {quote(source_dir / 'arch/x86/boot/bzImage')} || (echo 'Kernel image missing.'; exit 1)",
        f"cd {quote(source_dir)} && make -s kernelrelease | tee {quote(rf)}",
        f"release=$(cat {quote(rf)}) && echo \"Installing kernel release: $release\" && pkexec /usr/bin/make -C {quote(source_dir)} modules_install",
        f"release=$(cat {quote(rf)}) && test -d \"/usr/lib/modules/$release\" || (echo \"Module directory missing: /usr/lib/modules/$release\"; exit 1)",
        f"release=$(cat {quote(rf)}) && pkexec /usr/bin/depmod \"$release\"",
        f"release=$(cat {quote(rf)}) && pkexec /usr/bin/cp {quote(source_dir / 'arch/x86/boot/bzImage')} \"/boot/vmlinuz-$release\"",
        f"release=$(cat {quote(rf)}) && pkexec /usr/bin/cp {quote(source_dir / 'System.map')} \"/boot/System.map-$release\"",
        f"release=$(cat {quote(rf)}) && pkexec /usr/bin/cp {quote(source_dir / '.config')} \"/boot/config-$release\"",
        f"release=$(cat {quote(rf)}) && pkexec /usr/bin/mkinitcpio -k \"$release\" -g \"/boot/initramfs-$release.img\"",
        "pkexec /usr/bin/grub-mkconfig -o /boot/grub/grub.cfg",
        f"release=$(cat {quote(rf)}) && echo 'Installed release:' && echo \"$release\" && ls -ld \"/usr/lib/modules/$release\"",
    ]
