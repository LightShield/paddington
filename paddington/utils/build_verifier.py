"""Build verification utilities."""

import subprocess
from pathlib import Path
from .logger import Logger


def run_build_command(command: str, cwd: Path) -> bool:
    """Run build command and check if it succeeds.

    Args:
        command: Build command to execute (e.g., 'make test', 'clang++ test.cpp')
        cwd: Working directory to run command in

    Returns:
        True if build succeeded, False otherwise
    """
    log = Logger()

    log.info(f"Running build command: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            log.info("Build succeeded ✓")
            return True
        else:
            log.error(f"Build failed with exit code {result.returncode}")
            if result.stdout:
                log.error(f"stdout: {result.stdout[:500]}")
            if result.stderr:
                log.error(f"stderr: {result.stderr[:500]}")
            return False

    except subprocess.TimeoutExpired:
        log.error("Build command timed out after 300 seconds")
        return False
    except Exception as e:
        log.error(f"Error running build command: {e}")
        return False
