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


def is_valid_time(hour_str, minute_str):
    try:
        h = int(hour_str)
        m = int(minute_str)
        return 0 <= h <= 23 and 0 <= m <= 59
    except:
        return False


def is_valid_shamsi_date(date_str):
    try:
        # Expecting format "YYYY/MM/DD"
        parts = date_str.split('-')
        if len(parts) != 3:
            return False
        y, m, d = map(int, parts)
        jdatetime.date(y, m, d)  # Will raise ValueError if invalid
        return True
    except Exception:
        return False


def add_to_startup(file_path=None, app_name="DeadlineApp"):
    if file_path is None:
        file_path = sys.executable  # path to the .exe file

    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE) as registry_key:
        reg.SetValueEx(registry_key, app_name, 0, reg.REG_SZ, file_path)


def get_resource_path(relative_path):
    try:
        # When bundled by PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def adjust_root_height():
    deadlines = load_deadlines(get_resource_path("deadlines.csv"))
    num_rows = len(deadlines)

    # Base height for window (buttons, padding, etc.)
    base_height = 110  
    # Height per row (approximate)
    row_height = 50  

    # Maximum window height
    max_height = min(root.winfo_screenheight() - 100, 800)  # Ensure it fits on screen

    new_height = base_height + row_height * num_rows
    new_height = min(new_height, max_height)

    # Update canvas and window dimensions
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

        # ورودی تاریخ
        date_entry = tk.Entry(row_frame, width=12, font=vazir_font)
        date_entry.insert(0, date)
        date_entry.pack(side="right", padx=3)

        # دکمه باز کردن تقویم شمسی
        def open_datepicker():
            JalaliDatepicker(root, date_entry)

        date_btn = tk.Button(row_frame, text="📅", font=vazir_font, command=open_datepicker)
        date_btn.pack(side="right", padx=3)

        # ورودی زمان
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
        invalid_rows = []
        valid_rows = []

        for i, (_, course_e, date_e, hour_v, minute_v) in enumerate(entry_rows, start=1):
            course = course_e.get().strip()
            shamsi_date_str = date_e.get()  # get Shamsi date string directly

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
                    "deadline_time": time_str
                })

        if invalid_rows:
            messagebox.showwarning(
                "خطای ورودی",
                f"لطفاً تاریخ و زمان‌های معتبر وارد کنید. خطا در سطر(های): {', '.join(map(str, invalid_rows))}"
            )
            return  # Keep popup open for correction

        with open(get_resource_path("deadlines.csv"), "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["course", "deadline_shamsi", "deadline_time"])
            writer.writeheader()
            for row in valid_rows:
                writer.writerow(row)

        popup.destroy()
        update_table()







    # ✅ حالا بخونیم از فایل و add_row بزنیم
    try:
        with open(get_resource_path("deadlines.csv"), newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                course = row.get('course', '')
                date = row.get('deadline_shamsi', '')
                time_ = row.get('deadline_time', '00:00')
                add_row(course, date, time_)
    except FileNotFoundError:
        pass

    # ✅ دکمه‌ها
    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="➕ ددلاین جدید", font=vazir_font, command=add_row).pack(side="right", padx=5)
    tk.Button(btn_frame, text="💾 ذخیره همه", font=vazir_font, command=save_all).pack(side="right", padx=5)


# def add_deadline_popup():
#     popup = tk.Toplevel(root)
#     popup.title("افزودن / ویرایش ددلاین")
#     popup.geometry("300x200")

#     tk.Label(popup, text="نام درس:", font=vazir_font).pack()
#     course_entry = tk.Entry(popup, font=vazir_font)
#     course_entry.pack()

#     tk.Label(popup, text="تاریخ (مثلاً 1403-04-20):", font=vazir_font).pack()
#     date_entry = tk.Entry(popup, font=vazir_font)
#     date_entry.pack()

#     tk.Label(popup, text="ساعت (مثلاً 14:00:00):", font=vazir_font).pack()
#     time_entry = tk.Entry(popup, font=vazir_font)
#     time_entry.pack()

#     def save_deadline():
#         course = course_entry.get()
#         date = date_entry.get()
#         time_ = time_entry.get() or "00:00:00"

#         if not course or not date:
#             return  # you can show a warning here

#         # Append to CSV
#         with open("deadlines.csv", "a", newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=["course", "deadline_shamsi", "deadline_time"])
#             if csvfile.tell() == 0:
#                 writer.writeheader()
#             writer.writerow({
#                 "course": course,
#                 "deadline_shamsi": date,
#                 "deadline_time": time_
#             })

#         popup.destroy()
#         update_table()

#     save_button = tk.Button(popup, text="ذخیره", command=save_deadline, font=vazir_font)
#     save_button.pack(pady=10)

def load_deadlines(file_path):
    deadlines = []
    now = jdatetime.datetime.now()

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            course = row['course']
            shamsi_date = row['deadline_shamsi']
            time_str = row.get('deadline_time', '00:00:00')
            try:
                deadline_dt = jdatetime.datetime.strptime(shamsi_date + " " + time_str, "%Y-%m-%d %H:%M:%S")
                delta = deadline_dt - now
                total_seconds = int(delta.total_seconds())

                total_range = (deadline_dt - jdatetime.datetime(now.year, now.month, now.day)).total_seconds()
                passed = total_range - total_seconds
                progress = max(0, min(100, int((passed / total_range) * 100))) if total_range > 0 else 100

                if total_seconds < 0:
                    days = hours = minutes = seconds = 0
                    countdown_text = "پایان یافته"
                    deadlines.append((course, shamsi_date, countdown_text, days, True, progress))
                else:
                    days = total_seconds // 86400
                    hours = (total_seconds % 86400) // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    countdown_text = f"{days}:{hours:02d}:{minutes:02d}:{seconds:02d}"
                    deadlines.append((course, shamsi_date, countdown_text, days, False, progress))

            except Exception as e:
                print(f"Error parsing date/time: {shamsi_date} {time_str} - {e}")
    return deadlines


def get_color_tag(days):
    if days > 14:
        return "green"
    elif days > 12:
        return "lightgreen"
    elif days > 10:
        return "yellowgreen"
    elif days > 8:
        return "yellow"
    elif days > 6:
        return "gold"
    elif days > 4:
        return "orange"
    elif days > 2:
        return "orangered"
    else:
        return "red"


def update_table():
    for widget in frame.winfo_children():
        widget.destroy()

    csv_path = get_resource_path("deadlines.csv")
    deadlines = load_deadlines(csv_path)
    deadlines.sort(key=lambda x: x[3])

    for course, shamsi, countdown_text, days, expired, progress in deadlines:
        tag_color = get_color_tag(days)

        label = tk.Label(frame, text=f"{countdown_text} | {shamsi} | {course}", font=vazir_font, bg=tag_color, anchor='w')
        if expired:
            label.config(fg="gray", font=strikethrough_font)
        label.pack(fill='x', padx=10, pady=(3, 0))

        pb = ttk.Progressbar(frame, orient="horizontal", length=350, mode="determinate")
        pb["value"] = progress
        pb.pack(fill='x', padx=10, pady=(0, 5))
    adjust_root_height()
    root.after(1000, update_table)



# --- Root setup ---
root = tk.Tk()
root.title("شمارش معکوس امتحانات")
root.attributes('-topmost', True)
root.resizable(True, True)

vazir_font = tkFont.Font(family="Vazir", size=10)
vazir_bold_font = tkFont.Font(family="Vazir", size=10, weight="bold")
strikethrough_font = tkFont.Font(family="Vazir", size=10)
strikethrough_font.configure(overstrike=True, slant="italic")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 370
window_height = 550
x = screen_width - window_width - 10
y = 10
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# --- Scrollable Frame ---
container = tk.Frame(root)
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor="nw")

canvas.configure(yscrollcommand=scrollbar.set)
frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# --- Enable mouse scrolling ---
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# --- Add button ---
edit_button = tk.Button(root, text="اضافه/ویرایش ددلاین", command=manage_deadlines_popup, font=vazir_font)
edit_button.pack(side="bottom", pady=5)


if __name__ == "__main__":
    update_table()
    add_to_startup()
    root.mainloop()
