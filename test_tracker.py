import unittest
import os
import json
import csv
import shutil
from datetime import datetime, timedelta
from tracker import ProgressTracker


class BaseProgressTest(unittest.TestCase):
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


class TestProgressCalculation(BaseProgressTest):
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

    def test_objective_importance_multipliers(self):
        """
        Test that importance multipliers are correctly applied to objective points.
        """
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=6)  # 7-day program
        program_data = {
            "name": "Test Program",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_indispensable",
                    "name": "Critical Task",
                    "type": "checkbox",
                    "frequency": "daily",
                    "scoring": "binary",
                    "target_value": 1,
                    "weight": 1,
                    "start_value": 0,
                    "unit": "",
                    "importance": "indispensable",  # x3 multiplier
                },
                {
                    "id": "obj_important",
                    "name": "Important Task",
                    "type": "checkbox",
                    "frequency": "daily",
                    "scoring": "binary",
                    "target_value": 1,
                    "weight": 1,
                    "start_value": 0,
                    "unit": "",
                    "importance": "important",  # x2 multiplier
                },
                {
                    "id": "obj_bien",
                    "name": "Nice Task",
                    "type": "checkbox",
                    "frequency": "daily",
                    "scoring": "binary",
                    "target_value": 1,
                    "weight": 1,
                    "start_value": 0,
                    "unit": "",
                    "importance": "bien",  # x1 multiplier
                },
            ],
            "tasks": [],
        }

        # Complete all objectives for the first day
        user_data_rows = [
            [start_date.strftime("%Y-%m-%d"), "obj_indispensable", "binary", "1"],
            [start_date.strftime("%Y-%m-%d"), "obj_important", "binary", "1"],
            [start_date.strftime("%Y-%m-%d"), "obj_bien", "binary", "1"],
        ]

        progress = self._run_progress_test(program_data, user_data_rows)

        # Expected points calculation:
        # - Total points possible: (1*3 + 1*2 + 1*1) * 7 days = 6 * 7 = 42 points
        # - Current points: 1*3 + 1*2 + 1*1 = 6 points (for one day)
        # - Expected points: 6 points (for one day out of 7)
        # - Current progress: 6/42 * 100 = 14.3%
        # - Expected progress: 1/7 * 100 = 14.3%

        self.assertEqual(progress["current_points"], 6)  # 3+2+1 = 6 points for day 1
        self.assertEqual(progress["total_points"], 42)  # (3+2+1) * 7 days = 42 total
        self.assertAlmostEqual(progress["current_progress"], 14.3, places=1)
        self.assertAlmostEqual(progress["expected_progress"], 14.3, places=1)
        self.assertTrue(progress["is_on_track"])

    def test_weekly_objective_importance_multipliers(self):
        """
        Test importance multipliers for weekly objectives.
        """
        start_date = datetime.now().date()
        # Find the Monday of this week
        days_since_monday = start_date.weekday()
        monday = start_date - timedelta(days=days_since_monday)
        end_date = monday + timedelta(days=13)  # 2 weeks

        program_data = {
            "name": "Test Program",
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_weekly_indispensable",
                    "name": "Weekly Critical",
                    "type": "checkbox",
                    "frequency": "weekly",
                    "scoring": "binary",
                    "target_value": 3,  # Need 3 completions per week
                    "weight": 5,
                    "start_value": 0,
                    "unit": "",
                    "importance": "indispensable",  # x3 multiplier
                }
            ],
            "tasks": [],
        }

        # Complete the objective 3 times in the first week
        user_data_rows = [
            [monday.strftime("%Y-%m-%d"), "obj_weekly_indispensable", "binary", "1"],
            [
                (monday + timedelta(days=1)).strftime("%Y-%m-%d"),
                "obj_weekly_indispensable",
                "binary",
                "1",
            ],
            [
                (monday + timedelta(days=2)).strftime("%Y-%m-%d"),
                "obj_weekly_indispensable",
                "binary",
                "1",
            ],
        ]

        progress = self._run_progress_test(program_data, user_data_rows)

        # Expected calculation:
        # - Total points possible: 5 * 3 (multiplier) * 2 weeks = 30 points
        # - Current points: 5 * 3 (multiplier) = 15 points (first week completed)
        # - Since we're in the first week, expected points depend on exact timing

        self.assertEqual(progress["current_points"], 15)  # 5 base * 3 multiplier
        self.assertEqual(progress["total_points"], 30)  # 15 per week * 2 weeks

    def test_program_objective_importance_multipliers(self):
        """
        Test importance multipliers for program-wide objectives.
        """
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=13)  # 14-day program

        program_data = {
            "name": "Test Program",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_program_important",
                    "name": "Program Important",
                    "type": "cumulative",
                    "frequency": "program",
                    "scoring": "binary",
                    "target_value": 100,
                    "weight": 15,
                    "start_value": 0,
                    "unit": "points",
                    "importance": "important",  # x2 multiplier
                }
            ],
            "tasks": [],
        }

        # Add progress toward the program objective
        user_data_rows = [
            [
                start_date.strftime("%Y-%m-%d"),
                "obj_program_important",
                "numeric",
                "100",
            ],  # Complete the target
        ]

        progress = self._run_progress_test(program_data, user_data_rows)

        # Expected calculation:
        # - Total points possible: 15 * 2 (multiplier) = 30 points
        # - Current points: 15 * 2 (multiplier) = 30 points (target achieved)
        # - Current progress: 30/30 * 100 = 100%

        self.assertEqual(progress["current_points"], 30)  # 15 base * 2 multiplier
        self.assertEqual(progress["total_points"], 30)  # 15 base * 2 multiplier
        self.assertEqual(progress["current_progress"], 100.0)

    def test_mixed_importance_levels(self):
        """
        Test a mix of different importance levels in one program.
        """
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=6)  # 7-day program

        program_data = {
            "name": "Test Program",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_daily_indispensable",
                    "name": "Daily Critical",
                    "type": "checkbox",
                    "frequency": "daily",
                    "scoring": "binary",
                    "target_value": 1,
                    "weight": 1,
                    "start_value": 0,
                    "unit": "",
                    "importance": "indispensable",  # x3
                },
                {
                    "id": "obj_program_important",
                    "name": "Program Important",
                    "type": "cumulative",
                    "frequency": "program",
                    "scoring": "binary",
                    "target_value": 10,
                    "weight": 15,
                    "start_value": 0,
                    "unit": "",
                    "importance": "important",  # x2
                },
            ],
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Regular Task",
                    "weight": 5,
                }  # No multiplier for tasks
            ],
        }

        # Complete daily objective for first day, complete the task, and make progress on program objective
        user_data_rows = [
            [start_date.strftime("%Y-%m-%d"), "obj_daily_indispensable", "binary", "1"],
            [
                start_date.strftime("%Y-%m-%d"),
                "obj_program_important",
                "numeric",
                "10",
            ],  # Complete target
            [start_date.strftime("%Y-%m-%d"), "task_1", "task", "1"],
        ]

        progress = self._run_progress_test(program_data, user_data_rows)

        # Expected calculation:
        # - Daily objective: 1 * 3 (multiplier) * 7 days = 21 total points, 3 earned
        # - Program objective: 15 * 2 (multiplier) = 30 total points, 30 earned
        # - Task: 5 points total, 5 earned
        # - Total possible: 21 + 30 + 5 = 56 points
        # - Current earned: 3 + 30 + 5 = 38 points
        # - Current progress: 38/56 * 100 = 67.9%

        self.assertEqual(progress["current_points"], 38)  # 3 + 30 + 5
        self.assertEqual(progress["total_points"], 56)  # 21 + 30 + 5
        self.assertAlmostEqual(progress["current_progress"], 67.9, places=1)


