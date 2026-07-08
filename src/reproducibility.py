"""Helpers for recording reproducibility metadata for simulation runs."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
from typing import Any

from config import SimulationConfig


REPO_ROOT = Path(__file__).resolve().parents[1]


def _json_safe(value: Any) -> Any:
    """Convert configuration values into JSON-serializable objects."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _git_output(args: list[str]) -> str:
    """Return git command output, or 'unknown' when git is unavailable."""

    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

    return completed.stdout.strip()


def collect_run_metadata(
    config: SimulationConfig,
    run_name: str,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect configuration and environment details for one simulation run."""

    git_status = _git_output(["status", "--porcelain"])
    metadata = {
        "run_name": run_name,
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": _git_output(["rev-parse", "--short", "HEAD"]),
        "git_dirty": git_status not in ("", "unknown"),
        "config": _json_safe(asdict(config)),
    }
    if extra_metadata:
        metadata.update(_json_safe(extra_metadata))
    return metadata


def write_run_metadata(
    config: SimulationConfig,
    output_path: Path,
    run_name: str,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    """Write a JSON metadata file for reproducible local experiments."""

    metadata = collect_run_metadata(config, run_name, extra_metadata=extra_metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
