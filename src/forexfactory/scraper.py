# src/forexfactory/scraper.py

import time
import re
import logging
import pandas as pd
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
import platform
import undetected_chromedriver as uc

from .csv_util import ensure_csv_header, read_existing_data, write_data_to_csv, merge_new_data
from .detail_parser import parse_detail_table, detail_data_to_string

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def parse_calendar_day(driver, the_date: datetime, scrape_details=False, existing_df=None) -> pd.DataFrame:
    """
    Scrape data for a single day (the_date) and return a DataFrame with columns:
      DateTime, Currency, Impact, Event, Actual, Forecast, Previous, Detail
    If scrape_details is False, skip detail parsing.

    Before fetching detail data from the Internet, this function checks if the record
    already exists (using existing_df) with a non-empty "Detail" field.
    """
    date_str = the_date.strftime('%b%d.%Y').lower()
    url = f"https://www.forexfactory.com/calendar?day={date_str}"
    logger.info(f"Scraping URL: {url}")
    try:
        driver.get(url)
    except Exception as e:
        logger.warning(f"Failed to load page for {the_date.date()}: {e}")
        return pd.DataFrame(
            columns=["DateTime", "Currency", "Impact", "Event", "Actual", "Forecast", "Previous", "Detail"])

    try:
        WebDriverWait(driver, 30).until(  # Increased wait time
            EC.visibility_of_element_located((By.XPATH, '//table[contains(@class,"calendar__table")]'))
        )
    except TimeoutException:
        logger.warning(f"Page did not load for day={the_date.date()}")
        return pd.DataFrame(
            columns=["DateTime", "Currency", "Impact", "Event", "Actual", "Forecast", "Previous", "Detail"])

    ff_offset_minutes = 420  # default Bangkok
    try:
        from datetime import timezone as _dtz
        tz_el = driver.find_element(By.XPATH, '//a[@href="/timezone"]')
        ff_time_str = tz_el.text.strip().lower()
        m_clock = re.match(r'(\d{1,2}):(\d{2})(am|pm)?', ff_time_str)
        ff_h = int(m_clock.group(1))
        ff_m = int(m_clock.group(2))
        if m_clock.group(3) == 'pm' and ff_h < 12:
            ff_h += 12
        elif m_clock.group(3) == 'am' and ff_h == 12:
            ff_h = 0
        now_utc = datetime.now(_dtz.utc)
        diff = (ff_h * 60 + ff_m) - (now_utc.hour * 60 + now_utc.minute)
        if diff > 720:
            diff -= 1440
        elif diff < -720:
            diff += 1440
        ff_offset_minutes = round(diff / 15) * 15
        logger.debug(f"FF clock: {ff_time_str}, UTC: {now_utc.strftime('%H:%M')} → offset UTC{'+' if ff_offset_minutes >= 0 else ''}{ff_offset_minutes // 60}")
    except Exception as e:
        logger.warning(f"Could not detect FF timezone: {e}")

    rows = driver.find_elements(By.XPATH, '//tr[contains(@class,"calendar__row")]')
    data_list = []
    current_day = the_date
    last_clock_time = None

    for row in rows:
        row_class = row.get_attribute("class")
        if "day-breaker" in row_class or "no-event" in row_class:
            continue

        # Parse the basic cells
        try:
            time_el = row.find_element(By.XPATH, './/td[contains(@class,"calendar__time")]')
            currency_el = row.find_element(By.XPATH, './/td[contains(@class,"calendar__currency")]')
            impact_el = row.find_element(By.XPATH, './/td[contains(@class,"calendar__impact")]')
            event_el = row.find_element(By.XPATH, './/td[contains(@class,"calendar__event")]')
            actual_el = row.find_element(By.XPATH, './/td[contains(@class,"calendar__actual")]')
            forecast_el = row.find_element(By.XPATH, './/td[contains(@class,"calendar__forecast")]')
            previous_el = row.find_element(By.XPATH, './/td[contains(@class,"calendar__previous")]')
        except NoSuchElementException:
            continue

        time_text = time_el.text.strip()
        currency_text = currency_el.text.strip()

        # Get impact text
        impact_text = ""
        try:
            impact_span = impact_el.find_element(By.XPATH, './/span')
            impact_text = impact_span.get_attribute("title") or ""
        except Exception:
            impact_text = impact_el.text.strip()

        event_text = event_el.text.strip()
        actual_text = actual_el.text.strip()
        # ForexFactory puts better/worse on the td or on a child span
        actual_class = actual_el.get_attribute("class") or ""
        try:
            actual_span = actual_el.find_element(By.XPATH, './/span')
            actual_class = actual_class + " " + (actual_span.get_attribute("class") or "")
        except Exception:
            pass
        if "better" in actual_class:
            actual_dir = "better"
        elif "worse" in actual_class:
            actual_dir = "worse"
        else:
            actual_dir = ""
        forecast_text = forecast_el.text.strip()
        previous_text = previous_el.text.strip()

        # Determine event time based on text
        from datetime import timezone as _tz
        ff_tz_obj = _tz(timedelta(minutes=ff_offset_minutes))
        event_dt = current_day.replace(tzinfo=ff_tz_obj)
        time_lower = time_text.lower()
        if not time_lower and last_clock_time is not None:
            event_dt = last_clock_time
        elif "day" in time_lower or "tentative" in time_lower or re.search(r'\d+(st|nd|rd|th)', time_lower):
            event_dt = datetime(current_day.year, current_day.month, current_day.day, 0, 0, 0, tzinfo=_tz.utc)
        elif "data" in time_lower:
            event_dt = datetime(current_day.year, current_day.month, current_day.day, 0, 0, 1, tzinfo=_tz.utc)
        else:
            m = re.match(r'(\d{1,2}):(\d{2})(am|pm)', time_lower)
            if m:
                hh = int(m.group(1))
                mm = int(m.group(2))
                ampm = m.group(3)
                if ampm == 'pm' and hh < 12:
                    hh += 12
                if ampm == 'am' and hh == 12:
                    hh = 0
                # Parse time in FF's actual display timezone, store with that offset
                event_dt = event_dt.replace(hour=hh, minute=mm, second=0, tzinfo=ff_tz_obj)
                last_clock_time = event_dt

        event_dt = event_dt.astimezone(_tz.utc)

        # Compute a unique key for the event using DateTime, Currency, and Event
        unique_key = f"{event_dt.isoformat()}_{currency_text}_{event_text}"

        # Capture event URL from row's data-event-id
        detail_url = ""
        try:
            event_id = row.get_attribute("data-event-id")
            if event_id:
                day_str_url = current_day.strftime('%b').lower() + str(current_day.day) + '.' + str(current_day.year)
                detail_url = f"https://www.forexfactory.com/calendar?day={day_str_url}#detail={event_id}"
        except Exception:
            pass

        # Initialize detail string
        detail_str = ""
        if scrape_details:
            # If an existing CSV DataFrame is provided, check if this record exists and has detail.
            if existing_df is not None:
                matched = existing_df[
                    (existing_df["DateTime"] == event_dt.isoformat()) &
                    (existing_df["Currency"].str.strip() == currency_text) &
                    (existing_df["Event"].str.strip() == event_text)
                    ]
                if not matched.empty:
                    existing_detail = str(matched.iloc[0]["Detail"]).strip() if pd.notnull(
                        matched.iloc[0]["Detail"]) else ""
                    if existing_detail:
                        detail_str = existing_detail

            # If detail_str is still empty, then fetch detail from the Internet.
            if not detail_str:
                try:
                    open_link = row.find_element(By.XPATH, './/td[contains(@class,"calendar__detail")]/a')
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", open_link)
                    time.sleep(1)
                    open_link.click()
                    WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located(
                            (By.XPATH, '//tr[contains(@class,"calendar__details--detail")]'))
                    )
                    detail_data = parse_detail_table(driver)
                    detail_str = detail_data_to_string(detail_data)
                    try:
                        close_link = row.find_element(By.XPATH, './/a[@title="Close Detail"]')
                        close_link.click()
                    except Exception:
                        pass
                except Exception:
                    pass

        data_list.append({
            "DateTime": event_dt.isoformat(),
            "Currency": currency_text,
            "Impact": impact_text,
            "Event": event_text,
            "Actual": actual_text,
            "ActualDir": actual_dir,
            "Forecast": forecast_text,
            "Previous": previous_text,
            "Detail": detail_str,
            "Url": detail_url,
        })

    return pd.DataFrame(data_list)


