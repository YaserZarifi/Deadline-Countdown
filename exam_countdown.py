import tkinter as tk
from tkinter import ttk
import jdatetime
import csv
from tkinter import font as tkFont
from tkcalendar import DateEntry
import datetime
from Jallai import JalaliDatepicker
from tkinter import messagebox
import os
import sys
import winreg as reg
import json # ADDED


# --- Global variable to hold references to rendered deadline items ---
rendered_deadline_items = {} # To store references to widget frames and their components


# --- Helper Functions ---

def is_valid_time(hour_str, minute_str):
    try:
        h = int(hour_str)
        m = int(minute_str)
        return 0 <= h <= 23 and 0 <= m <= 59
    except:
        return False

def is_valid_shamsi_date(date_str):
    try:
        parts = date_str.split('-')
        if len(parts) != 3:
            return False
        y, m, d = map(int, parts)
        jdatetime.date(y, m, d)
        return True
    except Exception:
        return False

def add_to_startup(file_path=None, app_name="DeadlineApp"):
    if file_path is None:
        file_path = sys.executable
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE) as registry_key:
            reg.SetValueEx(registry_key, app_name, 0, reg.REG_SZ, file_path)
    except Exception as e:
        print(f"Could not add to startup: {e}")


def get_persistent_path(filename="deadlines.json"): # Changed default to JSON
    """
    Returns the path to the JSON file in the project root.
    Creates an empty JSON file if it doesn't exist.
    """
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([], f)  # Write an empty list to the new file
    return filename


# --- Notebook Feature ---

class NotebookWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("یادداشت روزانه")
        self.geometry("400x500")
        self.vazir_font = tkFont.Font(family="Vazir", size=12)

        self.current_date = jdatetime.date.today()
        # Define the single JSON file path for notes
        self.notes_directory = "notes"
        self.notes_file = os.path.join(self.notes_directory, "notes.json")
        
        # Ensure the 'notes' directory exists
        os.makedirs(self.notes_directory, exist_ok=True)

        self.save_timer = None # For auto-save mechanism

        self.create_widgets()
        self.load_note_for_date(self.current_date)
        
        # Ensure changes are saved when the window is closed
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # Frame for date navigation
        nav_frame = tk.Frame(self)
        nav_frame.pack(pady=10)

        self.prev_button = tk.Button(nav_frame, text="< دیروز", font=self.vazir_font, command=self.prev_day)
        self.prev_button.pack(side="left", padx=10)

        self.date_label = tk.Label(nav_frame, text="", font=self.vazir_font)
        self.date_label.pack(side="left")

        self.next_button = tk.Button(nav_frame, text="فردا >", font=self.vazir_font, command=self.next_day)
        self.next_button.pack(side="right", padx=10)

        # Text area for notes
        self.notes_text = tk.Text(self, font=self.vazir_font, wrap="word", height=20, width=50)
        self.notes_text.pack(padx=10, pady=5, expand=True, fill="both")
        
        # Bind the key release event to schedule a save
        self.notes_text.bind("<KeyRelease>", self.schedule_save)

        # A small status label instead of a save button
        self.status_label = tk.Label(self, text="", font=("Vazir", 8), fg="grey")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    def schedule_save(self, event=None):
        """Schedules a save to happen after a short period of inactivity."""
        # Cancel any previously scheduled save
        if self.save_timer:
            self.after_cancel(self.save_timer)

        # Schedule a new save after 1.5 seconds (1500 ms)
        self.save_timer = self.after(1500, self.save_note)

    def load_note_for_date(self, date_obj):
        """Loads the note for the given date from the JSON file and sets the widget state."""
        self.current_date = date_obj
        self.date_label.config(text=date_obj.strftime("%Y-%m-%d"))
        
        notes_content = {}
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    notes_content = json.load(f)
            except json.JSONDecodeError:
                notes_content = {} # Handle empty or corrupt JSON file

        date_str = date_obj.strftime("%Y-%m-%d")
        note_text = notes_content.get(date_str, "")

        # Re-enable the text widget to clear and load new content
        self.notes_text.config(state="normal")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", note_text)

        # Set read-only status for past days
        if date_obj < jdatetime.date.today():
            self.notes_text.config(state="disabled")
            self.status_label.config(text="Read-only")
        else:
            self.notes_text.config(state="normal")
            self.status_label.config(text="All changes are saved automatically.")

    def save_note(self):
        """Silently saves the current content of the text widget to the JSON file."""
        # Do not save if the widget is disabled (i.e., for past dates)
        if self.notes_text.cget("state") == "disabled":
            return
            
        note_content = self.notes_text.get("1.0", tk.END).strip()
        date_str = self.current_date.strftime("%Y-%m-%d")
        
        # Load existing notes
        all_notes = {}
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    all_notes = json.load(f)
            except json.JSONDecodeError:
                pass # File is empty or corrupt, start with empty dict

        # Update the specific date's note
        all_notes[date_str] = note_content

        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(all_notes, f, ensure_ascii=False, indent=4)
            # Update status label to show it's saved
            self.status_label.config(text=f"Saved at {datetime.datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.status_label.config(text=f"Error saving: {e}")

    def save_note_if_pending(self):
        """Saves immediately if a save operation was pending."""
        if self.save_timer:
            self.after_cancel(self.save_timer)
            self.save_timer = None
            self.save_note()

    def prev_day(self):
        self.save_note_if_pending()
        self.load_note_for_date(self.current_date - jdatetime.timedelta(days=1))

    def next_day(self):
        self.save_note_if_pending()
        self.load_note_for_date(self.current_date + jdatetime.timedelta(days=1))
        
    def on_close(self):
        """Called when the notebook window is closed."""
        self.save_note_if_pending()
        self.destroy()

def open_notebook():
    NotebookWindow(root)


# --- Deadline Management ---

def adjust_root_height():
    json_path = get_persistent_path()
    deadlines = load_deadlines(json_path)
    num_rows = len(deadlines)
    base_height = 150
    row_height = 60
    max_height = min(root.winfo_screenheight() - 100, 800)
    new_height = base_height + row_height * num_rows
    new_height = min(new_height, max_height)
    canvas.config(height=new_height - 100)
    root.geometry(f"{window_width}x{new_height}+{x}+{y}")


def manage_deadlines_popup():
    popup = tk.Toplevel(root)
    popup.title("مدیریت ددلاین‌ها")
    popup.geometry("500x400")

    container = tk.Frame(popup)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    entry_rows = []

    def add_row(course="", date="", time_="00:00"):
        row_frame = tk.Frame(scroll_frame)
        row_frame.pack(fill="x", pady=2)

        course_entry = tk.Entry(row_frame, width=20, font=vazir_font)
        course_entry.insert(0, course)
        course_entry.pack(side="right", padx=3)

        date_entry = tk.Entry(row_frame, width=12, font=vazir_font)
        date_entry.insert(0, date)
        date_entry.pack(side="right", padx=3)

        def open_datepicker():
            JalaliDatepicker(root, date_entry)

        date_btn = tk.Button(row_frame, text="📅", font=vazir_font, command=open_datepicker)
        date_btn.pack(side="right", padx=3)

        try:
            h, m = map(int, time_.split(":")[:2])
        except:
            h, m = 0, 0

        hour_var = tk.StringVar(value=f"{h:02}")
        minute_var = tk.StringVar(value=f"{m:02}")

        time_frame = tk.Frame(row_frame)
        hour_spin = tk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=hour_var, format="%02.0f", font=vazir_font, wrap=True)
        minute_spin = tk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=minute_var, format="%02.0f", font=vazir_font, wrap=True)

        hour_spin.pack(side="left")
        tk.Label(time_frame, text=":", font=vazir_font).pack(side="left")
        minute_spin.pack(side="left")
        time_frame.pack(side="right", padx=3)

        delete_btn = tk.Button(row_frame, text="❌", font=vazir_font, command=lambda: remove_row(row_frame))
        delete_btn.pack(side="right", padx=3)

        entry_rows.append((row_frame, course_entry, date_entry, hour_var, minute_var))

    def remove_row(row_frame):
        for i, (rf, _, _, _, _) in enumerate(entry_rows):
            if rf == row_frame:
                entry_rows.pop(i)
                break
        row_frame.destroy()

    def save_all():
        # Read existing data to preserve 'checked' status
        json_path = get_persistent_path()
        existing_data = []
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        checked_status_map = {item.get('course'): item.get('checked', '0') for item in existing_data}

        # Process rows from the popup
        invalid_rows = []
        valid_rows = []
        for i, (_, course_e, date_e, hour_v, minute_v) in enumerate(entry_rows, start=1):
            course = course_e.get().strip()
            shamsi_date_str = date_e.get()
            hour_str = hour_v.get()
            minute_str = minute_v.get()

            if not is_valid_shamsi_date(shamsi_date_str) or not is_valid_time(hour_str, minute_str):
                invalid_rows.append(i)
                continue

            time_str = f"{int(hour_str):02}:{int(minute_str):02}:00"
            if course and shamsi_date_str:
                valid_rows.append({
                    "course": course,
                    "deadline_shamsi": shamsi_date_str,
                    "deadline_time": time_str,
                    "checked": checked_status_map.get(course, '0') # Preserve checked status
                })

        if invalid_rows:
            messagebox.showwarning("خطای ورودی", f"لطفاً تاریخ و زمان‌های معتبر وارد کنید. خطا در سطر(های): {', '.join(map(str, invalid_rows))}")
            return

        with open(json_path, "w", encoding='utf-8') as jsonfile:
            json.dump(valid_rows, jsonfile, ensure_ascii=False, indent=4)

        popup.destroy()
        refresh_deadlines_display() # Call the full refresh after saving


    # Load initial data from JSON to populate the popup
    try:
        with open(get_persistent_path(), 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            for row in data:
                add_row(row.get('course', ''), row.get('deadline_shamsi', ''), row.get('deadline_time', '00:00'))
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Buttons
    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="➕ ددلاین جدید", font=vazir_font, command=add_row).pack(side="right", padx=5)
    tk.Button(btn_frame, text="💾 ذخیره همه", font=vazir_font, command=save_all).pack(side="right", padx=5)


