# SPDX-License-Identifier: MIT
"""Check the browser endpoint and the application process; no model downloads."""
import os
from pathlib import Path
import sys
from urllib.request import urlopen


def main():
    scheme = "https" if os.getenv("SECURE_CONNECTION", "0") == "1" else "http"
    port = os.getenv("WEB_LISTENING_PORT", "5800")
    if scheme == "https":
        # Loopback readiness probe only; the base generates a self-signed cert.
        import ssl
        context = ssl._create_unverified_context()
    else:
        context = None
    with urlopen(f"{scheme}://127.0.0.1:{port}/", timeout=5, context=context) as response:
        if response.status != 200:
            raise RuntimeError(f"Web interface returned {response.status}")
    for path in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            args = path.read_bytes().split(b"\0")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if any(args[i:i + 2] == [b"-m", b"buzz"] for i in range(len(args) - 1)):
            if os.getenv('BUZZ_CONTAINER_READINESS') == '1':
                from buzz_observability import ui_ready
                if not ui_ready(int(path.parent.name))[0]:
                    raise RuntimeError('Buzz window is not ready or its event loop is unresponsive')
            return
    raise RuntimeError("Buzz application process is not running")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
