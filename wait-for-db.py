#!/usr/bin/env python
import socket
import time
import sys
import os


def wait_for_port(port, host="localhost", timeout=30.0):
    """Wait until a port starts accepting TCP connections.
    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (float): In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connections after time specified in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    "Waited too long for the port {} on host {} to start accepting "
                    "connections.".format(port, host)
                ) from ex


if __name__ == "__main__":
    # Get database host and port from environment variables or use defaults
    # Updated default to "localhost" to match GitHub Actions service configuration
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = int(os.environ.get("DB_PORT", 5432))
    # Add a timeout for the database connection check
    db_timeout = float(os.environ.get("DB_TIMEOUT", 60.0))

    print(f"Waiting for database at {db_host}:{db_port} (timeout: {db_timeout}s)...")
    try:
        wait_for_port(db_port, db_host, db_timeout)
        print("Database is ready!")
    except TimeoutError as e:
        print(f"Error: {e}")
        sys.exit(1)