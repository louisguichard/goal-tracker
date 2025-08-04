import unittest
import os
import json
import csv
import shutil
from datetime import datetime, timedelta
from tracker import ProgressTracker


class TestProgressCalculation(unittest.TestCase):
    def setUp(self):
        """Set up a temporary environment for tests."""
        self.test_dir = "temp_test_data"
        self.program_id = "test_program"
        program_dir = os.path.join(self.test_dir, self.program_id)
        os.makedirs(program_dir, exist_ok=True)

        current_program_file = os.path.join(self.test_dir, "current_program.txt")
        with open(current_program_file, "w") as f:
            f.write(self.program_id)

    def tearDown(self):
        """Clean up the temporary environment after tests."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_program_file(self, program_data):
        """Helper to create a program.json file."""
        program_dir = os.path.join(self.test_dir, self.program_id)
        program_file = os.path.join(program_dir, "program.json")
        with open(program_file, "w") as f:
            json.dump(program_data, f, indent=2)

    def _create_user_data_file(self, user_data_rows):
        """Helper to create a user_data.csv file."""
        program_dir = os.path.join(self.test_dir, self.program_id)
        user_data_file = os.path.join(program_dir, "user_data.csv")
        with open(user_data_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "item_id", "type", "value"])
            writer.writerows(user_data_rows)

    def _run_progress_test(self, program_data, user_data_rows):
        """
        Factory method to run a test scenario.
        It creates the necessary files, runs the calculation, and returns the result.
        """
        self._create_program_file(program_data)
        self._create_user_data_file(user_data_rows)

        tracker = ProgressTracker(data_dir=self.test_dir)
        tracker.load_program()
        user_data = tracker.get_user_data()
        return tracker.compute_progress(user_data)

    def test_progress_first_day_one_task_completed(self):
        """
        Test with one task, completed on day 1 of a 49-day program.
        - Current progress should be 100%.
        - Expected progress should be ~2.0% (1/49th).
        """
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=48)
        program_data = {
            "name": "Test Program",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [],
            "tasks": [{"id": "task_1", "name": "Do the thing", "weight": 100}],
        }
        user_data_rows = [[start_date.strftime("%Y-%m-%d"), "task_1", "task", "1"]]

        progress = self._run_progress_test(program_data, user_data_rows)

        self.assertEqual(progress["current_progress"], 100.0)
        self.assertEqual(progress["expected_progress"], 2.0)
        self.assertTrue(progress["is_on_track"])
        self.assertEqual(progress["current_points"], 100)
        self.assertEqual(progress["total_points"], 100)
        self.assertEqual(progress["elapsed_days"], 1)
        self.assertEqual(progress["total_days"], 49)

    def test_progress_first_day_one_task_not_completed(self):
        """
        Test with one task, not completed on day 1 of a 49-day program.
        - Current progress should be 0%.
        - Expected progress should be ~2.0% (1/49th).
        """
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=48)
        program_data = {
            "name": "Test Program",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [],
            "tasks": [{"id": "task_1", "name": "Do the thing", "weight": 100}],
        }
        user_data_rows = []  # No data, so task is not done

        progress = self._run_progress_test(program_data, user_data_rows)

        self.assertEqual(progress["current_progress"], 0.0)
        self.assertEqual(progress["expected_progress"], 2.0)
        self.assertFalse(progress["is_on_track"])
        self.assertEqual(progress["current_points"], 0)
        self.assertEqual(progress["total_points"], 100)
        self.assertEqual(progress["elapsed_days"], 1)
        self.assertEqual(progress["total_days"], 49)


if __name__ == "__main__":
    unittest.main()
