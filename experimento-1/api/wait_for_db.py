#!/usr/bin/env python3
import os
import socket
import time
import sys


def wait_for(host: str, port: int, timeout: int = 2, retries: int = 30):
    for attempt in range(1, retries + 1):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                print(f"Connected to {host}:{port}")
                return 0
        except Exception as e:
            print(f"Attempt {attempt}/{retries} -- {host}:{port} not available: {e}")
            time.sleep(1)
    print(f"Timed out waiting for {host}:{port}")
    return 1


def main():
    host = os.getenv("DB_HOST", "pgpool")
    port = int(os.getenv("DB_PORT", "5432"))
    rc = wait_for(host, port)
    if rc != 0:
        print("Proceeding anyway (db still unreachable)")

    # If command-line args were provided (via Docker CMD/compose `command`),
    # execute them; otherwise default to starting gunicorn.
    argv = sys.argv[1:]
    if argv:
        print("Executing provided command:", " ".join(argv))
        os.execvp(argv[0], argv)

    args = [
        "gunicorn",
        "-w",
        os.getenv("GUNICORN_WORKERS", "4"),
        "-b",
        "0.0.0.0:5000",
        "app:app",
    ]
    print("Starting default:", " ".join(args))
    os.execvp("gunicorn", args)


if __name__ == "__main__":
    sys.exit(main())
