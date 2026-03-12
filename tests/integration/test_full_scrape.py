import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
import shutil
from datetime import datetime
from dateutil.tz import gettz
from src.forexfactory.main import scrape_range_with_details

class TestFullScrape(unittest.TestCase):

    def setUp(self):
        self.output_file = "test_integration_output.csv"
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_scrape_small_range(self):
        """
        End-to-end test that scrapes a small date range
        and verifies the output CSV is created and contains the expected row(s).
        """
        tz = gettz("Asia/Bangkok")
        start_dt = datetime(2025, 1, 5, tzinfo=tz)
        end_dt   = datetime(2025, 1, 5, tzinfo=tz)
        scrape_range_with_details(
            start_date=start_dt,
            end_date=end_dt,
            output_csv=self.output_file,
            tzname="Asia/Bangkok"
        )

        self.assertTrue(os.path.exists(self.output_file), "CSV output file should be created.")

        with open(self.output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 1, "Should have at least one row of data (plus header).")

if __name__ == '__main__':
    unittest.main()
