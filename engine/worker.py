import subprocess
from PySide6.QtCore import QThread, Signal

class Worker(QThread):
    log = Signal(str)
    completed = Signal(bool, str)

    def __init__(self, commands: list[str], action: str):
        super().__init__()
        self.commands = commands
        self.action = action

    def run(self) -> None:
        for command in self.commands:
            self.log.emit(f"\n$ {command}\n")
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True,
                executable="/bin/bash", bufsize=1,
            )
            if process.stdout is not None:
                for line in process.stdout:
                    self.log.emit(line)
            code = process.wait()
            if code != 0:
                self.log.emit(f"\nERROR: command failed with exit code {code}\n")
                self.completed.emit(False, self.action)
                return
        self.log.emit("\nDONE.\n")
        self.completed.emit(True, self.action)
