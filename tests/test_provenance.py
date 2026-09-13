import hashlib
from pathlib import Path

from chessophila.neuro.provenance import (
    UpstreamArtifact,
    git_blob_sha1,
    load_upstream_lock,
    verify_artifact,
)


def expected_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def test_pinned_upstream_identity_is_explicit() -> None:
    lock = load_upstream_lock()

    assert lock.repository == "https://github.com/philshiu/Drosophila_brain_model.git"
    assert lock.commit == "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"
    assert lock.flywire_materialization == 783
    assert {artifact.path for artifact in lock.artifacts} == {
        "model.py",
        "Completeness_783.csv",
        "Connectivity_783.parquet",
        "environment.yml",
    }


def test_git_blob_hash_matches_git_object_format(tmp_path: Path) -> None:
    data = b"connectome-test\n"
    path = tmp_path / "artifact.bin"
    path.write_bytes(data)

    assert git_blob_sha1(path) == expected_blob(data)


def test_artifact_verification_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "model.py"
    original = b"print('fly')\n"
    path.write_bytes(original)
    artifact = UpstreamArtifact(
        path="model.py",
        size=len(original),
        git_blob_sha1=expected_blob(original),
    )

    assert verify_artifact(tmp_path, artifact) is None

    path.write_bytes(b"print('not the pinned model')\n")
    assert verify_artifact(tmp_path, artifact) is not None
