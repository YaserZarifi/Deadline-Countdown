# Deadline Countdown & Daily Notebook App

A simple, user-friendly desktop application built with Python and Tkinter to help you keep track of your deadlines and manage daily notes. This application is designed with support for the Shamsi (Jalali) calendar.

## ✨ Features

* **Deadline Tracking:** Displays a countdown for multiple deadlines.
* **Color-Coded Urgency:** Deadlines are color-coded based on their proximity, allowing for quick visual prioritization.
* **Completion Checkboxes:** Mark deadlines as completed directly from the main window.
* **Persistent Data:** All deadline data is saved to a local `deadlines.json` file.
* **Daily Note-Taking (Mini-Notebook):**
    * A dedicated section for daily notes.
    * Navigate between different days to view or add notes.
    * **Automatic Saving:** Notes are saved automatically as you type (after a brief pause in activity).
    * **Read-Only Past Notes:** Notes for past days are automatically set to read-only.
    * **Centralized Storage:** All notes are stored efficiently in a single `notes/notes.json` file, keyed by date.
* **Smooth UI Updates:** The countdowns update seamlessly every second without causing any visual "blinking."
* **Deadline Management:** Easily add, edit, or remove deadlines through a dedicated popup window.
* **Shamsi (Jalali) Calendar Support:** Integrated for dates and deadlines.
* **Windows Startup:** Optionally configured to start automatically when Windows launches.

## 🚀 Installation

To get this application up and running on your local machine, follow these steps:

### Prerequisites

* **Python 3.x:** Ensure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/). During installation, make sure to check "Add Python to PATH."

### Setup Steps

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/YaserZarifi/Deadline-Countdown.git]
    cd Deadline-Countdown
    ```

2.  **Install Dependencies:**
    This project requires a few Python libraries. You can install them using `pip`:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `tkcalendar` and `jdatetime`. `tkinter` is usually included with standard Python installations.

## 💡 Usage

### Running the Application

Simply execute the main script:
```bash
python exam_countdown.py
