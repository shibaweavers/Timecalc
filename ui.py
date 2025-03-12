import tkinter.font as tkFont
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
        # self.use_current_timestamp()  # Add this line to call paste_current_timestamp on startup
        self.use_days_first_second()  # Set today's first second as the default TARGET
        self.update_timestamp_list()

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
            print(f"Timestamp {timestamp} successfully saved.")  # Debug output
            self.load_timestamps()
            self.update_timestamp_list()
        except sqlite3.IntegrityError as e:
            print(f"Failed to save timestamp {timestamp}: {e}")  # Debug error message

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        # Theme selection frame
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

        # Upper frame for TARGET and BOOKMARKS groups
        upper_frame = ttk.Frame(main_frame)
        upper_frame.pack(fill=tk.BOTH, expand=True)

        # TARGET group
        target_group = ttk.LabelFrame(upper_frame, text="TARGET", relief="groove", borderwidth=2)
        target_group.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        # Target frame for increment, decrement, and target entry
        target_frame = ttk.Frame(target_group)
        target_frame.pack(padx=5, pady=5, fill=tk.X)
        self.decrement_button = ttk.Button(target_frame, text="←", width=3, command=self.decrement_target)
        self.decrement_button.pack(side=tk.LEFT, padx=(0, 2))
        self.increment_button = ttk.Button(target_frame, text="→", width=3, command=self.increment_target)
        self.increment_button.pack(side=tk.LEFT, padx=(0, 2))

        # Target entry box
        vcmd = (self.register(self.validate_number), '%P')
        self.target_entry = ttk.Entry(target_frame, validate="key", validatecommand=vcmd, width=20)
        self.target_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        current_ts = PosixTime.now()
        self.target_entry.insert(0, str(current_ts))
        self.add_button = ttk.Button(target_frame, text="+", width=3, command=self.add_current_target)
        self.add_button.pack(side=tk.LEFT, padx=(2, 0))

        # Target date label
        self.target_date_label = ttk.Label(target_group, text="Date: ")
        self.target_date_label.pack(fill=tk.X, padx=5)

        # Use Current button (First row)
        self.use_current_button = ttk.Button(target_group, text="Use Current", command=self.use_current_timestamp)
        self.use_current_button.pack(pady=5, padx=5, fill=tk.X)

        # Second row frame for "Use day's first second" and "Use day's last second"
        second_row_frame = ttk.Frame(target_group)
        second_row_frame.pack(pady=(0, 5), padx=5, fill=tk.X)

        # Add buttons for the second row
        self.use_first_second_button = ttk.Button(
            second_row_frame, text="Use day's first second", command=self.use_days_first_second
        )
        self.use_first_second_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.use_last_second_button = ttk.Button(
            second_row_frame, text="Use day's last second", command=self.use_days_last_second
        )
        self.use_last_second_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Enable and pack the calendar widget
        calendar_frame = ttk.Frame(target_group)
        calendar_frame.pack(pady=5, expand=True)
        self.calendar = Calendar(calendar_frame, selectmode='day', date_pattern='yyyy-mm-dd', showweeknumbers=False,
                                 width=20, height=5, firstweekday='monday', disabledforeground='black',
                                 showothermonthdays=False, state='normal')  # Reenable the calendar
        self.calendar.pack(pady=5)

        # Bind calendar selection to update the target
        self.calendar.bind("<<CalendarSelected>>", lambda e: self.use_calendar_date())

        # POSITION IN DAY group for day progress
        self.month_progress_group = ttk.LabelFrame(target_group, text="POSITION IN DAY", relief="groove", borderwidth=2)
        self.month_progress_group.pack(fill=tk.X, padx=5, pady=(0, 5))
        progress_container = ttk.Frame(self.month_progress_group, width=1020)
        progress_container.pack(fill=tk.X, padx=5, pady=5)

        # POSITION IN DAY subframes with fixed sizes
        left_frame = ttk.Frame(progress_container, width=200, height=40)
        left_frame.pack_propagate(False)  # Prevent size from adjusting to content
        left_frame.pack(side=tk.LEFT, padx=2)

        middle_frame = ttk.Frame(progress_container, width=300, height=40)
        middle_frame.pack_propagate(False)
        middle_frame.pack(side=tk.LEFT, padx=2)

        right_frame = ttk.Frame(progress_container, width=200, height=40)
        right_frame.pack_propagate(False)
        right_frame.pack(side=tk.LEFT, padx=2)

        self.start_day_label = ttk.Label(left_frame, text="", anchor='center')
        self.start_day_label.pack(expand=False)



        self.day_progress_canvas = tk.Canvas(middle_frame, height=20, bg='white')
        self.day_progress_canvas.pack(fill=tk.X, expand=True, padx=5)
        self.end_day_label = ttk.Label(right_frame, text="", anchor='center')
        self.end_day_label.pack(expand=False)





        # Enable mouse interaction on the day progress canvas
        self.day_progress_canvas.bind("<Button-1>", self.set_target_from_progress)  # Handle single click
        self.day_progress_canvas.bind("<B1-Motion>", self.set_target_from_progress)  # Handle click and drag

        # BOOKMARKS group
        bookmarks_group = ttk.LabelFrame(upper_frame, text="BOOKMARKS", relief="groove", borderwidth=2)
        bookmarks_group.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Define a monospace font for timestamps listbox
        monospace_font = tkFont.Font(family="Courier", size=10)

        self.timestamp_listbox = tk.Listbox(bookmarks_group, width=20, font=monospace_font)
        self.timestamp_listbox.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        # Buttons below the Listbox in BOOKMARKS group
        buttons_frame = ttk.Frame(bookmarks_group)
        buttons_frame.pack(pady=5, padx=5)
        self.star_button = ttk.Button(buttons_frame, text="Star", width=4, command=self.star_timestamp)
        self.star_button.pack(side=tk.LEFT, padx=2)
        self.edit_button = ttk.Button(buttons_frame, text="Edit", width=5, command=self.edit_timestamp)
        self.edit_button.pack(side=tk.LEFT, padx=2)
        self.delete_button = ttk.Button(buttons_frame, text="Del", width=3, command=self.delete_timestamp)
        self.delete_button.pack(side=tk.LEFT, padx=2)
        self.delete_button.state(['disabled'])

        # Bind Listbox selection
        self.timestamp_listbox.bind("<<ListboxSelect>>", self.select_timestamp)

        # Output frame for HEAD and TAIL
        lower_frame = ttk.Frame(main_frame)
        lower_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

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

        start_str = f"{format(int(start_of_day), ',')}\n{seconds_to_text(target - int(start_of_day), output_format=-3)}"
        end_str = f"{format(int(end_of_day), ',')}\n{seconds_to_text(target - int(end_of_day), output_format=-3)}"

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
            # self.calendar.config(state='normal')
            self.calendar.selection_set(date_utc)
            self.calendar.see(date_utc)
            # self.calendar.config(state='disabled')

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
        """
        Populate the timestamp list in the Listbox. The items in the list will be ordered by the
        numerical value of the POSIX timestamps. Each list item will display the timestamp and its
        UTC date in the format: [* or space] [POSIX timestamp] [UTC date].
        """
        self.timestamp_listbox.delete(0, tk.END)  # Clear the existing listbox items

        # Combine starred and regular timestamps into a single list with a flag for "starred"
        timestamps = []
        for ts in self.starred_timestamps:
            timestamps.append((int(ts), True))  # Flag as starred
        for ts in self.saved_timestamps:
            if ts not in self.starred_timestamps:
                timestamps.append((int(ts), False))  # Flag as regular

        # Sort timestamps numerically in ascending order
        timestamps.sort(key=lambda x: x[0])  # Sort by numerical POSIX timestamp

        # Populate the Listbox, with each entry formatted as [* or space] [timestamp] [ymd hms UTC]
        for timestamp, is_starred in timestamps:
            utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            prefix = "* " if is_starred else "  "  # Add '*' for starred timestamps
            self.timestamp_listbox.insert(tk.END, f"{prefix}{timestamp} {utc_time}")

    def update_delete_button_state(self, index):
        if index < len(self.saved_timestamps):
            timestamp = self.saved_timestamps[index]
            if timestamp in self.starred_timestamps:
                self.delete_button.state(['disabled'])
            else:
                self.delete_button.state(['!disabled'])

    def set_target_from_progress(self, event):
        """Update TARGET based on progress bar click/drag, constrained within the TARGET-selected date."""
        # Get the current TARGET date as the base
        current_target = self.get_target_datetime()
        if not current_target:
            return

        # Calculate the start and end of the day for the TARGET date
        start_of_day = datetime(current_target.year, current_target.month, current_target.day,
                                tzinfo=timezone.utc).timestamp()
        end_of_day = datetime(current_target.year, current_target.month, current_target.day, 23, 59, 59,
                              tzinfo=timezone.utc).timestamp()

        # Get the click position
        canvas_width = self.day_progress_canvas.winfo_width()
        if canvas_width > 0:
            # Calculate the progress as a decimal (from 0.0 to 1.0)
            click_x = event.x
            progress = click_x / canvas_width

            # Map progress to the timestamp range for the current TARGET-selected day
            target = start_of_day + (progress * (end_of_day - start_of_day))

            # Clamp the value to ensure the target stays within the day
            target = max(start_of_day, min(target, end_of_day))

            # Update TARGET entry
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(int(target)))

            # Update labels and other UI elements
            self.update_labels()

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

    def use_days_first_second(self):
        """Set the TARGET entry to the first second of the date in TARGET."""
        current_target = self.get_target_datetime()
        if current_target:
            start_of_day = datetime(current_target.year, current_target.month, current_target.day,
                                    tzinfo=timezone.utc).timestamp()
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(int(start_of_day)))
            self.update_labels()

    def use_days_last_second(self):
        """Set the TARGET entry to the last second of the date in TARGET."""
        current_target = self.get_target_datetime()
        if current_target:
            end_of_day = datetime(current_target.year, current_target.month, current_target.day, 23, 59, 59,
                                  tzinfo=timezone.utc).timestamp()
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(int(end_of_day)))
            self.update_labels()

    def use_calendar_date(self):
        """Update the TARGET when selecting a new date, preserving the current time."""
        # Get the currently selected time (hour, minute, second) from TARGET
        current_target = self.get_target_datetime()
        if not current_target:
            return  # If TARGET is invalid, do nothing

        # Extract the currently selected hour, minute, and second
        current_time = (current_target.hour, current_target.minute, current_target.second)

        # Get the new date selected on the calendar
        calendar_date = self.calendar.get_date()  # Returns 'yyyy-mm-dd' string
        new_date = datetime.strptime(calendar_date, "%Y-%m-%d")  # Convert selected date to datetime object

        # Combine the selected date with the current time
        new_target = datetime(new_date.year, new_date.month, new_date.day,
                              current_time[0], current_time[1], current_time[2], tzinfo=timezone.utc).timestamp()

        # Update the TARGET entry with the newly calculated timestamp
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, str(int(new_target)))

        # Update labels and refresh the UI
        self.update_labels()

    def get_target_datetime(self):
        """Parse the TARGET timestamp into a datetime object."""
        try:
            target_timestamp = int(self.target_entry.get().strip())
            return datetime.fromtimestamp(target_timestamp, tz=timezone.utc)
        except ValueError:
            # Handle invalid input gracefully
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(int(PosixTime.now())))  # Reset to current timestamp
            self.update_labels()
            return None


if __name__ == "__main__":
    app = TimestampApp()
    app.mainloop()
