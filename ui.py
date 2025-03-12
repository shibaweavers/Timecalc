import sqlite3
import tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk, messagebox
from tkinter.ttk import Style

from tkcalendar import Calendar

from core import PosixTime, seconds_to_text
from themes import ThemeManager


class TimestampApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("POSIX Timestamp Converter")
        self.geometry("1100x650")
        self.resizable(False, False)
        self.preset_options = ["DAY", "WEEK", "12 DAYS", "13 DAYS", "2 WEEKS", "15 DAYS", "28 DAYS", "29 DAYS", "30 DAYS", "31 DAYS", "365 DAYS"]
        self.preset_mapping = {
            "DAY": 86400,
            "WEEK": 604800,
            "12 DAYS": 1036800,
            "13 DAYS": 1123200,
            "2 WEEKS": 1209600,
            "15 DAYS": 1296000,
            "28 DAYS": 2419200, "29 DAYS": 2505600,
                               "30 DAYS": 2592000, "31 DAYS": 2678400, "365 DAYS": 31536000}
        self.db_conn = sqlite3.connect("timestamps.db")
        self.create_table()
        self.load_timestamps()
        self.create_widgets()
        saved_theme = self.load_theme()
        self.apply_theme(saved_theme)
        self.theme_combo.set(saved_theme)
        self.update_timer()
        self.use_current_timestamp()  # Add this line to call paste_current_timestamp on startup

    def create_table(self):
        cursor = self.db_conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS timestamps (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER UNIQUE, starred BOOLEAN DEFAULT 0)""")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")
        self.db_conn.commit()

    def save_theme(self, theme_name):
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                       ("theme", theme_name))
        self.db_conn.commit()

    def load_theme(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'theme'")
        result = cursor.fetchone()
        return result[0] if result else 'SHIBA INU'

    def load_timestamps(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT timestamp FROM timestamps WHERE starred = 1 ORDER BY id DESC")
        starred_rows = cursor.fetchall()
        cursor.execute("SELECT timestamp FROM timestamps WHERE starred = 0 ORDER BY id DESC LIMIT ?",
                       (max(0, 100 - len(starred_rows)),))
        regular_rows = cursor.fetchall()
        self.saved_timestamps = []
        self.starred_timestamps = set()
        for (ts,) in starred_rows:
            self.saved_timestamps.append(str(ts))
            self.starred_timestamps.add(str(ts))
        for (ts,) in regular_rows:
            self.saved_timestamps.append(str(ts))

    def save_timestamp(self, timestamp):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("INSERT INTO timestamps (timestamp) VALUES (?)", (timestamp,))
            self.db_conn.commit()
            self.load_timestamps()
            self.update_timestamp_list()
        except sqlite3.IntegrityError:
            pass

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
        theme_frame = ttk.Frame(main_frame)
        theme_frame.pack(fill=tk.X, pady=(0, 5))
        theme_container = ttk.Frame(theme_frame)
        theme_container.pack(side=tk.RIGHT)
        ttk.Label(theme_container, text="Theme:").pack(side=tk.LEFT, padx=(0, 5))
        self.theme_combo = ttk.Combobox(theme_container, values=list(ThemeManager.THEMES.keys()), state="readonly",
                                        width=15)
        self.theme_combo.pack(side=tk.LEFT)
        self.theme_combo.set('SHIBA INU')
        self.theme_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_theme(self.theme_combo.get()))
        upper_frame = ttk.Frame(main_frame)
        upper_frame.pack(fill=tk.BOTH, expand=True)
        lower_frame = ttk.Frame(main_frame)
        lower_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        target_group = ttk.LabelFrame(upper_frame, text="TARGET", relief="groove", borderwidth=2)
        target_group.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        target_frame = ttk.Frame(target_group)
        target_frame.pack(padx=5, pady=5, fill=tk.X)
        self.decrement_button = ttk.Button(target_frame, text="←", width=3, command=self.decrement_target)
        self.decrement_button.pack(side=tk.LEFT, padx=(0, 2))
        self.increment_button = ttk.Button(target_frame, text="→", width=3, command=self.increment_target)
        self.increment_button.pack(side=tk.LEFT, padx=(0, 2))
        vcmd = (self.register(self.validate_number), '%P')
        self.target_entry = ttk.Entry(target_frame, validate="key", validatecommand=vcmd, width=20)
        self.target_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        current_ts = PosixTime.now()
        self.target_entry.insert(0, str(current_ts))
        self.add_button = ttk.Button(target_frame, text="+", width=3, command=self.add_current_target)
        self.add_button.pack(side=tk.LEFT, padx=(2, 0))
        self.target_date_label = ttk.Label(target_group, text="Date: ")
        self.target_date_label.pack(fill=tk.X, padx=5)
        self.use_current_button = ttk.Button(target_group, text="Use Current", command=self.use_current_timestamp)
        self.use_current_button.pack(pady=5, padx=5, fill=tk.X)
        calendar_frame = ttk.Frame(target_group)
        calendar_frame.pack(pady=5, expand=True)
        self.calendar = Calendar(calendar_frame, selectmode='day', date_pattern='yyyy-mm-dd', showweeknumbers=False,
                                 width=20, height=5, firstweekday='monday', disabledforeground='black', showothermonthdays=False,
                                 disableddaybackground='white', selectbackground='lightblue', selectforeground='black',
                                 state='disabled')
        self.calendar.pack(pady=5)
        self.calendar.config(state='disabled')
        self.month_progress_group = ttk.LabelFrame(target_group, text="POSITION IN DAY", relief="groove", borderwidth=2)
        self.month_progress_group.pack(fill=tk.X, padx=5, pady=(0, 5))
        progress_container = ttk.Frame(self.month_progress_group)
        progress_container.pack(fill=tk.X, padx=5, pady=5)
        left_frame = ttk.Frame(progress_container)
        left_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        middle_frame = ttk.Frame(progress_container)
        middle_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        right_frame = ttk.Frame(progress_container)
        right_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.start_day_label = ttk.Label(left_frame, text="", anchor='center')
        self.start_day_label.pack(expand=True)
        self.day_progress_canvas = tk.Canvas(middle_frame, height=20, bg='white')
        self.day_progress_canvas.pack(fill=tk.X, expand=True, padx=5)
        self.end_day_label = ttk.Label(right_frame, text="", anchor='center')
        self.end_day_label.pack(expand=True)
        bookmarks_group = ttk.LabelFrame(upper_frame, text="BOOKMARKS", relief="groove", borderwidth=2)
        bookmarks_group.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.timestamp_listbox = tk.Listbox(bookmarks_group, width=20)
        self.timestamp_listbox.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        buttons_frame = ttk.Frame(bookmarks_group)
        buttons_frame.pack(pady=5, padx=5)
        self.star_button = ttk.Button(buttons_frame, text="Star", width=4, command=self.star_timestamp)
        self.star_button.pack(side=tk.LEFT, padx=2)
        self.edit_button = ttk.Button(buttons_frame, text="Edit", width=5, command=self.edit_timestamp)
        self.edit_button.pack(side=tk.LEFT, padx=2)
        self.delete_button = ttk.Button(buttons_frame, text="Del", width=3, command=self.delete_timestamp)
        self.delete_button.pack(side=tk.LEFT, padx=2)
        self.delete_button.state(['disabled'])
        self.update_timestamp_list()
        self.timestamp_listbox.bind("<<ListboxSelect>>", self.select_timestamp)
        head_output_frame = ttk.LabelFrame(lower_frame, text="HEAD", relief="groove", borderwidth=2)
        head_output_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(head_output_frame, text="DELTA HEAD").pack(anchor=tk.W, padx=5)
        self.head_entry = ttk.Entry(head_output_frame, validate="key", validatecommand=vcmd, width=20)
        self.head_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.head_duration_label = ttk.Label(head_output_frame, text="Duration: ")
        self.head_duration_label.pack(anchor=tk.W, padx=5)
        self.head_date_label = ttk.Label(head_output_frame, text="Date (-HEAD): ")
        self.head_date_label.pack(anchor=tk.W, padx=5)
        self.head_combo = ttk.Combobox(head_output_frame, values=self.preset_options, width=15, state="readonly")
        self.head_combo.pack(anchor=tk.W, padx=5, pady=(5, 5))
        tail_output_frame = ttk.LabelFrame(lower_frame, text="TAIL", relief="groove", borderwidth=2)
        tail_output_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(tail_output_frame, text="DELTA TAIL").pack(anchor=tk.W, padx=5)
        self.tail_entry = ttk.Entry(tail_output_frame, validate="key", validatecommand=vcmd, width=20)
        self.tail_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.tail_duration_label = ttk.Label(tail_output_frame, text="Duration: ")
        self.tail_duration_label.pack(anchor=tk.W, padx=5)
        self.tail_date_label = ttk.Label(tail_output_frame, text="Date (+TAIL): ")
        self.tail_date_label.pack(anchor=tk.W, padx=5)
        self.tail_combo = ttk.Combobox(tail_output_frame, values=self.preset_options, width=15, state="readonly")
        self.tail_combo.pack(anchor=tk.W, padx=5, pady=(5, 5))
        self.head_entry.bind("<KeyRelease>", lambda e: self.update_labels())
        self.target_entry.bind("<KeyRelease>", lambda e: self.update_labels())
        self.tail_entry.bind("<KeyRelease>", lambda e: self.update_labels())
        self.head_combo.bind("<<ComboboxSelected>>",
                             lambda e: (self.set_head_from_preset(), self.update_head_tail_labels()))
        self.tail_combo.bind("<<ComboboxSelected>>",
                             lambda e: (self.set_tail_from_preset(), self.update_head_tail_labels()))
        self.update_labels()

    def update_day_progress(self, timestamp):
        if not hasattr(self, 'theme_colors'):  # Prevents access issues
            print("Theme colors not set. Please apply a theme first.")
            return

        # Get UTC date
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        # Calculate start and end of UTC day
        start_of_day = datetime(date.year, date.month, date.day,
                                tzinfo=timezone.utc).timestamp()
        end_of_day = start_of_day + 86399  # Last second of the day

        try:
            target = int(self.target_entry.get()) if self.target_entry.get() else timestamp
        except ValueError:
            target = timestamp

        start_str = f"{format(int(start_of_day), ',')}\n{seconds_to_text(target - int(start_of_day), output_format=-2)}"
        end_str = f"{format(int(end_of_day), ',')}\n{seconds_to_text(target - int(end_of_day), output_format=-2)}"

        self.start_day_label.config(text=start_str)
        self.end_day_label.config(text=end_str)

        canvas_width = self.day_progress_canvas.winfo_width()
        if canvas_width > 0:
            # Calculate the day's progress
            day_progress = (target - start_of_day) / 86400
            marker_x = int(canvas_width * day_progress)
            self.day_progress_canvas.delete('all')

            # Background (progress bar trough)
            self.day_progress_canvas.create_rectangle(
                0, 5, canvas_width, 15,
                fill=self.theme_colors['progress_trough'],  # Theme-specific trough color
                outline=""
            )

            # Foreground (progress bar fill)
            self.day_progress_canvas.create_rectangle(
                0, 5, marker_x, 15,
                fill=self.theme_colors['progress_bg'],  # Theme-specific progress color
                outline=""
            )

            # Marker
            marker_size = 5
            self.day_progress_canvas.create_polygon(
                marker_x, 10 - marker_size,
                          marker_x - marker_size, 10,
                marker_x, 10 + marker_size,
                          marker_x + marker_size, 10,
                fill='red'  # Marker color, can also be themed
            )

    def apply_theme(self, theme_name):
        # Retrieve the theme class
        theme_class = ThemeManager.get_theme(theme_name)

        # Create an instance of the retrieved theme
        current_theme = theme_class()
        self.theme_colors = current_theme.get_colors()  # Retrieve the color dictionary

        # Apply the background color for the main window
        self.configure(bg=self.theme_colors.get('bg', 'white'))

        # Reinitialize ttk styles based on the selected theme
        style = Style()
        current_theme.apply_style(style)  # Applies ttk styles for the current theme

        # Apply theme to all widgets
        for widget in self.winfo_children():
            # Handle tk.Listbox
            if isinstance(widget, tk.Listbox):
                widget.configure(
                    bg=self.theme_colors.get('listbox_bg', 'white'),
                    fg=self.theme_colors.get('listbox_fg', 'black')
                )

            # Handle tk.Entry
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    bg=self.theme_colors.get('entry_bg', 'white'),
                    fg=self.theme_colors.get('entry_fg', 'black')
                )

            # Handle tk.Canvas for progress bar
            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=self.theme_colors.get('progress_trough', 'light gray'))
                self.update_day_progress(int(self.target_entry.get()))

            # Generic background configuration (for other non-ttk widgets)
            elif hasattr(widget, 'configure') and not isinstance(widget, ttk.Widget):
                try:
                    widget.configure(bg=self.theme_colors.get('bg', 'white'))
                except Exception as e:
                    print(f"Could not configure background for {widget}. Reason: {e}")

        # Save the user's selected theme to the database
        self.save_theme(theme_name)

        # Refresh the progress bar (ensure correct theme colors)
        self.update_day_progress(int(self.target_entry.get()))

    def add_current_target(self):
        if self.target_entry.get():
            try:
                timestamp = int(self.target_entry.get())
                self.save_timestamp(timestamp)
            except ValueError:
                messagebox.showerror("Error", "Invalid timestamp value")

    def validate_number(self, new_value: str) -> bool:
        if new_value == "" or new_value == "-":
            return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False

    def use_current_timestamp(self):
        current_ts = PosixTime.now()
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, str(current_ts))
        self.update_labels()

    def star_timestamp(self):
        selection = self.timestamp_listbox.curselection()
        if selection:
            index = selection[0]
            timestamp = self.saved_timestamps[index]
            cursor = self.db_conn.cursor()
            cursor.execute("UPDATE timestamps SET starred = NOT starred WHERE timestamp = ?", (timestamp,))
            self.db_conn.commit()
            self.load_timestamps()
            self.update_timestamp_list()
            self.update_delete_button_state(index)

    def edit_timestamp(self):
        selection = self.timestamp_listbox.curselection()
        if selection:
            index = selection[0]
            old_timestamp = self.saved_timestamps[index]
            edit_dialog = tk.Toplevel(self)
            edit_dialog.title("Edit Timestamp")
            edit_dialog.geometry("300x100")
            edit_dialog.transient(self)
            edit_dialog.grab_set()
            ttk.Label(edit_dialog, text="New timestamp value:").pack(pady=5)
            entry = ttk.Entry(edit_dialog)
            entry.insert(0, old_timestamp)
            entry.pack(pady=5)

            def save_edit():
                try:
                    new_timestamp = int(entry.get())
                    cursor = self.db_conn.cursor()
                    cursor.execute("UPDATE timestamps SET timestamp = ? WHERE timestamp = ?",
                                   (new_timestamp, old_timestamp))
                    self.db_conn.commit()
                    self.load_timestamps()
                    self.update_timestamp_list()
                    edit_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Invalid timestamp value")

            ttk.Button(edit_dialog, text="Save", command=save_edit).pack(pady=5)

    def delete_timestamp(self):
        selection = self.timestamp_listbox.curselection()
        if selection:
            index = selection[0]
            timestamp = self.saved_timestamps[index]
            cursor = self.db_conn.cursor()
            cursor.execute("DELETE FROM timestamps WHERE timestamp = ?", (timestamp,))
            self.db_conn.commit()
            self.load_timestamps()
            self.update_timestamp_list()

    def update_labels(self):
        try:
            head = int(self.head_entry.get()) if self.head_entry.get() != "" else 0
        except ValueError:
            head = None
        try:
            target = int(self.target_entry.get()) if self.target_entry.get() != "" else None
        except ValueError:
            target = None
        try:
            tail = int(self.tail_entry.get()) if self.tail_entry.get() != "" else 0
        except ValueError:
            tail = None

        if target is not None:
            # Convert to UTC date
            date_utc = datetime.fromtimestamp(target, tz=timezone.utc)
            formatted_date = date_utc.strftime('%Y-%m-%d %H:%M:%S UTC')
            self.target_date_label.config(text=f"Date: {formatted_date}")

            # Update day position label
            day_of_month = date_utc.day
            self.month_progress_group.config(text=f"POSITION IN DAY {day_of_month}")
            self.update_day_progress(target)

            # Temporarily enable calendar for updates
            self.calendar.config(state='normal')
            self.calendar.selection_set(date_utc)
            self.calendar.see(date_utc)
            self.calendar.config(state='disabled')

            # Update head and tail labels
            self.update_head_tail_labels()
        else:
            self.target_date_label.config(text="Date: ")
            self.month_progress_group.config(text="POSITION IN DAY -")

            # Clear head and tail labels
            self.head_duration_label.config(text="Duration: ")
            self.head_date_label.config(text="Date (-HEAD): ")
            self.tail_duration_label.config(text="Duration: ")
            self.tail_date_label.config(text="Date (+TAIL): ")

    def increment_target(self):
        try:
            current = int(self.target_entry.get()) if self.target_entry.get() else 0
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(current + 1))
            self.update_labels()
        except ValueError:
            pass

    def decrement_target(self):
        try:
            current = int(self.target_entry.get()) if self.target_entry.get() else 0
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(current - 1))
            self.update_labels()
        except ValueError:
            pass

    def update_head_tail_labels(self):
        try:
            target = int(self.target_entry.get()) if self.target_entry.get() != "" else None
            head_value = self.head_entry.get()
            if head_value and target:
                head_seconds = int(head_value)
                head_timestamp = target - head_seconds
                head_date = datetime.fromtimestamp(head_timestamp, tz=timezone.utc)
                self.head_duration_label.config(text=f"Duration: {seconds_to_text(head_seconds)}")
                self.head_date_label.config(
                    text=f"Date (-HEAD): {head_date.strftime('%Y-%m-%d %H:%M:%S UTC')} | POSIX: {head_timestamp}")
            else:
                self.head_duration_label.config(text="Duration: ")
                self.head_date_label.config(text="Date (-HEAD): ")

            tail_value = self.tail_entry.get()
            if tail_value and target:
                tail_seconds = int(tail_value)
                tail_timestamp = target + tail_seconds
                tail_date = datetime.fromtimestamp(tail_timestamp, tz=timezone.utc)
                self.tail_duration_label.config(text=f"Duration: {seconds_to_text(tail_seconds)}")
                self.tail_date_label.config(
                    text=f"Date (+TAIL): {tail_date.strftime('%Y-%m-%d %H:%M:%S UTC')} | POSIX: {tail_timestamp}")
            else:
                self.tail_duration_label.config(text="Duration: ")
                self.tail_date_label.config(text="Date (+TAIL): ")
        except ValueError:
            self.head_duration_label.config(text="Duration: ")
            self.head_date_label.config(text="Date (-HEAD): ")
            self.tail_duration_label.config(text="Duration: ")
            self.tail_date_label.config(text="Date (+TAIL): ")

    def update_timer(self):
        now_dt = datetime.utcnow()
        ts = int(now_dt.timestamp())
        formatted_ts = f"{ts:,}"
        formatted_date = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        self.title(f"POSIX Timestamp Converter - POSIX: {formatted_ts} | Timestamp: {formatted_date}")
        delay = 1000 - (now_dt.microsecond // 1000)
        self.after(delay, self.update_timer)

    def set_head_from_preset(self, event=None):
        preset = self.head_combo.get()
        if preset in self.preset_mapping:
            self.head_entry.delete(0, tk.END)
            self.head_entry.insert(0, self.preset_mapping[preset])
            self.update_labels()

    def set_tail_from_preset(self, event=None):
        preset = self.tail_combo.get()
        if preset in self.preset_mapping:
            self.tail_entry.delete(0, tk.END)
            self.tail_entry.insert(0, self.preset_mapping[preset])
            self.update_labels()

    def update_timestamp_list(self):
        self.timestamp_listbox.delete(0, tk.END)
        for ts in self.saved_timestamps:
            prefix = "* " if ts in self.starred_timestamps else "  "
            self.timestamp_listbox.insert(tk.END, f"{prefix}{ts}")

    def update_delete_button_state(self, index):
        if index < len(self.saved_timestamps):
            timestamp = self.saved_timestamps[index]
            if timestamp in self.starred_timestamps:
                self.delete_button.state(['disabled'])
            else:
                self.delete_button.state(['!disabled'])

    def select_timestamp(self, event):
        selection = self.timestamp_listbox.curselection()
        if selection:
            index = selection[0]
            selected_timestamp = self.saved_timestamps[index]
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, selected_timestamp)
            self.update_labels()  # Add this line to refresh calendar and related labels
            self.update_delete_button_state(index)
        else:
            self.delete_button.state(['disabled'])


if __name__ == "__main__":
    app = TimestampApp()
    app.mainloop()
