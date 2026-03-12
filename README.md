# Forex Factory Scraper

A robust web scraper for [Forex Factory](https://www.forexfactory.com/) economic calendar events. Built with Selenium and pandas, supporting incremental scraping and automated daily actual value updates.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Scripts](#scripts)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **Incremental Scraping:** Only fetches new or updated events, skipping already-scraped data
- **Daily Actual Updates:** Automated script to update actual values every 4-6 hours via cron
- **Flexible Date Range:** Specify any start/end date range
- **Timezone Support:** Defaults to `Asia/Bangkok` (UTC+7)
- **JSON Export:** Convert CSV output to JSON for backend consumption
- **Filtering:** Filter by impact level and currency

## Installation

### Prerequisites

- Python 3.7+
- Google Chrome (latest version recommended)

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/Tabmydata/forexfactory-scraper.git
   cd forexfactory-scraper
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--start` | Yes | — | Start date (YYYY-MM-DD) |
| `--end` | Yes | — | End date (YYYY-MM-DD) |
| `--csv` | No | `forex_factory_cache.csv` | Output CSV file path |
| `--tz` | No | `Asia/Bangkok` | Timezone |
| `--details` | No | false | Scrape detailed event info |
| `--impact` | No | all | Filter by impact: `high,medium,low` |
| `--keep-currencies` | No | all | Filter by currency: `USD EUR GBP` |

### Examples

```bash
# Scrape a specific week
python3 -m src.forexfactory.main \
  --start 2026-03-10 --end 2026-03-14 \
  --csv econ_2026.csv

# Scrape high-impact USD/EUR events only
python3 -m src.forexfactory.main \
  --start 2026-01-01 --end 2026-12-31 \
  --csv econ_2026.csv \
  --impact high \
  --keep-currencies USD EUR
```

## Scripts

### scrape_2026.sh — Full year initial scrape

```bash
bash scrape_2026.sh
```

Scrapes month by month (Jan–Dec 2026) into a single `econ_2026.csv`, then converts to `econ_2026.json`. Run once on initial setup.

### update_actuals.sh — Daily actual updates

```bash
bash update_actuals.sh
```

Scrapes the past 2 days through tomorrow to capture actual values for recently released events.

**Set up cron to run every 4 hours:**

```bash
crontab -e
# Add this line:
0 */4 * * * /home/ubuntu/forexfactory-scraper/update_actuals.sh >> /home/ubuntu/forexfactory-scraper/actuals.log 2>&1
```

### to_json.py — Convert CSV to JSON

```bash
python3 to_json.py econ_2026.csv econ_2026.json
```

## Dependencies

- [selenium](https://pypi.org/project/selenium/) — browser automation
- [pandas](https://pandas.pydata.org/) — data manipulation
- [undetected-chromedriver](https://pypi.org/project/undetected-chromedriver/) — bypass detection mechanisms
- [python-dateutil](https://dateutil.readthedocs.io/en/stable/) — date and timezone handling

## Troubleshooting

### Getting 0 rows

Forex Factory may block continuous requests. Use `scrape_2026.sh` which scrapes month by month with delays between requests.

### Chrome version mismatch

Check your installed Chrome version and update `scraper.py`:

```python
driver = uc.Chrome(version_main=134)  # match your Chrome version
```

### StaleElementReferenceException

The scraper has built-in retry logic. If it persists, re-run the same date range — incremental mode will skip already-scraped events.

### CAPTCHA / Cloudflare blocks

- `undetected-chromedriver` handles most cases automatically
- Increase the sleep delay between months in `scrape_2026.sh` if needed

## License

This project is licensed under the [MIT License](LICENSE).

---

**Disclaimer:** For personal and educational use only. Ensure compliance with Forex Factory's [Terms of Service](https://www.forexfactory.com/disclaimer).
