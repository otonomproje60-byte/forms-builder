#!/bin/sh
# Forms Builder - Entrypoint script to fix volume permissions
# Applied lesson from heartbeat-monitor incident (2026-09-27)

# Fix permissions on mounted volumes (runs as root before dropping to app user)
chown -R app:app /app/data 2>/dev/null || true

# Drop to app user and exec the main command
exec gosu app "$@"