from flask import Flask, render_template, request, jsonify, redirect, url_for, g
from tracker import ProgressTracker
from datetime import datetime
import os
import glob
from werkzeug.utils import secure_filename
import json
import shutil

app = Flask(__name__)

# Initialize tracker
tracker = ProgressTracker()


@app.before_request
def ensure_program_loaded():
    """Load the program once per request and expose a flag in g."""
    tracker.load_program()
    g.program_loaded = bool(tracker.program)


@app.route("/")
def index():
    """Dashboard"""
    if not g.program_loaded:
        return redirect(url_for("setup"))

    user_data = tracker.get_user_data()
    progress = tracker.compute_progress(user_data)

    return render_template(
        "dashboard.html",
        program=tracker.program,
        progress=progress,
        user_data=user_data,
        simulated_today=datetime.now().strftime("%Y-%m-%d"),
    )


@app.route("/daily")
def daily():
    """Daily tracking page"""
    if not g.program_loaded:
        return redirect(url_for("setup"))

    # Get selected date from query parameter, default to today
    selected_date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = datetime.now().date()

    # Default to always show arrows
    show_prev_arrow = True
    show_next_arrow = True

    if tracker.program.start_date and tracker.program.end_date:
        program_start_date = datetime.strptime(
            tracker.program.start_date, "%Y-%m-%d"
        ).date()
        program_end_date = datetime.strptime(
            tracker.program.end_date, "%Y-%m-%d"
        ).date()

        if selected_date < program_start_date:
            return redirect(url_for("daily", date=tracker.program.start_date))

        if selected_date > program_end_date:
            return redirect(url_for("daily", date=tracker.program.end_date))

        show_prev_arrow = selected_date > program_start_date
        show_next_arrow = selected_date < program_end_date

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
        show_prev_arrow=show_prev_arrow,
        show_next_arrow=show_next_arrow,
    )


@app.route("/todo")
def todo():
    """To Do page with tasks"""
    if not g.program_loaded:
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
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Calculate points for each objective
    objective_points = {}
    total_program_points = 0

    if tracker.program:
        # Use a dummy user_data to compute total points
        progress_data = tracker.compute_progress(user_data={})
        if progress_data:
            total_program_points = progress_data.get("total_points", 0)

        for obj in tracker.program.objectives:
            max_points = tracker.get_objective_max_points(obj)
            percentage = (
                (max_points / total_program_points * 100) if total_program_points else 0
            )
            objective_points[obj.id] = {
                "points": round(max_points),
                "percentage": round(percentage),
            }

    return render_template(
        "setup.html",
        program=tracker.program,
        today_str=today_str,
        objective_points=objective_points,
        total_program_points=total_program_points,
    )


@app.route("/progress-explanation")
def progress_explanation():
    """Progress calculation explanation page"""
    if not g.program_loaded:
        return redirect(url_for("setup"))

    user_data = tracker.get_user_data()

    # Calculate detailed breakdown
    breakdown = tracker.calculate_detailed_breakdown(user_data)
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
                "importance": obj_data.get("importance", "bien"),
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
    user_data = tracker.get_user_data()
    progress = tracker.compute_progress(user_data)
    return jsonify(progress)


@app.route("/api/dashboard")
def get_dashboard_data():
    """Get comprehensive dashboard data including weekly and daily breakdowns"""
    if not g.program_loaded:
        return jsonify({"error": "No program configured"}), 400

    # Check if program has valid dates
    if not tracker.program.start_date or not tracker.program.end_date:
        return jsonify(
            {
                "global_progress": 0,
                "expected_progress": 0,
                "weekly_progress": [],
                "daily_status": {},
                "program_start": "",
                "program_end": "",
                "error": "Program dates not configured",
            }
        )

    user_data = tracker.get_user_data()
    progress = tracker.compute_progress(user_data)

    # Calculate weekly progress (now returns empty list if dates invalid)
    weekly_progress = tracker.calculate_weekly_progress(user_data)

    # Calculate daily status (now returns empty dict if dates invalid)
    daily_status = tracker.calculate_daily_status(user_data)

    return jsonify(
        {
            "global_progress": progress["current_progress"] if progress else 0,
            "expected_progress": progress["expected_progress"] if progress else 0,
            "weekly_progress": weekly_progress if weekly_progress else [],
            "daily_status": daily_status if daily_status else {},
            "program_start": tracker.program.start_date or "",
            "program_end": tracker.program.end_date or "",
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


@app.route("/api/delete_program", methods=["POST"])
def delete_program():
    """Delete the currently selected program and its data."""
    data = request.get_json() or {}
    program_id = data.get("program_id")

    if not program_id:
        return jsonify({"success": False, "error": "Program ID is required"}), 400

    # Prevent deleting the default root folder blindly
    if program_id == "default":
        # Default program stores files directly in data_dir
        program_path = tracker.data_dir
        program_files = [
            os.path.join(program_path, f) for f in ("program.json", "user_data.csv")
        ]
        try:
            for fp in program_files:
                if os.path.exists(fp):
                    os.remove(fp)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        program_path = os.path.join(tracker.data_dir, program_id)
        if not os.path.isdir(program_path):
            return jsonify({"success": False, "error": "Program not found"}), 404
        try:
            shutil.rmtree(program_path)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # If we just deleted the current program, clear selection
    if tracker.current_program_id == program_id:
        tracker.current_program_id = None
        # Remove current_program.txt content
        current_file = os.path.join(tracker.data_dir, "current_program.txt")
        try:
            with open(current_file, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass
        tracker.program = None

    return jsonify({"success": True})


if __name__ == "__main__":
    import sys

    if "--demo" in sys.argv:
        from demo import create_demo_program

        program_id = create_demo_program()
        tracker.select_program(program_id)
        # This will set the "today" for the demo
        from freezegun import freeze_time
        from datetime import date

        demo_today = date(2025, 12, 12)
        freezer = freeze_time(demo_today)
        freezer.start()

    app.run(debug=True)