class TestObjectiveTypesAndScoring(BaseProgressTest):
    def test_weekly_cumulative_proportional_scoring(self):
        """Test weekly cumulative objective with proportional scoring."""
        start_date = datetime.now().date()
        days_since_monday = start_date.weekday()
        monday = start_date - timedelta(days=days_since_monday)
        end_date = monday + timedelta(days=6)  # 1 week

        program_data = {
            "name": "Test Program",
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_weekly_cumulative",
                    "name": "Read 100 pages",
                    "type": "cumulative",
                    "frequency": "weekly",
                    "scoring": "proportional",
                    "target_value": 100,
                    "weight": 10,
                    "start_value": 0,
                    "unit": "pages",
                    "importance": "bien",
                }
            ],
            "tasks": [],
        }

        # Read 50 pages over two days
        user_data_rows = [
            [monday.strftime("%Y-%m-%d"), "obj_weekly_cumulative", "numeric", "20"],
            [
                (monday + timedelta(days=1)).strftime("%Y-%m-%d"),
                "obj_weekly_cumulative",
                "numeric",
                "30",
            ],
        ]

        progress = self._run_progress_test(program_data, user_data_rows)

        # Expected points: 10 (weight) * (50 / 100) = 5 points
        self.assertEqual(progress["current_points"], 5)

    def test_weekly_cumulative_binary_scoring(self):
        """Test weekly cumulative objective with binary scoring (fail and pass)."""
        start_date = datetime.now().date()
        days_since_monday = start_date.weekday()
        monday = start_date - timedelta(days=days_since_monday)
        end_date = monday + timedelta(days=6)

        program_data = {
            "name": "Test Program",
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_weekly_binary",
                    "name": "Workout 3 times",
                    "type": "cumulative",
                    "frequency": "weekly",
                    "scoring": "binary",
                    "target_value": 3,
                    "weight": 20,
                    "start_value": 0,
                    "unit": "workouts",
                    "importance": "important",
                }
            ],
            "tasks": [],
        }

        # Scenario 1: Fail (2 out of 3 workouts)
        user_data_rows_fail = [
            [monday.strftime("%Y-%m-%d"), "obj_weekly_binary", "numeric", "1"],
            [
                (monday + timedelta(days=2)).strftime("%Y-%m-%d"),
                "obj_weekly_binary",
                "numeric",
                "1",
            ],
        ]
        progress_fail = self._run_progress_test(program_data, user_data_rows_fail)
        # Expected points: 0 (since target not met)
        # Importance multiplier is x2, but 0 * 2 = 0
        self.assertEqual(progress_fail["current_points"], 0)

        # Scenario 2: Pass (3 out of 3 workouts)
        user_data_rows_pass = [
            [monday.strftime("%Y-%m-%d"), "obj_weekly_binary", "numeric", "1"],
            [
                (monday + timedelta(days=2)).strftime("%Y-%m-%d"),
                "obj_weekly_binary",
                "numeric",
                "1",
            ],
            [
                (monday + timedelta(days=4)).strftime("%Y-%m-%d"),
                "obj_weekly_binary",
                "numeric",
                "1",
            ],
        ]
        progress_pass = self._run_progress_test(program_data, user_data_rows_pass)
        # Expected points: 20 (weight) * 2 (importance) = 40 points
        self.assertEqual(progress_pass["current_points"], 40)

    def test_program_latest_proportional_scoring(self):
        """Test program 'latest' objective with proportional scoring."""
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=29)  # 30-day program

        program_data = {
            "name": "Test Program",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_program_latest",
                    "name": "Weigh 75kg",
                    "type": "latest",
                    "frequency": "program",
                    "scoring": "proportional",
                    "target_value": 75,
                    "weight": 50,
                    "start_value": 80,
                    "unit": "kg",
                    "importance": "indispensable",
                }
            ],
            "tasks": [],
        }

        # Multiple weight entries
        user_data_rows = [
            [start_date.strftime("%Y-%m-%d"), "obj_program_latest", "numeric", "78"],
            [
                (start_date + timedelta(days=10)).strftime("%Y-%m-%d"),
                "obj_program_latest",
                "numeric",
                "77",
            ],
            [
                (start_date + timedelta(days=20)).strftime("%Y-%m-%d"),
                "obj_program_latest",
                "numeric",
                "76",
            ],  # This is the latest value
        ]

        progress = self._run_progress_test(program_data, user_data_rows)

        # NOTE: The current logic for proportional scoring on 'latest' objectives doesn't make sense
        # for goals like weight loss (where lower is better).
        # Expected points: 50 (weight) * ((80-76)/(80-75)) * 3 (importance)
        expected_points = 50 * ((80 - 76) / (80 - 75)) * 3
        self.assertAlmostEqual(progress["current_points"], expected_points)

    def test_program_latest_binary_scoring(self):
        """Test program 'latest' objective with binary scoring."""
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=29)

        program_data = {
            "name": "Test Program",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "objectives": [
                {
                    "id": "obj_program_latest_binary",
                    "name": "Reach level 10",
                    "type": "latest",
                    "frequency": "program",
                    "scoring": "binary",
                    "target_value": 10,
                    "weight": 100,
                    "start_value": 1,
                    "unit": "level",
                    "importance": "bien",
                }
            ],
            "tasks": [],
        }

        # Scenario 1: Fail (latest level is 9)
        user_data_fail = [
            [
                start_date.strftime("%Y-%m-%d"),
                "obj_program_latest_binary",
                "numeric",
                "5",
            ],
            [
                (start_date + timedelta(days=15)).strftime("%Y-%m-%d"),
                "obj_program_latest_binary",
                "numeric",
                "9",
            ],
        ]
        progress_fail = self._run_progress_test(program_data, user_data_fail)
        self.assertEqual(progress_fail["current_points"], 0)

        # Scenario 2: Pass (latest level is 10)
        user_data_pass = [
            [
                start_date.strftime("%Y-%m-%d"),
                "obj_program_latest_binary",
                "numeric",
                "5",
            ],
            [
                (start_date + timedelta(days=15)).strftime("%Y-%m-%d"),
                "obj_program_latest_binary",
                "numeric",
                "10",
            ],
        ]
        progress_pass = self._run_progress_test(program_data, user_data_pass)
        self.assertEqual(progress_pass["current_points"], 100)


if __name__ == "__main__":
    unittest.main()
