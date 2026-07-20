#!/bin/sh
set -e

if [ -f /var/lib/postgresql/data/PG_VERSION ]; then
    echo "[repair] Fixing postgres role..."
    echo "ALTER ROLE postgres WITH LOGIN PASSWORD 'postgres';" | \
        su-exec postgres postgres --single -D /var/lib/postgresql/data postgres 2>/dev/null || true
    echo "[repair] Done."
fi

exec /usr/local/bin/docker-entrypoint.sh "$@"
