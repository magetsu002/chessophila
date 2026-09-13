#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

command -v uv >/dev/null || {
  echo "uv is required: https://docs.astral.sh/uv/" >&2
  exit 1
}

uv python install 3.10
uv venv --python 3.10 .venv-shiu
uv pip install --python .venv-shiu/bin/python -e '.[sim]'

echo "Simulator environment ready: $repo_root/.venv-shiu"
echo "Run: .venv-shiu/bin/python scripts/run_shiu_probe.py"
