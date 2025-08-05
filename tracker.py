import json
import csv
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class Objective:
    id: str
    name: str
    type: str  # 'checkbox', 'cumulative' or 'latest'
    frequency: str  # 'daily', 'weekly', 'program'
    scoring: str  # 'binary' (all points or none) or 'proportional' (points based on progress ratio)
    start_value: int
    target_value: int
    unit: str = ""
    weight: int = 1
    importance: str = "bien"  # 'indispensable', 'important', 'bien'


@dataclass
class Task:
    id: str
    name: str
    weight: int


@dataclass
class Program:
    name: str
    start_date: str
    end_date: str
    objectives: list[Objective]
    tasks: list[Task]


@dataclass
class ProgramInfo:
    id: str
    name: str
    folder_path: str
    has_data: bool = False


class ProgressTracker:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.current_program_id = None
        self.program = None

        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)

        # Load current program selection
        self._load_current_program_selection()

    def _load_current_program_selection(self):
        """Load the currently selected program ID"""
        current_file = os.path.join(self.data_dir, "current_program.txt")
        if os.path.exists(current_file):
            with open(current_file, "r", encoding="utf-8") as f:
                self.current_program_id = f.read().strip()
        else:
            # If no current program, use default if it exists
            if os.path.exists(os.path.join(self.data_dir, "program.json")):
                self.current_program_id = "default"
            else:
                self.current_program_id = None

    def _save_current_program_selection(self):
        """Save the currently selected program ID"""
        current_file = os.path.join(self.data_dir, "current_program.txt")
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(self.current_program_id or "")

    def get_program_folder(self):
        """Get the folder path for the current program"""
        if self.current_program_id == "default":
            return self.data_dir
        elif self.current_program_id:
            return os.path.join(self.data_dir, self.current_program_id)
        else:
            return self.data_dir

    def get_program_file(self):
        """Get the program.json file path for the current program"""
        return os.path.join(self.get_program_folder(), "program.json")

    def get_user_data_file(self):
        """Get the user_data.csv file path for the current program"""
        return os.path.join(self.get_program_folder(), "user_data.csv")

    def list_available_programs(self):
        """List all available programs"""
        programs = []

        # Check for default program (files directly in data directory)
        if os.path.exists(os.path.join(self.data_dir, "program.json")):
            program_data = self._load_program_data(
                os.path.join(self.data_dir, "program.json")
            )
            has_data = os.path.exists(os.path.join(self.data_dir, "user_data.csv"))
            programs.append(
                ProgramInfo(
                    id="default",
                    name=program_data.get("name", "Default Program")
                    if program_data
                    else "Default Program",
                    folder_path=self.data_dir,
                    has_data=has_data,
                )
            )

        # Check for programs in subdirectories
        for item in os.listdir(self.data_dir):
            item_path = os.path.join(self.data_dir, item)
            if os.path.isdir(item_path):
                program_file = os.path.join(item_path, "program.json")
                if os.path.exists(program_file):
                    program_data = self._load_program_data(program_file)
                    has_data = os.path.exists(os.path.join(item_path, "user_data.csv"))
                    programs.append(
                        ProgramInfo(
                            id=item,
                            name=program_data.get("name", item)
                            if program_data
                            else item,
                            folder_path=item_path,
                            has_data=has_data,
                        )
                    )

        return programs

    def _load_program_data(self, program_file):
        """Load program data from a JSON file"""
        try:
            with open(program_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    def select_program(self, program_id):
        """Select a program by ID"""
        available_programs = self.list_available_programs()
        program_ids = [p.id for p in available_programs]

        if program_id not in program_ids:
            raise ValueError(
                f"Program '{program_id}' not found. Available programs: {program_ids}"
            )

        self.current_program_id = program_id
        self._save_current_program_selection()
        self.program = None  # Force reload

    def create_new_program(self, program_id, program_name):
        """Create a new program folder and basic structure"""
        if program_id == "default":
            raise ValueError("Cannot create program with ID 'default'")

        program_folder = os.path.join(self.data_dir, program_id)
        os.makedirs(program_folder, exist_ok=True)

        # Create empty program.json
        program_data = {
            "name": program_name,
            "start_date": "",
            "end_date": "",
            "objectives": [],
            "tasks": [],
        }

        program_file = os.path.join(program_folder, "program.json")
        with open(program_file, "w", encoding="utf-8") as f:
            json.dump(program_data, f, indent=2, ensure_ascii=False)

        # Create empty user_data.csv
        user_data_file = os.path.join(program_folder, "user_data.csv")
        with open(user_data_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "item_id", "type", "value"])

        return program_id

    def load_program(self):
        """Load program from JSON file"""
        program_file = self.get_program_file()
        if os.path.exists(program_file):
            with open(program_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                objectives = [Objective(**obj) for obj in data["objectives"]]
                tasks = [Task(**task) for task in data["tasks"]]
                self.program = Program(
                    name=data["name"],
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    objectives=objectives,
                    tasks=tasks,
                )

    def save_program(self, program_data):
        """Save program to JSON file"""
        program_file = self.get_program_file()

        # Ensure the program folder exists
        program_folder = self.get_program_folder()
        os.makedirs(program_folder, exist_ok=True)

        with open(program_file, "w", encoding="utf-8") as f:
            json.dump(program_data, f, indent=2, ensure_ascii=False)
        self.load_program()

    def get_user_data(self):
        """Load user progress data from CSV"""
        user_data = {}
        user_data_file = self.get_user_data_file()
        if os.path.exists(user_data_file):
            with open(user_data_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    date = row["date"]
                    if date not in user_data:
                        user_data[date] = {}

                    # Improved value conversion
                    value = row["value"]
                    try:
                        # Try to convert to float first, then to int if it's a whole number
                        float_value = float(value)
                        if float_value.is_integer():
                            converted_value = int(float_value)
                        else:
                            converted_value = float_value
                    except (ValueError, TypeError):
                        # If conversion fails, keep as string
                        converted_value = value

                    user_data[date][row["item_id"]] = {
                        "type": row["type"],
                        "value": converted_value,
                    }
        return user_data

    def save_user_data_entry(self, date, item_id, item_type, value):
        """Save a single user data entry to CSV"""
        user_data_file = self.get_user_data_file()

        # Ensure the program folder exists
        program_folder = self.get_program_folder()
        os.makedirs(program_folder, exist_ok=True)

        # Read existing data
        existing_data = []
        fieldnames = ["date", "item_id", "type", "value"]
        if os.path.exists(user_data_file):
            with open(user_data_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    fieldnames = reader.fieldnames
                existing_data = list(reader)

        # Special handling for undoing tasks
        if item_type == "task" and int(value) == 0:
            # Remove all entries for this task id
            updated_data = [row for row in existing_data if row["item_id"] != item_id]

            with open(user_data_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated_data)
            return

        # Update or add entry
        found = False
        for row in existing_data:
            if row["date"] == date and row["item_id"] == item_id:
                row["value"] = str(value)
                found = True
                break

        if not found:
            existing_data.append(
                {
                    "date": date,
                    "item_id": item_id,
                    "type": item_type,
                    "value": str(value),
                }
            )

        # Write back to file
        with open(user_data_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_data)

    def _get_importance_multiplier(self, importance):
        """Get the point multiplier for importance level"""
        multipliers = {"indispensable": 3, "important": 2, "bien": 1}
        return multipliers.get(importance, 1)

    def get_objective_max_points(self, objective):
        """Calculate total possible points for a single objective."""
        if not self.program or not self.program.start_date or not self.program.end_date:
            return 0

        try:
            start_date = datetime.strptime(self.program.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.program.end_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return 0

        total_days = (end_date - start_date).days + 1
        weekly_info = self._get_weekly_boundaries(start_date, end_date)

        multiplier = self._get_importance_multiplier(
            getattr(objective, "importance", "bien")
        )

        obj_total_points = 0
        if objective.frequency == "daily":
            obj_total_points = objective.weight * total_days * multiplier
        elif objective.frequency == "weekly":
            obj_total_points = (
                objective.weight * weekly_info["num_complete_weeks"] * multiplier
            )
        elif objective.frequency == "program":
            obj_total_points = objective.weight * multiplier
        else:
            print(
                f"⚠️ Unknown objective frequency for objective {objective.id}: {objective.frequency}"
            )
            obj_total_points = 0

        return obj_total_points

    def _compute_objective_points(self, objective, user_data):
        """compute points for a specific objective based on type"""
        if objective.frequency == "daily":
            return self._compute_daily_objective_points(objective, user_data)
        elif objective.frequency == "weekly":
            return self._compute_weekly_objective_points(objective, user_data)
        elif objective.frequency == "program":
            return self._compute_program_objective_points(objective, user_data)
        else:
            print(
                f"⚠️ Unknown frequency for objective {objective.id}: '{objective.frequency}'"
            )
            return 0

    def _compute_daily_objective_points(self, objective, user_data):
        """Compute points for daily objectives"""
        total = 0
        for date in user_data:
            if objective.id in user_data[date]:
                if user_data[date][objective.id]["value"]:
                    if objective.type == "checkbox":
                        total += objective.weight
                    else:
                        print(
                            f"⚠️ Only 'checkbox' type has been implemented for daily objectives. Objective {objective.id} is of type '{objective.type}'"
                        )
                        return 0
        # Apply importance multiplier
        multiplier = self._get_importance_multiplier(
            getattr(objective, "importance", "bien")
        )
        return total * multiplier

    def _get_weekly_boundaries(self, start_date, end_date):
        """Calculate weekly boundaries for the program period"""
        # 1) Find first Monday
        if start_date.weekday() == 0:
            first_monday = start_date
        else:
            first_monday = start_date + timedelta(days=7 - start_date.weekday())

        # 2) Find last Sunday
        if end_date.weekday() == 6:
            last_sunday = end_date
        else:
            last_sunday = end_date - timedelta(days=end_date.weekday() + 1)

        # 3) Calculate number of complete weeks
        if last_sunday < first_monday:
            num_complete_weeks = 0
        else:
            num_complete_weeks = ((last_sunday - first_monday).days + 1) // 7

        return {
            "first_monday": first_monday,
            "last_sunday": last_sunday,
            "num_complete_weeks": num_complete_weeks,
        }

    def _compute_weekly_objective_points(self, objective, user_data):
        """Compute points for weekly objectives"""
        if not self.program or not self.program.start_date or not self.program.end_date:
            return 0

        try:
            start_date = datetime.strptime(self.program.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.program.end_date, "%Y-%m-%d").date()
        except ValueError:
            return 0

        # Get weekly boundaries
        weekly_info = self._get_weekly_boundaries(start_date, end_date)
        first_monday = weekly_info["first_monday"]
        last_sunday = weekly_info["last_sunday"]
        num_weeks = weekly_info["num_complete_weeks"]

        if num_weeks == 0:
            return 0

        # 4) Group data by weeks
        weeks = {idx: [] for idx in range(num_weeks)}
        for date_str in user_data:
            if objective.id in user_data[date_str]:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if date >= first_monday and date <= last_sunday:
                    week_index = (date - first_monday).days // 7
                    weeks[week_index].append(user_data[date_str][objective.id]["value"])

        # 5) Compute points for each week
        total_points = 0
        for week_index, week_data in weeks.items():
            # Compute week value
            if objective.type == "checkbox":
                week_value = len(week_data)
            elif objective.type == "cumulative":
                # Convert all values to numbers and sum them
                numeric_data = []
                for val in week_data:
                    try:
                        numeric_data.append(float(val) if val else 0)
                    except (ValueError, TypeError):
                        numeric_data.append(0)
                week_value = sum(numeric_data)
            else:
                print(
                    f"⚠️ Only 'checkbox' and 'cumulative' types have been implemented for weekly objectives. Objective {objective.id} is of type '{objective.type}'"
                )
                return 0

            # Apply scoring method
            if objective.scoring == "binary":
                if week_value >= objective.target_value:
                    total_points += objective.weight
            elif objective.scoring == "proportional":
                total_points += objective.weight * week_value / objective.target_value
            else:
                print(
                    f"⚠️ Unknown scoring method for objective {objective.id}: '{objective.scoring}'"
                )
                return 0

        # Apply importance multiplier
        multiplier = self._get_importance_multiplier(
            getattr(objective, "importance", "bien")
        )
        return total_points * multiplier

    def _compute_program_objective_points(self, objective, user_data):
        """Compute points for program-wide objectives"""
        start_date = datetime.strptime(self.program.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(self.program.end_date, "%Y-%m-%d").date()
        total_days = (end_date - start_date).days + 1
        # Select data
        objective_data = [
            user_data[date_str][objective.id]["value"]
            for date_str in user_data
            if objective.id in user_data[date_str]
        ]

        # Compute value
        if objective.type == "checkbox":
            value = len(objective_data)
        elif objective.type == "cumulative":
            # Convert all values to numbers and sum them
            numeric_data = []
            for val in objective_data:
                try:
                    numeric_data.append(float(val) if val else 0)
                except (ValueError, TypeError):
                    numeric_data.append(0)
            value = sum(numeric_data)
        elif objective.type == "latest":
            # Get the latest value and convert to number
            latest_val = objective_data[-1] if objective_data else 0
            try:
                value = float(latest_val) if latest_val else 0
            except (ValueError, TypeError):
                value = 0
        else:
            print(
                f"⚠️ Unknown objective type for objective {objective.id}: '{objective.type}'"
            )
            return 0

        # Apply scoring method
        points = 0
        if objective.scoring == "binary":
            if value >= objective.target_value:
                points = objective.weight
        elif objective.scoring == "proportional":
            # Handle cases where the goal is to decrease the value (e.g., weight loss)
            if objective.start_value > objective.target_value:
                # Progress is measured by how much the value has decreased
                progress_fraction = (objective.start_value - value) / (
                    objective.start_value - objective.target_value
                )
                points = objective.weight * progress_fraction
            else:
                # Regular proportional scoring
                points = objective.weight * value / objective.target_value
        else:
            print(
                f"⚠️ Unknown scoring method for objective {objective.id}: '{objective.scoring}'"
            )
            return 0

        # Apply importance multiplier
        multiplier = self._get_importance_multiplier(
            getattr(objective, "importance", "bien")
        )
        return points * multiplier

    def compute_progress(self, user_data):
        "Compute current and expected progress"

        # Check if program is loaded
        if not self.program:
            print("⚠️ No program loaded")
            return None

        # If user data is not available, initialize to empty dict
        if not user_data:
            user_data = {}

        # Compute program dates
        try:
            start_date = datetime.strptime(self.program.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.program.end_date, "%Y-%m-%d").date()
        except ValueError:
            print("⚠️ Invalid program dates")
            return None
        today = datetime.now().date()
        total_days = (end_date - start_date).days + 1

        if today < start_date:
            elapsed_days = 0
        elif today > end_date:
            elapsed_days = total_days
        else:
            elapsed_days = (today - start_date).days + 1

        # Calculate week boundaries for weekly objectives
        weekly_info = self._get_weekly_boundaries(start_date, end_date)

        # Compute progress
        current_points = 0
        total_points = 0
        expected_points = 0

        # Process objectives
        for obj in self.program.objectives:
            # Get importance multiplier
            multiplier = self._get_importance_multiplier(
                getattr(obj, "importance", "bien")
            )

            if obj.frequency == "daily":
                # Daily objectives: each day in program period can contribute
                obj_total_points = obj.weight * total_days * multiplier
                obj_expected_points = obj.weight * elapsed_days * multiplier

            elif obj.frequency == "weekly":
                # Weekly objectives: only complete weeks can contribute
                obj_total_points = (
                    obj.weight * weekly_info["num_complete_weeks"] * multiplier
                )

                # Calculate expected points for weekly objectives
                if weekly_info["num_complete_weeks"] == 0:
                    obj_expected_points = 0
                else:
                    # Count how many complete weeks have elapsed
                    elapsed_complete_weeks = 0

                    if today >= weekly_info["first_monday"]:
                        if today > weekly_info["last_sunday"]:
                            # All weeks have elapsed
                            elapsed_complete_weeks = weekly_info["num_complete_weeks"]
                        else:
                            # Calculate how many complete weeks have fully elapsed
                            days_since_first_monday = (
                                today - weekly_info["first_monday"]
                            ).days
                            elapsed_complete_weeks = (days_since_first_monday + 1) // 7

                            # Make sure we don't exceed the total number of complete weeks
                            elapsed_complete_weeks = min(
                                elapsed_complete_weeks,
                                weekly_info["num_complete_weeks"],
                            )

                    obj_expected_points = (
                        obj.weight * elapsed_complete_weeks * multiplier
                    )

            elif obj.frequency == "program":
                # Program objectives: points based on half the total days
                obj_total_points = obj.weight * multiplier
                obj_expected_points = (
                    obj.weight * (elapsed_days / total_days) * multiplier
                )
            else:
                print(
                    f"⚠️ Unknown objective frequency for objective {obj.id}: {obj.frequency}"
                )
                obj_total_points = 0
                obj_expected_points = 0

            total_points += obj_total_points
            expected_points += obj_expected_points

            # Compute objective points
            current_points += self._compute_objective_points(obj, user_data)

        # Process tasks
        for task in self.program.tasks:
            total_points += task.weight
            expected_points += task.weight * (elapsed_days / total_days)

            # Check if task is completed
            for date_str in user_data:
                if (
                    task.id in user_data[date_str]
                    and user_data[date_str][task.id]["value"]
                ):
                    current_points += task.weight
                    break

        # Compute percentages
        if total_points > 0:
            current_progress = current_points / total_points * 100
            expected_progress = expected_points / total_points * 100
        else:
            current_progress = 0
            expected_progress = 0

        return {
            "current_points": current_points,
            "total_points": total_points,
            "current_progress": round(current_progress, 1),
            "expected_progress": round(expected_progress, 1),
            "elapsed_days": elapsed_days,
            "total_days": total_days,
            "is_on_track": current_progress >= expected_progress,
        }

    def calculate_weekly_progress(self, user_data):
        """Calculate progress for each week of the program"""
        if not self.program or not self.program.start_date or not self.program.end_date:
            return []

        try:
            start_date = datetime.strptime(self.program.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.program.end_date, "%Y-%m-%d").date()
        except ValueError:
            return []

        # Find first Monday and last Sunday for complete weeks
        if start_date.weekday() == 0:
            first_monday = start_date
        else:
            first_monday = start_date + timedelta(days=7 - start_date.weekday())

        if end_date.weekday() == 6:
            last_sunday = end_date
        else:
            last_sunday = end_date - timedelta(days=end_date.weekday() + 1)

        # Calculate number of weeks
        if last_sunday < first_monday:
            # Program is shorter than a week
            return [{"week": "Week 1", "progress": 0}]

        num_weeks = ((last_sunday - first_monday).days + 1) // 7

        weekly_data = []
        for week_num in range(num_weeks):
            week_start = first_monday + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=6)

            # Calculate progress for this week
            week_progress = self.calculate_week_progress(
                user_data, week_start, week_end
            )

            weekly_data.append(
                {"week": f"Week {week_num + 1}", "progress": round(week_progress, 1)}
            )

        return weekly_data

    def calculate_week_progress(self, user_data, week_start, week_end):
        """Calculate progress for a specific week"""
        total_points = 0
        earned_points = 0

        # Calculate points from daily objectives
        for obj in self.program.objectives:
            if obj.frequency == "daily":
                # Each day in the week can earn points
                for day_offset in range(7):
                    current_date = week_start + timedelta(days=day_offset)
                    date_str = current_date.strftime("%Y-%m-%d")

                    total_points += obj.weight

                    if date_str in user_data and obj.id in user_data[date_str]:
                        if user_data[date_str][obj.id]["value"]:
                            earned_points += obj.weight

        # Calculate points from weekly objectives
        for obj in self.program.objectives:
            if obj.frequency == "weekly":
                total_points += obj.weight

                # Count achievements in this week
                week_achievements = 0
                for day_offset in range(7):
                    current_date = week_start + timedelta(days=day_offset)
                    date_str = current_date.strftime("%Y-%m-%d")

                    if date_str in user_data and obj.id in user_data[date_str]:
                        if (
                            obj.type == "checkbox"
                            and user_data[date_str][obj.id]["value"]
                        ):
                            week_achievements += 1
                        elif obj.type == "cumulative":
                            week_achievements += user_data[date_str][obj.id]["value"]

                # Apply scoring
                if obj.scoring == "binary":
                    if week_achievements >= obj.target_value:
                        earned_points += obj.weight
                elif obj.scoring == "proportional":
                    earned_points += obj.weight * min(
                        week_achievements / obj.target_value, 1.0
                    )

        return (earned_points / total_points * 100) if total_points > 0 else 0

    def calculate_daily_status(self, user_data):
        """Calculate status for each day of the program"""
        if not self.program or not self.program.start_date or not self.program.end_date:
            return {}

        try:
            start_date = datetime.strptime(self.program.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.program.end_date, "%Y-%m-%d").date()
        except ValueError:
            return {}

        today = datetime.now().date()

        daily_status = {}

        current_date = start_date
        while current_date <= min(end_date, today):
            date_str = current_date.strftime("%Y-%m-%d")

            # Calculate daily objectives completion
            daily_objectives = [
                obj for obj in self.program.objectives if obj.frequency == "daily"
            ]

            if not daily_objectives:
                # No daily objectives, skip
                current_date += timedelta(days=1)
                continue

            completed = 0
            total = len(daily_objectives)

            for obj in daily_objectives:
                if date_str in user_data and obj.id in user_data[date_str]:
                    if user_data[date_str][obj.id]["value"]:
                        completed += 1

            # Determine status
            if completed == total:
                daily_status[date_str] = "✅"  # Completed
            elif completed > 0:
                daily_status[date_str] = "⚠️"  # Partial
            else:
                daily_status[date_str] = "❌"  # Missed

            current_date += timedelta(days=1)

        return daily_status

    def calculate_detailed_breakdown(self, user_data):
        """Calculate detailed breakdown of points for each objective and task"""
        if not self.program or not self.program.start_date or not self.program.end_date:
            return {
                "objectives": [],
                "tasks": [],
                "totals": {"current_points": 0, "total_points": 0},
            }

        breakdown = {
            "objectives": [],
            "tasks": [],
            "totals": {"current_points": 0, "total_points": 0},
        }

        try:
            start_date = datetime.strptime(self.program.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.program.end_date, "%Y-%m-%d").date()
        except ValueError:
            return breakdown

        # Calculate for objectives
        for obj in self.program.objectives:
            obj_breakdown = {
                "objective": asdict(obj),
                "current_points": 0,
                "total_points": 0,
                "daily_breakdown": {},
            }

            # Calculate total possible points
            total_days = (end_date - start_date).days + 1

            if obj.frequency == "daily":
                obj_breakdown["total_points"] = obj.weight * total_days
            elif obj.frequency == "weekly":
                obj_breakdown["total_points"] = obj.weight * (total_days // 7)
            elif obj.frequency == "program":
                obj_breakdown["total_points"] = total_days / 2

            # Calculate current points using tracker's method
            obj_breakdown["current_points"] = self.calculate_objective_points_detailed(
                obj, user_data
            )

            # Calculate daily breakdown for visualization
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                day_points = 0

                if date_str in user_data and obj.id in user_data[date_str]:
                    if (
                        obj.frequency == "daily"
                        and user_data[date_str][obj.id]["value"]
                    ):
                        day_points = obj.weight

                obj_breakdown["daily_breakdown"][date_str] = {
                    "points": day_points,
                    "value": user_data.get(date_str, {})
                    .get(obj.id, {})
                    .get("value", 0),
                }
                current_date += timedelta(days=1)

            breakdown["objectives"].append(obj_breakdown)
            breakdown["totals"]["current_points"] += obj_breakdown["current_points"]
            breakdown["totals"]["total_points"] += obj_breakdown["total_points"]

        # Calculate for tasks
        for task in self.program.tasks:
            task_breakdown = {
                "task": asdict(task),
                "current_points": 0,
                "total_points": task.weight,
                "completed": False,
                "completion_date": None,
            }

            # Check if task is completed
            for date_str in user_data:
                if (
                    task.id in user_data[date_str]
                    and user_data[date_str][task.id]["value"]
                ):
                    task_breakdown["current_points"] = task.weight
                    task_breakdown["completed"] = True
                    task_breakdown["completion_date"] = date_str
                    break

            breakdown["tasks"].append(task_breakdown)
            breakdown["totals"]["current_points"] += task_breakdown["current_points"]
            breakdown["totals"]["total_points"] += task_breakdown["total_points"]

        return breakdown

    def calculate_objective_points_detailed(self, objective, user_data):
        """Calculate points for a specific objective (simplified version for breakdown)"""
        if objective.frequency == "daily":
            total = 0
            for date in user_data:
                if objective.id in user_data[date]:
                    if user_data[date][objective.id]["value"]:
                        total += objective.weight
            return total
        elif objective.frequency == "weekly":
            return self._compute_weekly_objective_points(objective, user_data)
        elif objective.frequency == "program":
            return self._compute_program_objective_points(objective, user_data)
        else:
            return 0
