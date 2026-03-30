#!/usr/bin/env python3
"""Local dev server — serves MkDocs with live reload.

Usage:
    python serve.py
    python serve.py --port 9000

Opens http://localhost:8000 (or specified port) in your default browser.
"""
import subprocess
import sys
import webbrowser
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="Serve dreamer-sidekick docs locally")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-open", action="store_true", help="Don't open browser")
    args = parser.parse_args()

    url = f"http://localhost:{args.port}"
    print(f"Starting MkDocs server at {url}")
    print("Press Ctrl+C to stop.\n")

    if not args.no_open:
        # Give the server a moment to start before opening the browser
        def open_browser():
            time.sleep(2)
            webbrowser.open(url)

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "serve", "--dev-addr", f"0.0.0.0:{args.port}"],
            check=True,
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except FileNotFoundError:
        print("mkdocs not found. Install with: uv pip install mkdocs mkdocs-material")
        sys.exit(1)


if __name__ == "__main__":
    main()
