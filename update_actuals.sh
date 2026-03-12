#!/bin/bash

cd "$(dirname "$0")"
source venv/bin/activate

# Load local env if exists (for local testing)
[ -f .env.local ] && source .env.local

# Scrape from 2 days ago to tomorrow to capture actuals for today and yesterday
START=$(date -v-2d +%Y-%m-%d)
END=$(date -v+1d +%Y-%m-%d)

echo "[$(date '+%Y-%m-%d %H:%M')] Updating actuals: $START → $END"

python3 -m src.forexfactory.main \
  --start "$START" \
  --end "$END" \
  --csv econ_2026.csv \
  --tz Asia/Bangkok

# Re-generate JSON from updated CSV
python3 to_json.py econ_2026.csv econ_2026.json

# Upload JSON to tmd-auth server
curl -s -X POST "${ECON_UPLOAD_URL}/calendar/econ/upload" \
  -H "Content-Type: application/json" \
  -H "x-upload-secret: ${ECON_UPLOAD_SECRET}" \
  --data-binary @econ_2026.json \
  && echo "[$(date '+%Y-%m-%d %H:%M')] Upload success." \
  || echo "[$(date '+%Y-%m-%d %H:%M')] Upload FAILED."

echo "[$(date '+%Y-%m-%d %H:%M')] Done."
