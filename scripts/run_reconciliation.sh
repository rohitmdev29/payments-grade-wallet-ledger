#!/usr/bin/env bash
# Manually trigger a reconciliation run.
set -e
docker compose exec api python -m app.workers.nightly_reconciliation