def scrape_day(driver, the_date: datetime, existing_df: pd.DataFrame, scrape_details=False) -> pd.DataFrame:
    """
    Re-scrape a single day, using existing_df to check for already-saved details.
    """
    df_day_new = parse_calendar_day(driver, the_date, scrape_details=scrape_details, existing_df=existing_df)
    return df_day_new


def scrape_range_pandas(from_date: datetime, to_date: datetime, output_csv: str, tzname="Asia/Bangkok",
                        scrape_details=False, impact_filter=None, keep_currencies=None):
    from .csv_util import ensure_csv_header, read_existing_data, write_data_to_csv

    ensure_csv_header(output_csv)
    existing_df = read_existing_data(output_csv)

    is_linux = platform.system() == 'Linux'
    if is_linux:
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1400, 1000))
        display.start()

    driver = uc.Chrome(version_main=146)
    driver.set_window_size(1400, 1000)
    driver.set_page_load_timeout(300)  # Increase timeout to 5 minutes

    driver.get('https://www.forexfactory.com')
    driver.delete_all_cookies()
    driver.refresh()
    time.sleep(3)

    total_new = 0
    day_count = (to_date - from_date).days + 1
    logger.info(f"Scraping from {from_date.date()} to {to_date.date()} for {day_count} days.")

    try:
        current_day = from_date
        while current_day <= to_date:
            logger.info(f"Scraping day {current_day.strftime('%Y-%m-%d')}...")
            df_new = scrape_day(driver, current_day, existing_df, scrape_details=scrape_details)

            if impact_filter and not df_new.empty:
                df_new = df_new[df_new['Impact'].str.lower().str.contains('|'.join(impact_filter))]

            if keep_currencies and not df_new.empty:
                df_new = df_new[df_new['Currency'].isin(keep_currencies)]

            day_str = current_day.date().isoformat()
            existing_day = existing_df[existing_df["DateTime"].str.startswith(day_str)].copy()

            if not df_new.empty:
                # Preserve Actual/ActualDir/Detail from existing rows where new scrape has empty values
                if not existing_day.empty:
                    def make_key(row):
                        return f"{str(row['DateTime']).strip()}_{str(row['Currency']).strip()}_{str(row['Event']).strip()}"
                    existing_day['_key'] = existing_day.apply(make_key, axis=1)
                    existing_lookup = existing_day.set_index('_key')

                    def enrich_row(row):
                        key = f"{str(row['DateTime']).strip()}_{str(row['Currency']).strip()}_{str(row['Event']).strip()}"
                        if key in existing_lookup.index:
                            ex = existing_lookup.loc[key]
                            if isinstance(ex, pd.DataFrame):
                                ex = ex.iloc[0]
                            for field in ('Actual', 'ActualDir', 'Detail'):
                                new_val = str(row.get(field, '')).strip()
                                ex_field = ex.get(field)
                                ex_val = str(ex_field).strip() if pd.notna(ex_field) else ''
                                if not new_val and ex_val:
                                    row[field] = ex_val
                        return row

                    df_new = df_new.apply(enrich_row, axis=1)

            # Replace this day's rows entirely (syncs deletions from FF)
            existing_df = existing_df[~existing_df["DateTime"].str.startswith(day_str)]

            if not df_new.empty:
                existing_df = pd.concat([existing_df, df_new], ignore_index=True)

            added = len(df_new) if not df_new.empty else 0
            removed = len(existing_day)
            net = added - removed
            if net != 0 or added > 0:
                logger.info(f"{current_day.date()}: {'+' if net >= 0 else ''}{net} net ({added} from FF, {removed} previously stored)")
            total_new += max(0, net)

            # Save updated data to CSV after processing the day's data.
            write_data_to_csv(existing_df, output_csv)

            current_day += timedelta(days=1)
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Chrome WebDriver closed successfully.")
            except OSError as ose:
                # Ignore specific OSError during final cleanup (e.g., WinError 6)
                logger.debug(f"Ignored OSError during WebDriver quit: {ose}")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                driver = None
        if is_linux and 'display' in locals():
            display.stop()

    # Final save (if needed)
    write_data_to_csv(existing_df, output_csv)
    logger.info(f"Done. Total new rows: {total_new}")
