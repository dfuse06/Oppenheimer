import shlex, shutil
from pathlib import Path
from engine.verifier import verification_commands

FILESYSTEM_OPTIONS = ["FAT_FS", "VFAT_FS", "MSDOS_FS", "NLS", "NLS_CODEPAGE_437", "NLS_ISO8859_1"]

def quote(value: object) -> str:
    return shlex.quote(str(value))

def download_commands(workspace_dir: Path, source_dir: Path, repository: str) -> list[str]:
    return [
        f"mkdir -p {quote(workspace_dir)}",
        f"if [ -f {quote(source_dir / 'Makefile')} ]; then "
        "echo 'Kernel workspace already exists.'; "
        "else "
        f"git clone --depth=1 {quote(repository)} {quote(source_dir)} && "
        f"rm -rf {quote(source_dir / '.git')}; fi",
    ]

def prepare_commands(source_dir: Path, config: Path, local_version: str,
                     apply_razer: bool, razer_apply: Path) -> list[str]:
    commands = [
        f"test -f {quote(source_dir / 'Makefile')} || "
        "(echo 'Kernel workspace is missing. Download it first.'; exit 1)",
        f"test -f {quote(config)} || (echo 'Selected config is missing: {quote(config)}'; exit 1)",
        f"cp {quote(config)} {quote(source_dir / '.config')}",
        f"cd {quote(source_dir)} && scripts/config --set-str LOCALVERSION {quote(local_version)}",
        f"cd {quote(source_dir)} && scripts/config --disable LOCALVERSION_AUTO",
        f"cd {quote(source_dir)} && scripts/config --set-str DEFAULT_HOSTNAME dfuse",
    ]
    for option in FILESYSTEM_OPTIONS:
        commands.append(f"cd {quote(source_dir)} && scripts/config --enable {quote(option)}")
    if apply_razer:
        py = shutil.which("python3") or "python3"
        commands += [
            f"test -x {quote(razer_apply)} || (echo 'Missing Razer apply script: {quote(razer_apply)}'; exit 1)",
            f"{quote(py)} {quote(razer_apply)} --kernel-src {quote(source_dir)}",
        ]
    else:
        commands.append(f"cd {quote(source_dir)} && scripts/config --disable HID_RAZER_DFUSE")
    commands += [
        f"cd {quote(source_dir)} && scripts/config --disable LOCALVERSION_AUTO",
        f"cd {quote(source_dir)} && make olddefconfig",
        f"cd {quote(source_dir)} && echo 'Kernel release:' && make -s kernelrelease",
        f"cd {quote(source_dir)} && grep -E 'HID_RAZER|LOCALVERSION|DEFAULT_HOSTNAME|FAT_FS|VFAT_FS|EXT4_FS|EFI' .config || true",
    ]
    return commands

def compile_commands(source_dir: Path, jobs: int) -> list[str]:
    return [
        f"cd {quote(source_dir)} && make -j{jobs}",
        f"test -s {quote(source_dir / 'arch/x86/boot/bzImage')} || (echo 'ERROR: bzImage was not created.'; exit 1)",
        f"test -s {quote(source_dir / 'System.map')} || (echo 'ERROR: System.map was not created.'; exit 1)",
        f"test -s {quote(source_dir / 'Module.symvers')} || (echo 'ERROR: Module.symvers was not created.'; exit 1)",
        f"cd {quote(source_dir)} && echo 'Built kernel release:' && make -s kernelrelease",
    ]

def build_commands(source_dir: Path, mode: str, jobs: int, config: Path,
                   local_version: str, apply_razer: bool, razer_apply: Path) -> list[str]:
    commands: list[str] = []
    if mode == "Deep Clean (mrproper)":
        commands.append(f"cd {quote(source_dir)} && make mrproper")
        commands += prepare_commands(source_dir, config, local_version, apply_razer, razer_apply)
        commands += verification_commands(source_dir, apply_razer)
    else:
        commands += verification_commands(source_dir, apply_razer)
        if mode == "Clean Build":
            commands.append(f"cd {quote(source_dir)} && make clean")
    commands += compile_commands(source_dir, jobs)
    return commands
