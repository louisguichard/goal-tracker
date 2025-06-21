from flask import Flask, render_template, request, jsonify, redirect, url_for
from tracker import ProgressTracker
from datetime import datetime, timedelta
import os
import glob
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)

# Initialize tracker
tracker = ProgressTracker()


@app.route("/")
def index():
    """Dashboard"""
    tracker.load_program()
    if not tracker.program:
        return redirect(url_for("setup"))

    user_data = tracker.get_user_data()
    progress = tracker.compute_progress(user_data)

    return render_template(
        "dashboard.html",
        program=tracker.program,
        progress=progress,
        user_data=user_data,
    )


@app.route("/daily")
def daily():
    """Daily tracking page"""
    tracker.load_program()
    if not tracker.program:
        return redirect(url_for("setup"))

    # Get selected date from query parameter, default to today
    selected_date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = datetime.now().date()

    user_data = tracker.get_user_data()

    # Get data for the selected date
    date_str = selected_date.strftime("%Y-%m-%d")
    day_data = user_data.get(date_str, {})

    return render_template(
        "daily.html",
        program=tracker.program,
        selected_date=selected_date,
        day_data=day_data,
        user_data=user_data,
    )


@app.route("/todo")
def todo():
    """To Do page with tasks"""
    tracker.load_program()
    if not tracker.program:
        return redirect(url_for("setup"))

    user_data = tracker.get_user_data()

    # Calculate task completion status
    task_status = {}
    for task in tracker.program.tasks:
        is_completed = False
        for date_str in user_data:
            if task.id in user_data[date_str] and user_data[date_str][task.id]["value"]:
                is_completed = True
                break
        task_status[task.id] = is_completed

    return render_template(
        "todo.html",
        program=tracker.program,
        task_status=task_status,
        user_data=user_data,
    )


@app.route("/setup")
def setup():
    """Program setup page"""
    tracker.load_program()
    return render_template("setup.html", program=tracker.program)


@app.route("/progress-explanation")
def progress_explanation():
    """Progress calculation explanation page"""
    tracker.load_program()
    if not tracker.program:
        return redirect(url_for("setup"))

    user_data = tracker.get_user_data()

    # Calculate detailed breakdown
    breakdown = calculate_detailed_breakdown(tracker.program, user_data)
    progress = tracker.compute_progress(user_data)

    return render_template(
        "progress_explanation.html",
        program=tracker.program,
        breakdown=breakdown,
        progress=progress,
        user_data=user_data,
    )


