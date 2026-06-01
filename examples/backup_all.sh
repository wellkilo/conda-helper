#!/usr/bin/env bash
# Example: nightly backup of every conda environment on this host.
# Drop into crontab, e.g.:
#   0 3 * * *  /path/to/backup_all.sh >> ~/conda-backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${HOME}/conda-backups/$(date +%F)"
mkdir -p "${BACKUP_DIR}"

# Iterate every env name (skip the JSON wrapper) and back it up.
conda-helper ls --json | python -c "
import json, sys
for e in json.load(sys.stdin):
    print(e['name'])
" | while read -r env; do
    [ -z "${env}" ] && continue
    conda-helper backup "${env}" --from-history -o "${BACKUP_DIR}" || true
done

echo "Backups written to ${BACKUP_DIR}"