def load_deadlines(file_path):
    deadlines = []
    now = jdatetime.datetime.now()

    if not os.path.exists(file_path): return []

    with open(file_path, 'r', encoding='utf-8') as jsonfile:
        try:
            data = json.load(jsonfile)
        except json.JSONDecodeError:
            data = []
    for row in data:
        try:
            course = row['course']
            shamsi_date = row['deadline_shamsi']
            time_str = row.get('deadline_time', '00:00:00')
            is_checked = bool(int(row.get('checked', '0')))

            deadline_dt = jdatetime.datetime.strptime(shamsi_date + " " + time_str, "%Y-%m-%d %H:%M:%S")
            delta = deadline_dt - now
            total_seconds = int(delta.total_seconds())

            total_range = (deadline_dt - jdatetime.datetime(now.year, now.month, now.day)).total_seconds()
            passed = total_range - total_seconds
            progress = max(0, min(100, int((passed / total_range) * 100))) if total_range > 0 else 100

            if total_seconds < 0:
                countdown_text = "پایان یافته"
                deadlines.append((course, shamsi_date, countdown_text, 0, True, progress, is_checked))
            else:
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                countdown_text = f"{days}:{hours:02d}:{minutes:02d}:{seconds:02d}"
                deadlines.append((course, shamsi_date, countdown_text, days, False, progress, is_checked))
        except Exception as e:
            print(f"Error parsing row: {row} - {e}")
    return deadlines

def toggle_deadline_checked(course_name, checked_var):
    json_path = get_persistent_path()
    data = []
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    for item in data:
        if item.get('course') == course_name:
            item['checked'] = '1' if checked_var.get() else '0'
            break

    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    refresh_deadlines_display() # Call the full refresh for immediate visual update


def get_color_tag(days, is_checked):
    if is_checked:
        return "lightgrey"
    if days > 14: return "green"
    elif days > 12: return "lightgreen"
    elif days > 10: return "yellowgreen"
    elif days > 8: return "yellow"
    elif days > 6: return "gold"
    elif days > 4: return "orange"
    elif days > 2: return "orangered"
    else: return "red"


def refresh_deadlines_display():
    """
    Renders all deadlines from scratch. Call this when deadlines are added, removed, or changed.
    This replaces the 'destroy all and redraw' part of the old update_table.
    """
    global rendered_deadline_items
    
    # Clear existing widgets from the main frame
    for widget in frame.winfo_children():
        widget.destroy()
    rendered_deadline_items = {} # Reset the dictionary

    json_path = get_persistent_path()
    deadlines = load_deadlines(json_path)
    deadlines.sort(key=lambda x: (x[6], x[3])) # Sort by checked then by days remaining

    for course, shamsi, countdown_text, days, expired, progress, is_checked in deadlines:
        # Create a new frame for each deadline item
        item_frame = tk.Frame(frame)
        item_frame.pack(fill='x', padx=10, pady=2)

        checked_var = tk.BooleanVar(value=is_checked)
        tag_color = get_color_tag(days, is_checked)
        item_frame.config(bg=tag_color)

        # Checkbox
        chk = tk.Checkbutton(item_frame, variable=checked_var, bg=tag_color,
                             command=lambda c=course, v=checked_var: toggle_deadline_checked(c, v))
        if expired:
            chk.config(state="disabled")
        chk.pack(side="left", padx=(0, 5))

        # Label for deadline text
        label_text = f"{countdown_text} | {shamsi} | {course}"
        label = tk.Label(item_frame, text=label_text, font=vazir_font, bg=tag_color, anchor='w')
        if expired or is_checked:
            label.config(fg="gray", font=strikethrough_font)
        label.pack(side="left", fill='x', expand=True)

        # Progress Bar (under the item_frame, but in its own small frame for packing)
        pb_frame = tk.Frame(frame)
        pb_frame.pack(fill='x', padx=10, pady=(0, 5))
        pb = ttk.Progressbar(pb_frame, orient="horizontal", length=350, mode="determinate", value=progress)
        pb.pack(fill='x')

        # Store references for later update
        rendered_deadline_items[course] = {
            'item_frame': item_frame,
            'label': label,
            'progressbar': pb,
            'checkbox_var': checked_var,
            'checkbox': chk,
            'pb_frame': pb_frame,
            'current_days': days,
            'is_expired': expired,
            'is_checked': is_checked
        }

    adjust_root_height()
    # DO NOT call root.after(1000, ...) here. This function is for full redraws.


