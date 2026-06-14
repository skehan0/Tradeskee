#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
git -C "$repo_root" config core.hooksPath .githooks
chmod +x "$repo_root/.githooks/pre-push"
echo "Git hooks configured. pre-push linting is now enabled for this repo."