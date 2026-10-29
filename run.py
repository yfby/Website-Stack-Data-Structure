"""Friendly local launcher. Opens the website once its server is ready."""

import argparse
import json
import os
import socket
import threading
import time
import urllib.request
import webbrowser


def open_when_ready(url):
    for attempt in range(40):
        try:
            with urllib.request.urlopen(url + "/health", timeout=1) as response:
                if json.load(response).get("app") == "studystack":
                    webbrowser.open(url)
                    return
        except (OSError, ValueError):
            pass
        time.sleep(0.2)


def main():
    parser = argparse.ArgumentParser(description="Start the StudyStack study planner.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")))
    parser.add_argument("--no-browser", action="store_true", help="Keep the browser closed.")
    arguments = parser.parse_args()
    if not 1024 <= arguments.port <= 65535:
        parser.error("Choose a port between 1024 and 65535.")
    url = "http://127.0.0.1:" + str(arguments.port)
    try:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", arguments.port))
    except OSError:
        print("\nPort " + str(arguments.port) + " is already in use.")
        print("Close the other server, or run: python run.py --port 5001")
        return 1

    from backend.app import create_app
    app = create_app()
    print("\nSTUDYSTACK IS STARTING")
    print("Open: " + url)
    print("Frontend: frontend/templates/ and frontend/static/")
    print("Backend:  backend/app.py | LIFO stack: backend/stack.py")
    print("Database: " + app.config["DATABASE"])
    print("Keep this window open. Press Ctrl+C to stop.")
    print("After changing Python code, stop and restart the server.\n")
    if not arguments.no_browser and os.environ.get("NO_BROWSER") != "1":
        threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    app.run(host="127.0.0.1", port=arguments.port, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
