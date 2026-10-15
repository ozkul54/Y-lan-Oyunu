import json
import random
import tkinter as tk
import time
from collections import deque
from pathlib import Path

try:
    import winsound
except ImportError:
    winsound = None

BG = "#101a16"
BOARD = "#17251e"
GRID = "#20342a"
SNAKE = "#5bcf88"
HEAD = "#b7f36b"
FOOD = "#ff6b5f"
TEXT = "#eef5e9"
MUTED = "#9eaf9f"
OVER = "#ffd166"

MAP_OPTIONS = {
    "Küçük": (400, 400, 20),
    "Orta": (500, 500, 20),
    "Büyük": (600, 600, 20),
}
GRAPHIC_THEMES = {
    "Orman": {
        "board": "#17251e",
        "grid": "#20342a",
        "snake": "#5bcf88",
        "head": "#b7f36b",
        "food": "#ff6b5f",
        "food_shadow": "#713b3c",
    },
    "Okyanus": {
        "board": "#142630",
        "grid": "#24414b",
        "snake": "#53c7c3",
        "head": "#b4f1d0",
        "food": "#ff8066",
        "food_shadow": "#713b3c",
    },
    "Gün Batımı": {
        "board": "#30231f",
        "grid": "#4a332b",
        "snake": "#f29b62",
        "head": "#ffd166",
        "food": "#ff627d",
        "food_shadow": "#713b3c",
    },
}
SPEED_OPTIONS = {"Yavaş": 160, "Normal": 120, "Hızlı": 85}
MAP_SCORE_BONUSES = {"Küçük": 0, "Orta": 1, "Büyük": 2}
SPEED_SCORE_BONUSES = {"Yavaş": 0, "Normal": 1, "Hızlı": 2}
BONUS_FOOD_POINTS = 5
BONUS_FOOD_CHANCE = 0.25
SCORE_TABLE_TEXT = (
    "PUAN / YEM\n"
    "            Yavaş Normal Hızlı\n"
    "Küçük          1      2      3\n"
    "Orta           2      3      4\n"
    "Büyük          3      4      5"
)

# Taşınabilir (Portable) Disk / .exe Çalışma Yolu Desteği
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

