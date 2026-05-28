#!/bin/bash
# Delete all ClickHouse metric records for a given project ID.
# Usage: ./clear_project_metrics.sh <project-id>

set -euo pipefail

[[ $# -lt 1 ]] && { echo "Usage: $0 <project-id>"; exit 1; }

PROJECT_ID="$1"
CH_USER="metrics_user"
CH_PASSWORD="metrics_pass"
CH_URL="http://localhost:8123"

echo "Deleting all metrics for project: $PROJECT_ID"

BEFORE=$(curl -sf "$CH_URL/?query=SELECT+count()+FROM+metrics.metric_records+WHERE+project_id='$PROJECT_ID'" \
  --user "$CH_USER:$CH_PASSWORD")
echo "  Rows before: $BEFORE"

curl -sf "$CH_URL/" \
  --user "$CH_USER:$CH_PASSWORD" \
  --data "ALTER TABLE metrics.metric_records DELETE WHERE project_id = '$PROJECT_ID'"

echo "  Delete issued. Waiting for mutation to apply..."
sleep 3

AFTER=$(curl -sf "$CH_URL/?query=SELECT+count()+FROM+metrics.metric_records+WHERE+project_id='$PROJECT_ID'" \
  --user "$CH_USER:$CH_PASSWORD")
echo "  Rows after:  $AFTER"
echo "Done."
