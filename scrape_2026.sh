#!/bin/bash

cd "$(dirname "$0")"
source venv/bin/activate

MONTHS=(
  "2026-01-01 2026-01-31"
  "2026-02-01 2026-02-28"
  "2026-03-01 2026-03-31"
  "2026-04-01 2026-04-30"
  "2026-05-01 2026-05-31"
  "2026-06-01 2026-06-30"
  "2026-07-01 2026-07-31"
  "2026-08-01 2026-08-31"
  "2026-09-01 2026-09-30"
  "2026-10-01 2026-10-31"
  "2026-11-01 2026-11-30"
  "2026-12-01 2026-12-31"
)

for MONTH in "${MONTHS[@]}"; do
  START=$(echo $MONTH | cut -d' ' -f1)
  END=$(echo $MONTH | cut -d' ' -f2)

  echo "========================================="
  echo "Scraping $START → $END"
  echo "========================================="

  python3 -m src.forexfactory.main \
    --start "$START" \
    --end "$END" \
    --csv econ_2026.csv \
    --tz Asia/Bangkok

  echo "Done $START → $END. Sleeping 30s..."
  sleep 30
done

echo "========================================="
echo "All months done! Converting to JSON..."
python3 to_json.py econ_2026.csv econ_2026.json
echo "Output: econ_2026.json"