RECORD_FILE = BASE_DIR / "yilan_rekor.json"
SETTINGS_FILE = BASE_DIR / "yilan_ayarlar.json"


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Yılan Oyunu - Taşınabilir Sürüm")
        self.root.resizable(False, False)

        self.game_started = False
        self.paused = False
        self.settings_from_game = False
        self.tick_after_id = None
        self.play_time = 0
        self.time_segment_started = None
        self.sound_enabled = True
        self.sound_volume = 0.7
        self.short_path_enabled = False
        self.theme_name = "Orman"
        self.show_grid = True
        self.last_manual_turn = None
        self.load_settings()
        self.theme_colors = GRAPHIC_THEMES[self.theme_name]
        self.selected_map = "Büyük"
        self.speed_var = tk.StringVar(value="Normal")
        self.tick_delay = SPEED_OPTIONS[self.speed_var.get()]
        self.points_per_food = 20
        self.root.configure(bg=BG)
        
        self.start_screen = tk.Frame(root, bg=BG, padx=44, pady=34)
        self.start_screen.pack(expand=True)

        tk.Label(
            self.start_screen,
            text="SNAKE  /  PORTABLE",
            fg=OVER,
            bg=BG,
            font=("Arial", 10, "bold"),
        ).pack(pady=(0, 10))

        title = tk.Label(
            self.start_screen,
            text="Yılan Oyunu",
            fg=TEXT,
            bg=BG,
            font=("Arial", 32, "bold"),
        )
        title.pack(pady=(0, 8))

        subtitle = tk.Label(
            self.start_screen,
            text="Yemleri topla, duvarlardan uzak dur.",
            fg=MUTED,
            bg=BG,
            font=("Arial", 11),
        )
        subtitle.pack(pady=(0, 26))

        self.map_frame = tk.Frame(self.start_screen, bg=BG)
        tk.Label(
            self.start_screen,
            text="HARİTA BOYUTU",
            fg=MUTED,
            bg=BG,
            font=("Arial", 9, "bold"),
        ).pack(pady=(0, 8))
        self.map_frame.pack(pady=(0, 20))

        self.map_buttons = {}
        for label, key in [("Küçük", "Küçük"), ("Orta", "Orta"), ("Büyük", "Büyük")]:
            btn = tk.Button(
                self.map_frame,
                text=label,
                width=10,
                bg=BOARD,
                fg=TEXT,
                activebackground="#294334",
                activeforeground=TEXT,
                relief=tk.FLAT,
                padx=8,
                pady=6,
                cursor="hand2",
                command=lambda k=key: self.set_map(k),
            )
            btn.pack(side=tk.LEFT, padx=8)
            self.map_buttons[key] = btn

        tk.Label(
            self.start_screen,
            text=SCORE_TABLE_TEXT,
            justify=tk.LEFT,
            fg=MUTED,
            bg=BG,
            font=("Consolas", 9),
        ).pack(pady=(0, 8))
        tk.Label(
            self.start_screen,
            text=f"ALTIN YEM  +{BONUS_FOOD_POINTS} PUAN",
            fg=OVER,
            bg=BG,
            font=("Arial", 9, "bold"),
        ).pack(pady=(0, 8))

        self.start_button = tk.Button(
            self.start_screen,
            text="OYNA",
            width=18,
            height=2,
            bg=HEAD,
            fg="#17251e",
            activebackground="#c9ff82",
            activeforeground="#17251e",
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 12, "bold"),
            command=self.start_game,
        )
        self.start_button.pack(pady=10)

        self.settings_button = tk.Button(
            self.start_screen,
            text="AYARLAR",
            width=18,
            bg=BG,
            fg=MUTED,
            activebackground=BG,
            activeforeground=TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 10, "bold"),
            command=self.open_settings,
        )
        self.settings_button.pack(pady=(4, 0))

        self.settings_screen = tk.Frame(root, bg=BG, padx=44, pady=34)
        self.settings_title = tk.Label(
            self.settings_screen,
            text="AYARLAR",
            fg=TEXT,
            bg=BG,
            font=("Arial", 28, "bold"),
        )
        self.settings_title.pack(pady=(10, 28))

        tk.Label(
            self.settings_screen,
            text="SES EFEKTİ",
            fg=MUTED,
            bg=BG,
            font=("Arial", 9, "bold"),
        ).pack(pady=(0, 8))
        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        self.sound_button = tk.Checkbutton(
            self.settings_screen,
            text="Puan sesi açık",
            variable=self.sound_var,
            command=self.toggle_sound,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=BOARD,
            font=("Arial", 11),
        )
        self.sound_button.pack(pady=(0, 10))

        tk.Label(
            self.settings_screen,
            text="SES SEVİYESİ",
            fg=MUTED,
            bg=BG,
            font=("Arial", 9, "bold"),
        ).pack(pady=(0, 8))
        self.sound_volume_var = tk.IntVar(value=int(self.sound_volume * 100))
        self.sound_volume_label = tk.Label(
            self.settings_screen,
            text=f"Ses: {self.sound_volume_var.get()}%",
            fg=TEXT,
            bg=BG,
            font=("Arial", 10, "bold"),
        )
        self.sound_volume_label.pack(pady=(0, 8))
        self.sound_slider = tk.Scale(
            self.settings_screen,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=220,
            variable=self.sound_volume_var,
            command=self.set_sound_volume,
            bg=BG,
            fg=TEXT,
            highlightbackground=BG,
            troughcolor=BOARD,
            activebackground=HEAD,
            sliderlength=18,
            showvalue=0,
        )
        self.sound_slider.pack(pady=(0, 18))

        self.short_path_var = tk.BooleanVar(value=self.short_path_enabled)
        self.short_path_button = tk.Checkbutton(
            self.settings_screen,
            text="Kısa yol otomatik yönlendirme açık",
            variable=self.short_path_var,
            command=self.toggle_short_path,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=BOARD,
            font=("Arial", 10),
        )
        self.short_path_button.pack(pady=(0, 18))

        tk.Label(
            self.settings_screen,
            text="GÖRÜNÜM TEMASI",
            fg=MUTED,
            bg=BG,
            font=("Arial", 9, "bold"),
        ).pack(pady=(0, 8))
        self.theme_var = tk.StringVar(value=self.theme_name)
        theme_frame = tk.Frame(self.settings_screen, bg=BG)
        theme_frame.pack(pady=(0, 10))
        self.theme_buttons = {}
        for theme_name, colors in GRAPHIC_THEMES.items():
            button = tk.Radiobutton(
                theme_frame,
                text=theme_name,
                value=theme_name,
                variable=self.theme_var,
                command=self.change_theme,
                indicatoron=False,
                width=11,
                padx=5,
                pady=7,
                bg=colors["board"],
                fg=colors["head"],
                selectcolor=colors["grid"],
                activebackground=colors["grid"],
                activeforeground=TEXT,
                relief=tk.FLAT,
                cursor="hand2",
            )
            button.pack(side=tk.LEFT, padx=4)
            self.theme_buttons[theme_name] = button

        self.grid_var = tk.BooleanVar(value=self.show_grid)
        self.grid_button = tk.Checkbutton(
            self.settings_screen,
            text="Tahta çizgilerini göster",
            variable=self.grid_var,
            command=self.toggle_grid,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=BOARD,
            font=("Arial", 10),
        )
        self.grid_button.pack(pady=(0, 18))

        tk.Label(
            self.settings_screen,
            text="OYUN HIZI",
            fg=MUTED,
            bg=BG,
            font=("Arial", 9, "bold"),
        ).pack(pady=(0, 8))
        speed_frame = tk.Frame(self.settings_screen, bg=BG)
        speed_frame.pack(pady=(0, 28))
        for speed in SPEED_OPTIONS:
            tk.Radiobutton(
                speed_frame,
                text=speed,
                value=speed,
                variable=self.speed_var,
                command=self.change_speed,
                indicatoron=False,
                width=8,
                padx=5,
                pady=8,
                bg=BOARD,
                fg=TEXT,
                selectcolor=HEAD,
                activebackground="#294334",
                activeforeground=TEXT,
                relief=tk.FLAT,
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=5)

        tk.Label(
            self.settings_screen,
            text=SCORE_TABLE_TEXT,
            justify=tk.LEFT,
            fg=MUTED,
            bg=BG,
            font=("Consolas", 9),
        ).pack(pady=(0, 12))
        tk.Label(
            self.settings_screen,
            text=f"ALTIN YEM  +{BONUS_FOOD_POINTS} PUAN",
            fg=OVER,
            bg=BG,
            font=("Arial", 9, "bold"),
        ).pack(pady=(0, 8))

        self.settings_back_button = tk.Button(
            self.settings_screen,
            text="GERİ DÖN",
            width=18,
            bg=HEAD,
            fg="#17251e",
            activebackground="#c9ff82",
            activeforeground="#17251e",
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 11, "bold"),
            command=self.close_settings,
        )
        self.settings_back_button.pack(pady=8)

        self.exit_game_button = tk.Button(
            self.settings_screen,
            text="OYUNDAN ÇIK",
            width=18,
            bg=BOARD,
            fg=TEXT,
            activebackground="#294334",
            activeforeground=TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 10, "bold"),
            command=self.return_to_menu,
        )
        self.exit_game_button.pack(pady=5)
        self.exit_game_button.pack_forget()

        self.quit_game_button = tk.Button(
            self.settings_screen,
            text="OYUNU KAPAT",
            width=18,
            bg="#4a2421",
            fg="#ffd6cb",
            activebackground="#65312c",
            activeforeground=TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 10, "bold"),
            command=self.root.destroy,
        )
        self.quit_game_button.pack(pady=5)
        self.quit_game_button.pack_forget()

        self.canvas = tk.Canvas(root, width=600, height=600, bg=BOARD, highlightthickness=0)
        self.canvas.pack_forget()

        self.score_bar = tk.Frame(root, bg=BG, pady=8)
        self.current_score_label = tk.Label(
            self.score_bar,
            text="PUAN  0",
            bg=BG,
            fg=TEXT,
            font=("Arial", 12, "bold"),
            padx=18,
        )
        self.current_score_label.pack(side=tk.LEFT)
        self.best_score = self.load_best_score()
        self.best_score_label = tk.Label(
            self.score_bar,
            text=f"REKOR  {self.best_score}",
            bg=BG,
            fg=OVER,
            font=("Arial", 12, "bold"),
            padx=18,
        )
        self.best_score_label.pack(side=tk.LEFT)
        self.time_label = tk.Label(
            self.score_bar,
            text="SÜRE  00:00",
            bg=BG,
            fg=MUTED,
            font=("Arial", 12, "bold"),
            padx=18,
        )
        self.time_label.pack(side=tk.LEFT)
        self.score_bar.pack_forget()

        self.width = 600
        self.height = 600
        self.cell_size = 20
        self.grid_width = self.width // self.cell_size
        self.grid_height = self.height // self.cell_size

        self.root.bind("<KeyPress>", self.on_key)
        self.set_map("Büyük")

    def start_game(self):
        self.game_started = True
        self.start_screen.pack_forget()
        self.settings_screen.pack_forget()
        self.canvas.pack(pady=5)
        self.score_bar.pack()
        self.reset()
        self.schedule_tick(150)

    def open_settings(self):
        self.settings_from_game = False
        self.settings_title.config(text="AYARLAR")
        self.settings_back_button.config(text="GERİ DÖN")
        self.exit_game_button.pack_forget()
        self.quit_game_button.pack_forget()
        self.start_screen.pack_forget()
        self.settings_screen.pack(expand=True)

    def close_settings(self):
        if self.settings_from_game:
            self.resume_game()
            return
        self.settings_screen.pack_forget()
        self.start_screen.pack(expand=True)

    def pause_game(self):
        if self.paused or self.game_over:
            return
        self.paused = True
        self.play_time += time.perf_counter() - self.time_segment_started
        self.time_segment_started = None
        if self.tick_after_id is not None:
            self.root.after_cancel(self.tick_after_id)
            self.tick_after_id = None
        self.update_time_label()
        self.settings_from_game = True
        self.settings_title.config(text="OYUN DURAKLATILDI")
        self.settings_back_button.config(text="OYUNA DÖN")
        self.exit_game_button.pack(pady=5)
        self.quit_game_button.pack(pady=5)
        self.canvas.pack_forget()
        self.score_bar.pack_forget()
        self.settings_screen.pack(expand=True)

    def return_to_menu(self):
        if self.tick_after_id is not None:
            self.root.after_cancel(self.tick_after_id)
            self.tick_after_id = None
        self.settings_screen.pack_forget()
        self.exit_game_button.pack_forget()
        self.quit_game_button.pack_forget()
        self.canvas.pack_forget()
        self.score_bar.pack_forget()
        self.game_started = False
        self.paused = False
        self.settings_from_game = False
        self.time_segment_started = None
        self.start_screen.pack(expand=True)

    def resume_game(self):
        self.settings_screen.pack_forget()
        self.exit_game_button.pack_forget()
        self.quit_game_button.pack_forget()
        self.canvas.pack(pady=5)
        self.score_bar.pack()
        self.paused = False
        self.settings_from_game = False
        self.time_segment_started = time.perf_counter()
        self.settings_title.config(text="AYARLAR")
        self.settings_back_button.config(text="GERİ DÖN")
        self.draw()
        self.schedule_tick(self.tick_delay)

    def schedule_tick(self, delay):
        self.tick_after_id = self.root.after(delay, self.tick)

    def update_time_label(self):
        elapsed = self.play_time
        if self.time_segment_started is not None and not self.paused:
            elapsed += time.perf_counter() - self.time_segment_started
        total_seconds = int(elapsed)
        minutes, seconds = divmod(total_seconds, 60)
        self.time_label.config(text=f"SÜRE  {minutes:02d}:{seconds:02d}")

    def toggle_sound(self):
        self.sound_enabled = self.sound_var.get()

    def toggle_short_path(self):
        self.short_path_enabled = self.short_path_var.get()
        self.save_settings()

    def load_settings(self):
        try:
            if SETTINGS_FILE.exists():
                with SETTINGS_FILE.open("r", encoding="utf-8") as settings_file:
                    settings = json.load(settings_file)
                if not isinstance(settings, dict):
                    return
                theme_name = settings.get("theme")
                if theme_name in GRAPHIC_THEMES:
                    self.theme_name = theme_name
                self.show_grid = bool(settings.get("show_grid", True))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def save_settings(self):
        try:
            with SETTINGS_FILE.open("w", encoding="utf-8") as settings_file:
                json.dump(
                    {
                        "theme": self.theme_name,
                        "show_grid": self.show_grid,
                        "short_path_enabled": self.short_path_enabled,
                    },
                    settings_file,
                    ensure_ascii=False,
                    indent=2,
                )
        except OSError:
            pass

    def change_theme(self):
        self.theme_name = self.theme_var.get()
        self.theme_colors = GRAPHIC_THEMES[self.theme_name]
        self.save_settings()
        if hasattr(self, "snake"):
            self.draw()

    def toggle_grid(self):
        self.show_grid = self.grid_var.get()
        self.save_settings()
        if hasattr(self, "snake"):
            self.draw()

    def set_sound_volume(self, value):
        self.sound_volume = max(0.0, min(1.0, int(value) / 100))
        if hasattr(self, "sound_volume_label"):
            self.sound_volume_label.config(text=f"Ses: {int(self.sound_volume * 100)}%")

    def change_speed(self):
        self.tick_delay = SPEED_OPTIONS[self.speed_var.get()]
        self.update_points_per_food()

    def update_points_per_food(self):
        map_bonus = MAP_SCORE_BONUSES[self.selected_map]
        speed_bonus = SPEED_SCORE_BONUSES[self.speed_var.get()]
        self.points_per_food = 1 + map_bonus + speed_bonus
        if hasattr(self, "current_score_label"):
            current_score = getattr(self, "score", 0)
            self.current_score_label.config(
                text=f"PUAN  {current_score:02d}  (+{self.points_per_food}/YEM)"
            )

    def set_map(self, map_name):
        self.selected_map = map_name
        self.width, self.height, self.cell_size = MAP_OPTIONS[map_name]
        self.grid_width = self.width // self.cell_size
        self.grid_height = self.height // self.cell_size
        self.update_points_per_food()
        self.root.geometry(f"{self.width + 20}x{self.height + 150}")
        self.canvas.config(width=self.width, height=self.height)

        for key, button in self.map_buttons.items():
            button.config(relief=tk.FLAT, bg=BOARD, fg=MUTED)
        self.map_buttons[map_name].config(bg=HEAD, fg="#17251e")

        if self.game_started:
            self.reset()

    def reset(self):
        self.snake = deque([
            (self.grid_width // 2, self.grid_height // 2),
            (self.grid_width // 2 - 1, self.grid_height // 2),
            (self.grid_width // 2 - 2, self.grid_height // 2),
        ])
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.bonus_food = None
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.paused = False
        self.play_time = 0
        self.time_segment_started = time.perf_counter()
        self.update_time_label()
        self.current_score_label.config(
            text=f"PUAN  0  (+{self.points_per_food}/YEM)"
        )
        self.best_score_label.config(text=f"REKOR  {self.best_score}")
        self.draw()

    def load_best_score(self):
        try:
            if RECORD_FILE.exists():
                with RECORD_FILE.open("r", encoding="utf-8") as record_file:
                    return max(0, int(json.load(record_file).get("best_score", 0)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
        return 0

    def save_best_score(self):
        try:
            with RECORD_FILE.open("w", encoding="utf-8") as record_file:
                json.dump({"best_score": self.best_score}, record_file)
        except OSError:
            pass

    def spawn_food(self, forbidden=()):
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if (x, y) not in self.snake and (x, y) not in forbidden:
                return (x, y)

    def on_key(self, event):
        if event.keysym == "Escape":
            if self.paused:
                self.resume_game()
            elif self.game_started and not self.game_over:
                self.pause_game()
            elif self.settings_screen.winfo_ismapped():
                self.close_settings()
            return

        if self.game_over:
            if event.keysym in ("Return", "space"):
                self.reset()
                self.schedule_tick(self.tick_delay)
            return

        key_map = {
            "Up": (0, -1),
            "Down": (0, 1),
            "Left": (-1, 0),
            "Right": (1, 0),
            "w": (0, -1),
            "s": (0, 1),
            "a": (-1, 0),
            "d": (1, 0),
        }
        new_dir = key_map.get(event.keysym)
        if new_dir is not None:
            if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
                self.next_direction = new_dir
                self.last_manual_turn = time.monotonic()

    def _distance(self, start, target):
        return abs(start[0] - target[0]) + abs(start[1] - target[1])

    def _target_food(self):
        if self.bonus_food is None:
            return self.food
        head = self.snake[0]
        if self._distance(head, self.bonus_food) < self._distance(head, self.food):
            return self.bonus_food
        return self.food

    def _get_path(self, start, goal, blocked):
        queue = deque([start])
        came_from = {start: None}

        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_cell = (current[0] + dx, current[1] + dy)
                if not (0 <= next_cell[0] < self.grid_width and 0 <= next_cell[1] < self.grid_height):
                    continue
                if next_cell in blocked or next_cell in came_from:
                    continue
                came_from[next_cell] = current
                queue.append(next_cell)

        if goal not in came_from:
            return []

        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from[current]
        return list(reversed(path))

    def _suggest_shortest_direction(self):
        if not self.snake or self.food is None:
            return None

        head = self.snake[0]
        target = self._target_food()
        blocked = set(self.snake[:-1])
        path = self._get_path(head, target, blocked)
        if len(path) < 2:
            return None

        next_step = path[1]
        direction = (next_step[0] - head[0], next_step[1] - head[1])
        return direction

    def play_score_sound(self):
        if not self.sound_enabled or winsound is None:
            return
        if self.sound_volume <= 0:
            return

        volume_factor = max(0.35, self.sound_volume)
        frequency = int(700 * (0.7 + volume_factor))
        duration = max(35, int(80 * volume_factor))
        try:
            winsound.Beep(frequency, duration)
        except RuntimeError:
            pass

    def tick(self):
        self.tick_after_id = None
        if self.paused or self.game_over:
            return

        self.update_time_label()
        if self.short_path_enabled:
            last_manual = self.last_manual_turn
            if last_manual is None or time.monotonic() - last_manual > 0.22:
                suggested_direction = self._suggest_shortest_direction()
                if suggested_direction is not None:
                    self.next_direction = suggested_direction

        if not self.game_over:
            self.direction = self.next_direction
            head_x = self.snake[0][0] + self.direction[0]
            head_y = self.snake[0][1] + self.direction[1]
            new_head = (head_x, head_y)

            if (
                head_x < 0
                or head_y < 0
                or head_x >= self.grid_width
                or head_y >= self.grid_height
                or new_head in self.snake
            ):
                self.game_over = True
                self.play_time += time.perf_counter() - self.time_segment_started
                self.time_segment_started = None
                self.update_time_label()
                self.current_score_label.config(text=f"OYUN BİTTİ  /  {self.score} PUAN")
                self.draw()
                self.root.after(150, self.tick)
                return

            ate_regular_food = new_head == self.food
            ate_bonus_food = new_head == self.bonus_food
            self.snake.appendleft(new_head)
            if ate_regular_food or ate_bonus_food:
                if ate_regular_food:
                    self.score += self.points_per_food
                    self.food = self.spawn_food(forbidden=(self.bonus_food,))
                    if self.bonus_food is None and random.random() < BONUS_FOOD_CHANCE:
                        self.bonus_food = self.spawn_food(forbidden=(self.food,))
                if ate_bonus_food:
                    self.score += BONUS_FOOD_POINTS
                    self.bonus_food = None
                self.play_score_sound()
                if self.score > self.best_score:
                    self.best_score = self.score
                    self.save_best_score()
                    self.best_score_label.config(text=f"REKOR  {self.best_score}")
                if ate_bonus_food:
                    self.current_score_label.config(
                        text=f"ALTIN +{BONUS_FOOD_POINTS}  /  PUAN {self.score:02d}"
                    )
                else:
                    self.current_score_label.config(
                        text=f"PUAN  {self.score:02d}  (+{self.points_per_food}/YEM)"
                    )
            else:
                self.snake.pop()

        self.draw()
        if not self.game_over:
            self.schedule_tick(self.tick_delay)

    def draw(self):
        self.canvas.delete("all")

        self.canvas.create_rectangle(
            0, 0, self.width, self.height, fill=self.theme_colors["board"], outline=""
        )
        if self.show_grid:
            for x in range(0, self.width, self.cell_size):
                self.canvas.create_line(x, 0, x, self.height, fill=self.theme_colors["grid"])
            for y in range(0, self.height, self.cell_size):
                self.canvas.create_line(0, y, self.width, y, fill=self.theme_colors["grid"])

        for index, part in reversed(list(enumerate(self.snake))):
            x1 = part[0] * self.cell_size
            y1 = part[1] * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            color = self.theme_colors["head"] if index == 0 else self.theme_colors["snake"]
            inset = 2 if index else 1
            self.canvas.create_oval(
                x1 + inset,
                y1 + inset,
                x2 - inset,
                y2 - inset,
                fill=color,
                outline="",
            )

        head_x = self.snake[0][0] * self.cell_size
        head_y = self.snake[0][1] * self.cell_size
        eye_positions = {
            (1, 0): ((head_x + 13, head_y + 6), (head_x + 13, head_y + 14)),
            (-1, 0): ((head_x + 7, head_y + 6), (head_x + 7, head_y + 14)),
            (0, -1): ((head_x + 6, head_y + 7), (head_x + 14, head_y + 7)),
            (0, 1): ((head_x + 6, head_y + 13), (head_x + 14, head_y + 13)),
        }
        for eye_x, eye_y in eye_positions[self.direction]:
            self.canvas.create_oval(eye_x - 1.5, eye_y - 1.5, eye_x + 1.5, eye_y + 1.5, fill=BG, outline="")

        fx = self.food[0] * self.cell_size
        fy = self.food[1] * self.cell_size
        self.canvas.create_oval(
            fx + 1,
            fy + 1,
            fx + self.cell_size - 1,
            fy + self.cell_size - 1,
            fill="#713b3c",
            outline="",
        )
        self.canvas.create_oval(
            fx + 3,
            fy + 3,
            fx + self.cell_size - 3,
            fy + self.cell_size - 3,
            fill=self.theme_colors["food"],
            outline="",
        )

        if self.bonus_food is not None:
            bonus_x = self.bonus_food[0] * self.cell_size
            bonus_y = self.bonus_food[1] * self.cell_size
            self.canvas.create_oval(
                bonus_x + 1,
                bonus_y + 1,
                bonus_x + self.cell_size - 1,
                bonus_y + self.cell_size - 1,
                fill="#9a701c",
                outline="",
            )
            self.canvas.create_oval(
                bonus_x + 3,
                bonus_y + 3,
                bonus_x + self.cell_size - 3,
                bonus_y + self.cell_size - 3,
                fill=OVER,
                outline="",
            )
            self.canvas.create_oval(
                bonus_x + 7,
                bonus_y + 7,
                bonus_x + 13,
                bonus_y + 13,
                fill="#fff3c4",
                outline="",
            )

        if self.game_over:
            self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#101a16", stipple="gray50", outline="")
            self.canvas.create_rectangle(50, self.height / 2 - 65, self.width - 50, self.height / 2 + 65, fill=BG, outline=OVER, width=2)
            self.canvas.create_text(self.width / 2, self.height / 2 - 22, text="OYUN BİTTİ", fill=OVER, font=("Arial", 24, "bold"))
            self.canvas.create_text(self.width / 2, self.height / 2 + 20, text="Enter veya Space ile yeniden başla", fill=TEXT, font=("Arial", 11))


def main():
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
    