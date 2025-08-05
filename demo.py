import json
import os
import random
from datetime import datetime, timedelta


def create_demo_program(data_dir="data"):
    """
    Generates a demo program and user data.
    The program spans 4 weeks over July and August 2025.
    The user is ahead of schedule with mostly good days.
    """
    program_id = "demo_program"
    program_name = "Demo Program"
    program_folder = os.path.join(data_dir, program_id)
    os.makedirs(program_folder, exist_ok=True)

    # --- Program Definition ---
    start_date = datetime(2025, 11, 24).date()
    end_date = datetime(2025, 12, 21).date()
    program_data = {
        "name": program_name,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "objectives": [
            {
                "id": "daily_check",
                "name": "Daily Check-in",
                "type": "checkbox",
                "frequency": "daily",
                "scoring": "binary",
                "start_value": 0,
                "target_value": 1,
                "weight": 5,
                "importance": "bien",
            },
            {
                "id": "daily_exercise",
                "name": "30 min exercise",
                "type": "checkbox",
                "frequency": "daily",
                "scoring": "binary",
                "start_value": 0,
                "target_value": 1,
                "weight": 5,
                "importance": "important",
            },
            {
                "id": "weekly_report",
                "name": "Weekly Report",
                "type": "checkbox",
                "frequency": "weekly",
                "scoring": "binary",
                "start_value": 0,
                "target_value": 1,
                "weight": 30,
                "importance": "important",
            },
            {
                "id": "project_milestone",
                "name": "Project Milestone",
                "type": "cumulative",
                "frequency": "program",
                "scoring": "proportional",
                "start_value": 0,
                "target_value": 5,
                "weight": 100,
                "importance": "indispensable",
            },
        ],
        "tasks": [
            {"id": "task1", "name": "Initial Setup", "weight": 20},
            {"id": "task2", "name": "Mid-term Review", "weight": 40},
        ],
    }
    program_file = os.path.join(program_folder, "program.json")
    with open(program_file, "w") as f:
        json.dump(program_data, f, indent=2)

    # --- User Data Generation ---
    # Today's date is set to be around 70% of the program duration
    today = start_date + timedelta(days=int((end_date - start_date).days * 0.7))
    print(f"Today: {today}")
    user_data = []

    # Define day types for daily objectives
    num_days_so_far = (today - start_date).days + 1
    num_fail_days = random.randint(2, 3)
    num_soso_days = random.randint(5, 6)
    num_good_days = num_days_so_far - num_fail_days - num_soso_days

    day_types = (
        ["fail"] * num_fail_days + ["soso"] * num_soso_days + ["good"] * num_good_days
    )
    random.shuffle(day_types)

    # Simulate progress
    for day_offset in range(num_days_so_far):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")

        day_type = day_types.pop()

        if day_type == "good":
            # Complete both daily objectives
            user_data.append([date_str, "daily_check", "objective", 1])
            user_data.append([date_str, "daily_exercise", "objective", 1])
        elif day_type == "soso":
            # Complete one of two daily objectives
            if random.random() < 0.5:
                user_data.append([date_str, "daily_check", "objective", 1])
            else:
                user_data.append([date_str, "daily_exercise", "objective", 1])
        # 'fail' days have no daily objective data

        # Weekly objective, completed on Sundays
        if current_date.weekday() == 6:  # Sunday
            user_data.append([date_str, "weekly_report", "objective", 1])

    # Program-level objective progress - being very generous to get ahead
    user_data.append(
        [start_date.strftime("%Y-%m-%d"), "project_milestone", "objective", 4]
    )
    user_data.append(
        [
            (start_date + timedelta(weeks=1)).strftime("%Y-%m-%d"),
            "project_milestone",
            "objective",
            4,
        ]
    )

    # Complete tasks
    user_data.append([start_date.strftime("%Y-%m-%d"), "task1", "task", 1])
    if today > start_date + timedelta(weeks=2):
        user_data.append(
            [(start_date + timedelta(weeks=2)).strftime("%Y-%m-%d"), "task2", "task", 1]
        )

    # Save user data to CSV
    user_data_file = os.path.join(program_folder, "user_data.csv")
    with open(user_data_file, "w") as f:
        f.write("date,item_id,type,value\n")
        for row in user_data:
            f.write(f"{row[0]},{row[1]},{row[2]},{row[3]}\n")

    return program_id


if __name__ == "__main__":
    demo_id = create_demo_program()
    print(f"Demo program created with ID: {demo_id}")
    print("To run the demo, use the command: python app.py --demo")
