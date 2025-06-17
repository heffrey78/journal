#!/usr/bin/env python3
"""
Development server launcher for Llens journal application.
Runs both backend (FastAPI) and frontend (Next.js) concurrently.
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Store process references for cleanup
processes = []


def cleanup(signum=None, frame=None):
    """Clean up all running processes."""
    print(f"\n{YELLOW}Shutting down servers...{RESET}")
    for proc in processes:
        try:
            if proc.poll() is None:  # Process is still running
                proc.terminate()
                proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    print(f"{GREEN}All servers stopped.{RESET}")
    sys.exit(0)


# Register cleanup handlers
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def run_command(cmd, name, cwd=None, color=GREEN):
    """Run a command and prefix output with colored name."""
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd,
            shell=True,
        )
        processes.append(process)

        # Stream output with colored prefix
        for line in iter(process.stdout.readline, ""):
            if line:
                print(f"{color}[{name}]{RESET} {line.rstrip()}")

        process.wait()

    except Exception as e:
        print(f"{RED}[{name}] Error: {e}{RESET}")
        cleanup()


def main():
    """Main function to start both servers."""
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print(
            f"{RED}Error: main.py not found. Please run this script from the journal project root.{RESET}"
        )
        sys.exit(1)

    if not os.path.exists("journal-app-next"):
        print(f"{RED}Error: journal-app-next directory not found.{RESET}")
        sys.exit(1)

    print(f"{BLUE}Starting Llens development servers...{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")

    # Start backend in a subprocess
    print(f"{GREEN}Starting backend server on http://localhost:8000{RESET}")
    backend_proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(backend_proc)

    # Give backend a moment to start
    time.sleep(2)

    # Start frontend in a subprocess
    print(f"{GREEN}Starting frontend server on http://localhost:3000{RESET}")
    frontend_proc = subprocess.Popen(
        "npm run dev",
        shell=True,
        cwd="journal-app-next",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(frontend_proc)

    print(f"{BLUE}{'='*50}{RESET}")
    print(f"{YELLOW}Press Ctrl+C to stop all servers{RESET}\n")

    # Monitor processes and print output
    import threading

    def monitor_output(proc, name, color):
        """Monitor and print output from a process."""
        try:
            for line in iter(proc.stdout.readline, ""):
                if line:
                    print(f"{color}[{name}]{RESET} {line.rstrip()}")
        except:
            pass

    # Create threads to monitor output
    backend_thread = threading.Thread(
        target=monitor_output, args=(backend_proc, "Backend", GREEN)
    )
    frontend_thread = threading.Thread(
        target=monitor_output, args=(frontend_proc, "Frontend", BLUE)
    )

    backend_thread.start()
    frontend_thread.start()

    # Wait for processes to complete or be interrupted
    try:
        backend_thread.join()
        frontend_thread.join()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
