import os
import sys

def get_binary_path():
    """Returns the absolute path to the recorder binary."""
    # This file is at: capture_bin/videodb_capture_bin/__init__.py
    # Binary is at:  capture_bin/videodb_capture_bin/bin/recorder (or .exe)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(base_dir, "bin")

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
