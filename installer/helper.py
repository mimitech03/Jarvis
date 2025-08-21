import os
import sys
import shutil
import time
import subprocess
from threading import Thread
from tempfile import NamedTemporaryFile
from unix_windows import IS_WIN

SUPPORTED_SHELLS = ["bash", "zsh"]

debug_log = None
spinning = True


def executable_exists(name: str) -> bool:
    """Check if an executable exists in PATH."""
    binary_path = shutil.which(name)
    return binary_path is not None and os.access(binary_path, os.X_OK)


def log_init() -> None:
    """Initialize debug logging."""
    global debug_log
    debug_log = NamedTemporaryFile(delete=False, mode="w")
    print(f"Logging to {debug_log.name}")


def log_close() -> None:
    """Close debug log."""
    if debug_log:
        debug_log.close()


def fail(msg: str, fatal: bool = False) -> None:
    """Handle installation failure."""
    log("Installation failed")
    log(msg)
    print(msg, "\n")

    if fatal:
        log("FATAL!")
        print("Installation failed with unexpected error - This should not have happened.")
        print(f"Please check logs at {debug_log.name}. If you open a bug report, include this file.")
    else:
        print("Installation failed!")

    log_close()
    sys.exit(1)


def log(msg: str) -> None:
    """Write message to debug log."""
    if debug_log:
        try:
            debug_log.write(msg + "\n")
        except Exception as e:
            print("Logging failed:", e)
            print("Message:", msg)


def printlog(msg: str) -> None:
    """Print and log a message."""
    log(msg)
    print(msg)


def section(title: str) -> None:
    """Print a formatted section title."""
    printlog(f"\n{title.center(50, '=')}")


def spinning_cursor_start() -> None:
    """Start a spinning cursor animation."""
    global spinning
    spinning = True

    def spin():
        while spinning:
            for cursor in "|/-\\":
                sys.stdout.write(cursor)
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write("\b")

    Thread(target=spin, daemon=True).start()


def spinning_cursor_stop() -> None:
    """Stop the spinning cursor animation."""
    global spinning
    spinning = False


def user_input(options: list[tuple[str, str]]) -> str:
    """Prompt user to select an option from a list."""
    log("User input:")
    for idx, (label, _) in enumerate(options, start=1):
        printlog(f"{idx}) {label}")

    while True:
        choice = input(f"Select number 1-{len(options)}: ")
        if choice.isdigit():
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                log(f"> User selected: {options[choice_idx][1]}")
                return options[choice_idx][1]
        log(f"> Invalid input: {choice}")


def confirm_user_input(message: str) -> bool:
    """Ask user for confirmation."""
    log("User Confirmation")
    printlog(message)
    confirm = input("Enter 'y' to confirm, 'n' to cancel: ").strip().lower()
    result = confirm in ["y", "yes"]
    log(f"> Confirmation: {'confirm' if result else 'cancel'}")
    return result


def shell(cmd: str):
    """Run a shell command and return result."""
    class Fail:
        def should_not_fail(self, msg=""):
            fail(msg, fatal=True)

        def success(self) -> bool:
            return False

        def __str__(self):
            return f"Fail {self.exception}"

    class Success:
        def should_not_fail(self, msg=""):
            pass

        def success(self) -> bool:
            return True

        def __str__(self):
            return "OK"

    result = Success()
    log("_" * 40)
    log(f"Shell: {cmd}")
    spinning_cursor_start()

    try:
        cli_output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        result = Fail()
        result.exception = str(e)
        cli_output = e.output

    result.cli_output = cli_output
    log(cli_output)
    log(f"Shell: Exit {result}")
    log("-" * 40)

    spinning_cursor_stop()
    time.sleep(0.3)
    sys.stdout.write(" \b")

    return result


def get_default_shell() -> str | None:
    """Return the default shell name of the current user."""
    shell_path = os.environ.get("SHELL")
    if shell_path:
        return os.path.basename(shell_path)
    return None
