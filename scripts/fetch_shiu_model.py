#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from chessophila.neuro import load_upstream_lock, verify_upstream


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the pinned Shiu/FlyWire simulator checkout")
    parser.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=Path("vendor/drosophila_brain_model"),
    )
    args = parser.parse_args()

    lock = load_upstream_lock()
    destination = args.destination.resolve()

    if destination.exists():
        report = verify_upstream(destination, lock)
        print(f"verified existing checkout: {report.commit}")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    run(
        "git",
        "clone",
        "--filter=blob:none",
        "--no-checkout",
        lock.repository,
        str(destination),
    )
    run("git", "-C", str(destination), "sparse-checkout", "init", "--no-cone")
    run(
        "git",
        "-C",
        str(destination),
        "sparse-checkout",
        "set",
        *(artifact.path for artifact in lock.artifacts),
    )
    run("git", "-C", str(destination), "checkout", "--detach", lock.commit)

    report = verify_upstream(destination, lock)
    print(
        f"verified {report.artifacts_checked} required artifacts at "
        f"{report.root} ({report.commit})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
