# Scraper Server Setup Guide

## 1. Install Prerequisites

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv curl

# Google Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
  | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Check Chrome version (note it down)
google-chrome --version
```

## 2. Clone & Setup

```bash
git clone https://github.com/Tabmydata/forexfactory-scraper.git
cd forexfactory-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Match Chrome Version in scraper.py

Open `src/forexfactory/scraper.py` and update the version number to match your Chrome:

```python
driver = uc.Chrome(version_main=134)  # ← change to your Chrome version
```

## 4. Set Environment Variables

```bash
echo 'export ECON_UPLOAD_URL=https://api.tabmydata.com/api' >> ~/.bashrc
echo 'export ECON_UPLOAD_SECRET=e48ab4fe26933362194dc635b15f1c891a2119d5f328a1d03464eb02e3f8ceeb' >> ~/.bashrc
source ~/.bashrc
```

## 5. Run Initial Full-Year Scrape (Once)

```bash
cd ~/forexfactory-scraper
source venv/bin/activate
bash scrape_2026.sh
```

This takes ~30-60 minutes (scrapes month by month with 30s delay).

## 6. Test Update Script

```bash
bash update_actuals.sh
# Expected output:
# [2026-03-12 10:00] Updating actuals: 2026-03-10 → 2026-03-13
# [2026-03-12 10:05] Upload success.
# [2026-03-12 10:05] Done.
```

## 7. Set Up Cron (Every 4 Hours)

```bash
crontab -e
```

Add this line:

```
0 */4 * * * /home/ubuntu/forexfactory-scraper/update_actuals.sh >> /home/ubuntu/forexfactory-scraper/actuals.log 2>&1
```

---

## tmd-auth Server

Add to `.env`:

```
ECON_UPLOAD_SECRET=e48ab4fe26933362194dc635b15f1c891a2119d5f328a1d03464eb02e3f8ceeb
```

---

## Summary

| Step | Where | Action |
|------|-------|--------|
| Install Chrome + Python | Scraper server | `apt install` |
| Clone repo | Scraper server | `git clone Tabmydata/forexfactory-scraper` |
| Set env vars | Scraper server | `~/.bashrc` |
| Run initial scrape | Scraper server | `bash scrape_2026.sh` |
| Set cron | Scraper server | `crontab -e` |
| Add env var | tmd-auth server | `.env` |