@app.route("/api/save_program", methods=["POST"])
def save_program():
    """Save program configuration"""
    data = request.get_json()

    # Validate and process objectives
    objectives = []
    for obj_data in data.get("objectives", []):
        weight = (
            1
            if obj_data["frequency"] == "daily"
            else (5 if obj_data["frequency"] == "weekly" else 15)
        )
        objectives.append(
            {
                "id": obj_data["id"],
                "name": obj_data["name"],
                "type": obj_data["type"],
                "frequency": obj_data["frequency"],
                "scoring": obj_data.get("scoring", "proportional"),
                "target_value": obj_data.get("target_value", 1),
                "weight": obj_data.get("weight", weight),
                "start_value": obj_data.get("start_value", 0),
                "unit": obj_data.get("unit", ""),
            }
        )

    # Validate and process tasks
    tasks = []
    for task_data in data.get("tasks", []):
        tasks.append(
            {
                "id": task_data["id"],
                "name": task_data["name"],
                "weight": task_data.get("weight", 5),
            }
        )

    program_data = {
        "name": data["name"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "objectives": objectives,
        "tasks": tasks,
    }

    tracker.save_program(program_data)
    return jsonify({"success": True})


@app.route("/api/save_data", methods=["POST"])
def save_data():
    """Save user progress data"""
    data = request.get_json()
    date = data["date"]
    item_id = data["item_id"]
    item_type = data["type"]
    value = data["value"]

    tracker.save_user_data_entry(date, item_id, item_type, value)
    return jsonify({"success": True})


@app.route("/api/progress")
def get_progress():
    """Get current progress data"""
    tracker.load_program()
    user_data = tracker.get_user_data()
    progress = tracker.compute_progress(user_data)
    return jsonify(progress)


@app.route("/api/dashboard")
def get_dashboard_data():
    """Get comprehensive dashboard data including weekly and daily breakdowns"""
    tracker.load_program()
    if not tracker.program:
        return jsonify({"error": "No program configured"}), 400

    user_data = tracker.get_user_data()
    progress = tracker.compute_progress(user_data)

    # Calculate weekly progress
    weekly_progress = calculate_weekly_progress(tracker.program, user_data)

    # Calculate daily status
    daily_status = calculate_daily_status(tracker.program, user_data)

    return jsonify(
        {
            "global_progress": progress["current_progress"] if progress else 0,
            "expected_progress": progress["expected_progress"] if progress else 0,
            "weekly_progress": weekly_progress,
            "daily_status": daily_status,
            "program_start": tracker.program.start_date,
            "program_end": tracker.program.end_date,
        }
    )


@app.route("/api/configs", methods=["GET"])
def list_configs():
    """List available configuration files"""
    try:
        config_files = glob.glob(os.path.join(tracker.data_dir, "*.json"))
        # Exclude the main program.json
        config_files = [
            os.path.basename(f)
            for f in config_files
            if os.path.basename(f) != "program.json"
        ]
        return jsonify(config_files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/save_config", methods=["POST"])
def save_config():
    """Save a named program configuration"""
    data = request.get_json()
    filename = data.get("name")
    config_data = data.get("config")

    if not filename or not config_data:
        return jsonify({"success": False, "error": "Missing name or config data"}), 400

    # Sanitize filename
    filename = secure_filename(filename)
    if not filename.endswith(".json"):
        filename += ".json"

    # Avoid overwriting main program file through this endpoint
    if filename == "program.json":
        return jsonify(
            {"success": False, "error": "Cannot overwrite main program file"}
        ), 400

    try:
        save_path = os.path.join(tracker.data_dir, filename)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/load_config", methods=["GET"])
def load_config():
    """Load a named program configuration"""
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    # Sanitize filename
    filename = secure_filename(filename)

    try:
        load_path = os.path.join(tracker.data_dir, filename)
        if os.path.exists(load_path):
            with open(load_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            return jsonify(config_data)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/programs", methods=["GET"])
def list_programs():
    """List all available programs"""
    try:
        programs = tracker.list_available_programs()
        return jsonify(
            [
                {
                    "id": p.id,
                    "name": p.name,
                    "folder_path": p.folder_path,
                    "has_data": p.has_data,
                    "is_current": p.id == tracker.current_program_id,
                }
                for p in programs
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/select_program", methods=["POST"])
def select_program():
    """Select a program to work with"""
    data = request.get_json()
    program_id = data.get("program_id")

    if not program_id:
        return jsonify({"success": False, "error": "Program ID is required"}), 400

    try:
        tracker.select_program(program_id)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/create_program", methods=["POST"])
def create_program():
    """Create a new program"""
    data = request.get_json()
    program_id = data.get("program_id")
    program_name = data.get("program_name")

    if not program_id or not program_name:
        return jsonify(
            {"success": False, "error": "Program ID and name are required"}
        ), 400

    try:
        # Sanitize program_id
        program_id = program_id.lower().replace(" ", "_").replace("-", "_")
        program_id = "".join(c for c in program_id if c.isalnum() or c == "_")

        created_id = tracker.create_new_program(program_id, program_name)
        return jsonify({"success": True, "program_id": created_id})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/current_program", methods=["GET"])
def get_current_program():
    """Get current program information"""
    try:
        programs = tracker.list_available_programs()
        current_program = None
        for p in programs:
            if p.id == tracker.current_program_id:
                current_program = {
                    "id": p.id,
                    "name": p.name,
                    "folder_path": p.folder_path,
                    "has_data": p.has_data,
                }
                break

        return jsonify(
            {
                "current_program": current_program,
                "current_program_id": tracker.current_program_id,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def calculate_weekly_progress(program, user_data):
    """Calculate progress for each week of the program"""
    start_date = datetime.strptime(program.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(program.end_date, "%Y-%m-%d").date()

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
        week_progress = calculate_week_progress(
            program, user_data, week_start, week_end
        )

        weekly_data.append(
            {"week": f"Week {week_num + 1}", "progress": round(week_progress, 1)}
        )

    return weekly_data


def calculate_week_progress(program, user_data, week_start, week_end):
    """Calculate progress for a specific week"""
    total_points = 0
    earned_points = 0

    # Calculate points from daily objectives
    for obj in program.objectives:
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
    for obj in program.objectives:
        if obj.frequency == "weekly":
            total_points += obj.weight

            # Count achievements in this week
            week_achievements = 0
            for day_offset in range(7):
                current_date = week_start + timedelta(days=day_offset)
                date_str = current_date.strftime("%Y-%m-%d")

                if date_str in user_data and obj.id in user_data[date_str]:
                    if obj.type == "checkbox" and user_data[date_str][obj.id]["value"]:
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


def calculate_daily_status(program, user_data):
    """Calculate status for each day of the program"""
    start_date = datetime.strptime(program.start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(program.end_date, "%Y-%m-%d").date()
    today = datetime.now().date()

    daily_status = {}

    current_date = start_date
    while current_date <= min(end_date, today):
        date_str = current_date.strftime("%Y-%m-%d")

        # Calculate daily objectives completion
        daily_objectives = [
            obj for obj in program.objectives if obj.frequency == "daily"
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


def calculate_detailed_breakdown(program, user_data):
    """Calculate detailed breakdown of points for each objective and task"""
    breakdown = {
        "objectives": [],
        "tasks": [],
        "totals": {"current_points": 0, "total_points": 0},
    }

    # Calculate for objectives
    for obj in program.objectives:
        obj_breakdown = {
            "objective": obj,
            "current_points": 0,
            "total_points": 0,
            "daily_breakdown": {},
        }

        # Calculate total possible points
        start_date = datetime.strptime(program.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(program.end_date, "%Y-%m-%d").date()
        total_days = (end_date - start_date).days + 1

        if obj.frequency == "daily":
            obj_breakdown["total_points"] = obj.weight * total_days
        elif obj.frequency == "weekly":
            obj_breakdown["total_points"] = obj.weight * (total_days // 7)
        elif obj.frequency == "program":
            obj_breakdown["total_points"] = obj.weight

        # Calculate current points using tracker's method
        obj_breakdown["current_points"] = calculate_objective_points_detailed(
            obj, user_data, program
        )

        # Calculate daily breakdown for visualization
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            day_points = 0

            if date_str in user_data and obj.id in user_data[date_str]:
                if obj.frequency == "daily" and user_data[date_str][obj.id]["value"]:
                    day_points = obj.weight

            obj_breakdown["daily_breakdown"][date_str] = {
                "points": day_points,
                "value": user_data.get(date_str, {}).get(obj.id, {}).get("value", 0),
            }
            current_date += timedelta(days=1)

        breakdown["objectives"].append(obj_breakdown)
        breakdown["totals"]["current_points"] += obj_breakdown["current_points"]
        breakdown["totals"]["total_points"] += obj_breakdown["total_points"]

    # Calculate for tasks
    for task in program.tasks:
        task_breakdown = {
            "task": task,
            "current_points": 0,
            "total_points": task.weight,
            "completed": False,
            "completion_date": None,
        }

        # Check if task is completed
        for date_str in user_data:
            if task.id in user_data[date_str] and user_data[date_str][task.id]["value"]:
                task_breakdown["current_points"] = task.weight
                task_breakdown["completed"] = True
                task_breakdown["completion_date"] = date_str
                break

        breakdown["tasks"].append(task_breakdown)
        breakdown["totals"]["current_points"] += task_breakdown["current_points"]
        breakdown["totals"]["total_points"] += task_breakdown["total_points"]

    return breakdown


def calculate_objective_points_detailed(objective, user_data, program):
    """Calculate points for a specific objective (simplified version for breakdown)"""
    if objective.frequency == "daily":
        total = 0
        for date in user_data:
            if objective.id in user_data[date]:
                if user_data[date][objective.id]["value"]:
                    total += objective.weight
        return total
    elif objective.frequency == "weekly":
        # Simplified weekly calculation for now
        return 0  # TODO: Implement detailed weekly calculation
    elif objective.frequency == "program":
        # Simplified program calculation for now
        return 0  # TODO: Implement detailed program calculation
    else:
        return 0


if __name__ == "__main__":
    app.run(debug=True)
