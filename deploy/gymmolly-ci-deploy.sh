#!/usr/bin/env bash
# Installed on the server as /usr/local/sbin/gymmolly-ci-deploy (root:root 755).
# It is the ONLY command the GitHub Actions deploy key can run: the key's line in
# /root/.ssh/authorized_keys is pinned with restrict,command="/usr/local/sbin/gymmolly-ci-deploy".
#
# Input: the commit SHA to deploy, passed as the SSH command (SSH_ORIGINAL_COMMAND).
# It fast-forwards /opt/gymmolly to that commit (must be on origin/main), rebuilds the containers
# with docker-compose.prod.yml, health-checks the frontend and API, and rolls back to the previous
# commit if the health check fails. /opt/gymmolly/.env is server-owned and never touched.
set -euo pipefail

APP=/opt/gymmolly
LOCK=/run/lock/gymmolly-ci-deploy.lock
compose() { docker-compose -f docker-compose.prod.yml "$@"; }
log() { printf '%s gymmolly-ci-deploy: %s\n' "$(date -u +%FT%TZ)" "$*"; }

exec 9>"$LOCK"
flock -n 9 || { log "another deploy is running"; exit 1; }

SHA="${SSH_ORIGINAL_COMMAND:-}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { log "expected a 40-character commit SHA"; exit 2; }

cd "$APP"
[ -f .env ] || { log ".env missing"; exit 1; }

healthy() {
  for _ in $(seq 1 18); do
    if curl -fsS -o /dev/null http://localhost:3001 && curl -fsS -o /dev/null http://localhost:5001/api/inventory; then
      return 0
    fi
    sleep 5
  done
  return 1
}

PREV="$(git rev-parse HEAD)"
git fetch -q origin main
git merge-base --is-ancestor "$SHA" origin/main || { log "$SHA is not on origin/main"; exit 2; }

log "deploying $SHA (was $PREV)"
git checkout -q main
git merge -q --ff-only "$SHA"
compose up -d --build

if healthy; then
  log "healthy at $(git rev-parse --short HEAD)"
  exit 0
fi

log "health check failed; rolling back to $PREV"
git reset -q --hard "$PREV"
compose up -d --build
healthy && log "rolled back and healthy" || log "rollback is NOT healthy, check by hand"
exit 1
