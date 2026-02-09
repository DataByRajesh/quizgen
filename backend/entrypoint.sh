#!/usr/bin/env sh
set -e

echo "[entrypoint] Starting container at $(date -u)"
echo "[entrypoint] Environment overview:"
echo "  PORT=${PORT:-<not set>}"
echo "  WEB_CONCURRENCY=${WEB_CONCURRENCY:-<not set>}"
if [ -n "$OPENAI_API_KEY" ]; then
  echo "  OPENAI_API_KEY=SET (masked)"
else
  echo "  OPENAI_API_KEY=<not set>"
fi
if [ -n "$API_KEYS" ]; then
  echo "  API_KEYS=SET"
else
  echo "  API_KEYS=<not set>"
fi
if [ -n "$QUIZGEN_DB_PATH" ]; then
  echo "  QUIZGEN_DB_PATH=$QUIZGEN_DB_PATH"
else
  echo "  QUIZGEN_DB_PATH=<default>"
fi

echo "[entrypoint] Working directory: $(pwd)"
echo "[entrypoint] Contents (top-level):"
ls -la . | sed -n '1,200p'

# Join all args into a single command string so shell expansion (eg. $PORT) occurs
CMD_STR="$*"
echo "[entrypoint] Executing (pre-expansion): $CMD_STR"

# Use sh -c to allow environment variable expansion (e.g., $PORT passed as literal in CMD)
exec sh -c "$CMD_STR"
