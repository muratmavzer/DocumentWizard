from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
URL = os.getenv("BELGEIZ_URL", "http://127.0.0.1:8501")


def open_browser() -> None:
    time.sleep(1.5)
    webbrowser.open(URL)


def main() -> int:
    os.chdir(ROOT)
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    if os.getenv("BELGEIZ_NO_BROWSER") != "1":
        threading.Thread(target=open_browser, daemon=True).start()

    print()
    print("  Belgeİz başlatılıyor…")
    print(f"  Adres: {URL}")
    print("  Kapatmak için bu pencerede Ctrl+C kullanın.")
    print()

    from streamlit.web import cli as streamlit_cli

    sys.argv = [
        "streamlit",
        "run",
        str(ROOT / "app.py"),
        "--server.address=127.0.0.1",
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
    ]
    return int(streamlit_cli.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())

