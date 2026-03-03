"""Cross-platform application builder using PyInstaller.

Run this script from the workspace root. It will invoke PyInstaller to
produce a single-file executable appropriate for the host OS.

Usage:
    python build.py

Requirements:
    pip install pyinstaller

On Windows the resulting .exe will be placed in `dist\PDFCompressor.exe`.
On macOS/Linux it will be `dist/PDFCompressor` and can be renamed
`PDFCompressor.app` or bundled further with tools like py2app or plat
for a native package.
"""

import os
import shutil
import subprocess
import sys


def run(cmd):
    print("running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def build():
    if shutil.which("pyinstaller") is None:
        print("PyInstaller not found; install it with `pip install pyinstaller`.")
        sys.exit(1)

    script = "main.py"
    project_name = "PDFCompressor"
    args = ["pyinstaller", "--onefile", "--noconsole", "--name", project_name, script]

    # macOS-specific adjustments could go here (codesign, icon, etc.)
    # Linux and Windows share the basic onefile invocation.

    run(args)

    print("# build complete #")
    out_path = os.path.join("dist", project_name + (".exe" if sys.platform.startswith("win") else ""))
    print(f"Executable created at: {out_path}")


if __name__ == "__main__":
    build()
