#!/bin/bash
# Coverage gate: blocks push if test coverage is below 80%.
# Called by .claude/settings.json PreToolUse hook before git push.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Running coverage check before push..."

# Run pytest with coverage
python3 -m pytest tests/ --cov=agents --cov-report=term-missing --cov-fail-under=80 -q
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo ""
  echo "PUSH BLOCKED: Test coverage is below 80%."
  echo "Fix failing tests or improve coverage before pushing."
  exit 1
fi

echo "Coverage check passed. Proceeding with push."
exit 0
