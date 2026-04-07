#!/bin/bash

cd "$(dirname "$0")"
source venv/bin/activate

YEAR=${1:-$(date +%Y)}
CSV="econ_${YEAR}.csv"
JSON="econ_${YEAR}.json"

# Days per month (handle leap year for Feb)
days_in_month() {
  local y=$1 m=$2
  case $m in
    01|03|05|07|08|10|12) echo 31 ;;
    04|06|09|11) echo 30 ;;
    02) [ $(( y % 4 == 0 && (y % 100 != 0 || y % 400 == 0) )) -eq 1 ] && echo 29 || echo 28 ;;
  esac
}

for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  START="${YEAR}-${m}-01"
  END="${YEAR}-${m}-$(days_in_month $YEAR $m)"

  echo "========================================="
  echo "Scraping $START → $END"
  echo "========================================="

  python3 -m src.forexfactory.main \
    --start "$START" \
    --end "$END" \
    --csv "$CSV" \
    --details

  echo "Done $START → $END. Sleeping 45s..."
  sleep 45
done

echo "========================================="
echo "All months done! Converting to JSON..."
python3 to_json.py "$CSV" "$JSON"
echo "Output: $JSON"
