#!/bin/bash

cd "$(dirname "$0")"
source venv/bin/activate

# scrape ย้อนหลัง 2 วัน ถึง พรุ่งนี้ เพื่อจับ actual ของวันนี้และเมื่อวาน
START=$(date -v-2d +%Y-%m-%d)
END=$(date -v+1d +%Y-%m-%d)

echo "[$(date '+%Y-%m-%d %H:%M')] Updating actuals: $START → $END"

python3 -m src.forexfactory.main \
  --start "$START" \
  --end "$END" \
  --csv econ_2026.csv \
  --tz Asia/Bangkok

# re-generate JSON จาก CSV ที่อัพเดตแล้ว
python3 to_json.py econ_2026.csv econ_2026.json

# copy ไป backend
cp econ_2026.json /Users/jay/Developer/tmd-auth/data/econ_2026.json

echo "[$(date '+%Y-%m-%d %H:%M')] Done."
