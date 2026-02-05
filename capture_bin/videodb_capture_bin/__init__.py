import os
import sys
import platform


def _get_platform_folder():
    """Returns the platform-specific folder name."""
    if sys.platform == "win32":
        return "win_amd64"
    elif sys.platform == "darwin":
        machine = platform.machine()
        if machine == "arm64":
            return "darwin_arm64"
        else:
            return "darwin_x86_64"
    else:
        # Linux
        machine = platform.machine()
        if machine == "aarch64":
            return "linux_arm64"
        else:
            return "linux_x86_64"


def get_binary_path():
    """Returns the absolute path to the recorder binary."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    platform_folder = _get_platform_folder()
    bin_dir = os.path.join(base_dir, "bin", platform_folder)

    if sys.platform == "win32":
        binary_name = "recorder.exe"
    else:
        binary_name = "recorder"

    binary_path = os.path.join(bin_dir, binary_name)

    if not os.path.exists(binary_path):
        raise FileNotFoundError(
            f"Recorder binary not found at {binary_path}. "
            "Please ensure the package was installed correctly for your platform."
        )

    return binary_path
