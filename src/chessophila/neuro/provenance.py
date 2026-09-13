from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


@dataclass(frozen=True, slots=True)
class UpstreamArtifact:
    path: str
    size: int
    git_blob_sha1: str


@dataclass(frozen=True, slots=True)
class UpstreamLock:
    name: str
    repository: str
    commit: str
    flywire_materialization: int
    license: str
    artifacts: tuple[UpstreamArtifact, ...]


@dataclass(frozen=True, slots=True)
class VerificationReport:
    root: Path
    commit: str
    artifacts_checked: int


class UpstreamVerificationError(RuntimeError):
    pass


def load_upstream_lock() -> UpstreamLock:
    resource = files("chessophila.neuro").joinpath("shiu_flywire_v783.json")
    raw = json.loads(resource.read_text(encoding="utf-8"))
    artifacts = tuple(UpstreamArtifact(**artifact) for artifact in raw["artifacts"])
    return UpstreamLock(
        name=raw["name"],
        repository=raw["repository"],
        commit=raw["commit"],
        flywire_materialization=int(raw["flywire_materialization"]),
        license=raw["license"],
        artifacts=artifacts,
    )


def git_blob_sha1(path: Path) -> str:
    """Return the Git blob object id for a file without invoking Git."""

    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode())
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(root: Path, artifact: UpstreamArtifact) -> str | None:
    path = root / artifact.path
    if not path.is_file():
        return f"missing {artifact.path}"
    actual_size = path.stat().st_size
    if actual_size != artifact.size:
        return f"size mismatch for {artifact.path}: expected {artifact.size}, got {actual_size}"
    actual_blob = git_blob_sha1(path)
    if actual_blob != artifact.git_blob_sha1:
        return (
            f"blob mismatch for {artifact.path}: expected {artifact.git_blob_sha1}, "
            f"got {actual_blob}"
        )
    return None


def verify_upstream(root: Path, lock: UpstreamLock | None = None) -> VerificationReport:
    """Verify that a simulator checkout exactly matches the pinned source and data files."""

    lock = lock or load_upstream_lock()
    root = root.resolve()
    if not (root / ".git").exists():
        raise UpstreamVerificationError(f"not a Git checkout: {root}")

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise UpstreamVerificationError(f"could not read upstream Git HEAD: {exc}") from exc

    commit = result.stdout.strip()
    errors: list[str] = []
    if commit != lock.commit:
        errors.append(f"commit mismatch: expected {lock.commit}, got {commit}")

    for artifact in lock.artifacts:
        error = verify_artifact(root, artifact)
        if error:
            errors.append(error)

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise UpstreamVerificationError(f"upstream verification failed:\n{details}")

    return VerificationReport(root=root, commit=commit, artifacts_checked=len(lock.artifacts))