def update_countdown_display():
    """
    Updates the countdown, progress bar, and color for existing deadlines without re-drawing all widgets.
    This function is called every second.
    """
    now = jdatetime.datetime.now()
    
    # It's better to reload the data to ensure we reflect any changes that might have occurred
    # (e.g., direct file edits, or if a deadline just expired).
    json_path = get_persistent_path()
    current_deadlines_data = load_deadlines(json_path) # Reload all data
    current_deadlines_map = {d[0]: d for d in current_deadlines_data} # Map for quick lookup

    # Iterate through the currently rendered items
    # Check for items that might have been removed from the file (will be handled by full refresh)
    # Update existing items
    for course, item_widgets in list(rendered_deadline_items.items()): # Use list() to allow deletion during iteration
        if course in current_deadlines_map:
            # Unpack the specific deadline data from the current file load
            _, shamsi, countdown_text, days, expired, progress, is_checked = current_deadlines_map[course]

            # Update label text
            item_widgets['label'].config(text=f"{countdown_text} | {shamsi} | {course}")

            # Update progress bar
            item_widgets['progressbar']["value"] = progress

            # Update color and font if status has changed (e.g., expired, or days crossed a threshold)
            # This avoids re-configuring if not needed, improving performance.
            if (item_widgets['current_days'] != days or 
                item_widgets['is_checked'] != is_checked or 
                item_widgets['is_expired'] != expired):

                tag_color = get_color_tag(days, is_checked)
                item_widgets['item_frame'].config(bg=tag_color)
                
                if expired or is_checked:
                    item_widgets['label'].config(fg="gray", font=strikethrough_font)
                    if expired: item_widgets['checkbox'].config(state="disabled")
                else:
                    item_widgets['label'].config(fg="black", font=vazir_font)
                    item_widgets['checkbox'].config(state="normal")
                
                # Update stored state
                item_widgets['current_days'] = days
                item_widgets['is_checked'] = is_checked
                item_widgets['is_expired'] = expired
            
            # Ensure checkbox variable is synced in case of external change (e.g., direct file edit)
            item_widgets['checkbox_var'].set(is_checked)

        else:
            # This deadline no longer exists in the data, remove it from display
            item_widgets['item_frame'].destroy()
            item_widgets['pb_frame'].destroy()
            del rendered_deadline_items[course]
            adjust_root_height() # Adjust height if an item is removed

    # If the order of deadlines changed significantly, we might need a full refresh
    # This is a trade-off. For now, simple periodic updates are done without full redraw.
    # If a deadline is added/removed, refresh_deadlines_display() will be called.

    root.after(1000, update_countdown_display) # Schedule the next update


# --- Root setup ---
root = tk.Tk()
root.title("شمارش معکوس ددلاین")
root.attributes('-topmost', True)
root.resizable(True, True)

vazir_font = tkFont.Font(family="Vazir", size=10)
vazir_bold_font = tkFont.Font(family="Vazir", size=10, weight="bold")
strikethrough_font = tkFont.Font(family="Vazir", size=10, overstrike=True, slant="italic")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 370
window_height = 550
x = screen_width - window_width - 10
y = 10
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# --- Scrollable Frame ---
container = tk.Frame(root)
container.pack(fill="both", expand=True, side="top")

canvas = tk.Canvas(container)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
canvas.bind_all("<MouseWheel>", _on_mousewheel)


# --- Buttons Frame ---
buttons_frame = tk.Frame(root)
buttons_frame.pack(side="bottom", pady=5, fill="x")

# Edit Deadlines Button
edit_button = tk.Button(buttons_frame, text="اضافه/ویرایش ددلاین", command=manage_deadlines_popup, font=vazir_font)
edit_button.pack(side="right", padx=10)

# Notebook Button
notebook_button = tk.Button(buttons_frame, text="یادداشت‌ها", command=open_notebook, font=vazir_font)
notebook_button.pack(side="left", padx=10)


if __name__ == "__main__":
    refresh_deadlines_display() # Initial draw of all deadlines
    update_countdown_display() # Start the continuous countdown updates
    add_to_startup()
    root.mainloop()