#!/usr/bin/env bash
# sync.sh — pull latest master into GOLDEN.
# Run from the container root: bash GOLDEN/sync.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="$(dirname "$SCRIPT_DIR")"

echo "Syncing GOLDEN with origin/master..."
git -C "$SCRIPT_DIR" pull origin master
echo "GOLDEN is up to date."

echo ""
echo "Worktree status:"
git -C "$CONTAINER" worktree list
