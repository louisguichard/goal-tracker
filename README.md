# Goal Tracker

**⚠️ This application was quickly "vibe-coded" and may not adhere to strict production standards or best practices.**

A web application to track program progress with objectives and tasks.

## Features

### Objectives
-   **Binary**: Yes/No completion.
-   **Numeric**: Track progress towards a specific target.
-   **Frequencies**:
    -   Daily (1 point per day)
    -   Weekly (5 points per week)
    -   Program (15 total points for the entire program)

### Tasks
-   Binary items to be completed once during the program.
-   5 points per task.

### Progress Calculation
-   **Current Progress**: Points earned / Total possible points.
-   **Expected Progress**: Proportion of elapsed days / Total program days.
-   **Status**: On track or Behind schedule.

## Installation

### Prerequisites
-   Python 3.7+
-   pip (Python package manager)

### Steps
1.  **Clone or download the project**:
    ```bash
    git clone <url-du-repo>
    cd goal-tracker
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Launch the application**:
    ```bash
    python app.py
    ```
4.  **Open in browser**: Access `http://localhost:5000`. The application will automatically open the setup page if no program is defined.

## Usage

### First Use
1.  **Initial Configuration**: Create your first program with objectives and tasks.
2.  **Define Objectives**: Choose type, frequency, and parameters.
3.  **Add Tasks**: Define one-time tasks for your program.

### Daily Tracking
1.  **Daily Page**: Record daily progress for your objectives.
2.  **Dashboard**: Visualize overall and individual progress.
3.  **To Do Page**: View and mark your tasks as complete.

### Point System
-   **Daily objectives**: 1 point per day completed.
-   **Weekly objectives**: 5 points per week when the target is reached.
-   **Program objectives**: 15 points when the target is reached.
-   **Tasks**: 5 points each when completed.

### Importance Multipliers
-   **🔴 Indispensable**: ×3 points
-   **🟠 Important**: ×2 points
-   **🟢 Good**: ×1 point (base)