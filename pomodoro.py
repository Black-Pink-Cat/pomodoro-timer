import tkinter as tk
from tkinter import ttk, messagebox
import winsound

WORK_TIME = 25 * 60
SHORT_BREAK = 5 * 60
LONG_BREAK = 15 * 60
POMODOROS_BEFORE_LONG_BREAK = 4

TICK_MS = 1000
WINDOW_SIZE = "380x440"
DISABLED_BTN = "#D5D8DC"
BG_COLOR = "#FFFFFF"

MODE_CONFIG = {
    "work":        {"bg": "#FFF5F5", "accent": "#E74C3C", "btn": "#E74C3C",
                    "label": "工作中",   "seconds": WORK_TIME},
    "short_break": {"bg": "#F0FFF0", "accent": "#2ECC71", "btn": "#2ECC71",
                    "label": "短休息", "seconds": SHORT_BREAK},
    "long_break":  {"bg": "#F0F4FF", "accent": "#3498DB", "btn": "#3498DB",
                    "label": "长休息", "seconds": LONG_BREAK},
}


class PomodoroApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("番茄钟")
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg=BG_COLOR)

        self.mode = "work"
        self.time_left = MODE_CONFIG["work"]["seconds"]
        self.completed = 0
        self.total_pomodoros = 0
        self.is_running = False
        self.after_id = None

        self.build_ui()
        self.update_display()

    def build_ui(self):
        self.title_label = tk.Label(
            self.root, text="🍅 番茄钟", font=("Microsoft YaHei", 18, "bold"),
            bg=BG_COLOR, fg="#333333"
        )
        self.title_label.pack(pady=(22, 12))

        self.mode_label = tk.Label(
            self.root, text=MODE_CONFIG[self.mode]["label"],
            font=("Microsoft YaHei", 13, "bold"),
            bg=MODE_CONFIG[self.mode]["bg"],
            fg=MODE_CONFIG[self.mode]["accent"],
            padx=28, pady=5
        )
        self.mode_label.pack()

        self.timer_label = tk.Label(
            self.root, text="25:00",
            font=("Consolas", 58, "bold"),
            bg=BG_COLOR, fg="#2C3E50"
        )
        self.timer_label.pack(pady=(16, 8))

        self.progress = ttk.Progressbar(self.root, length=320, mode='determinate')
        self.progress.pack(pady=(4, 12))
        self.progress['value'] = 100

        self.counter_label = tk.Label(
            self.root, text="已完成: 0 个番茄",
            font=("Microsoft YaHei", 10),
            bg=BG_COLOR, fg="#999999"
        )
        self.counter_label.pack(pady=(0, 18))

        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=(0, 20))

        self.btn_start = self._make_btn(btn_frame, "开始", MODE_CONFIG["work"]["btn"], self.start_timer)
        self.btn_pause = self._make_btn(btn_frame, "暂停", "#F39C12", self.pause_timer)
        self.btn_reset = self._make_btn(btn_frame, "重置", "#95A5A6", self.reset_timer)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _make_btn(self, parent, text, color, command):
        btn = tk.Button(
            parent, text=text, command=command,
            font=("Microsoft YaHei", 11, "bold"),
            bg=color, fg="white",
            activebackground="#BDC3C7", activeforeground="white",
            relief="flat", padx=22, pady=7, width=7, cursor="hand2"
        )
        btn.pack(side=tk.LEFT, padx=5)
        return btn

    def total_seconds(self):
        return MODE_CONFIG[self.mode]["seconds"]

    def _cancel_timer(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _set_start_btn(self, enabled):
        if enabled:
            self.btn_start.config(state=tk.NORMAL, bg=MODE_CONFIG[self.mode]["btn"])
        else:
            self.btn_start.config(state=tk.DISABLED, bg=DISABLED_BTN)

    def start_timer(self):
        if self.is_running:
            return
        self.is_running = True
        self._set_start_btn(False)
        self.tick()

    def pause_timer(self):
        if not self.is_running:
            return
        self._cancel_timer()
        self.is_running = False
        self._set_start_btn(True)

    def reset_timer(self):
        self._cancel_timer()
        self.is_running = False
        self.time_left = self.total_seconds()
        self._set_start_btn(True)
        self.update_display()

    def tick(self):
        if not self.is_running:
            return
        if self.time_left <= 0:
            self.timer_finished()
            return

        self.time_left -= 1
        self.update_display()
        self.after_id = self.root.after(TICK_MS, self.tick)

    def timer_finished(self):
        self.is_running = False
        self.after_id = None
        self._play_sound()

        if self.mode == "work":
            self.completed += 1
            self.total_pomodoros += 1
            self.counter_label.config(text=f"已完成: {self.total_pomodoros} 个番茄")

            if self.completed % POMODOROS_BEFORE_LONG_BREAK == 0:
                self.mode = "long_break"
                msg = "完成 4 个番茄！休息 15 分钟吧 🎉"
            else:
                self.mode = "short_break"
                msg = "番茄完成！休息 5 分钟吧 ☕"
        else:
            msg = "休息结束，开始新的番茄！💪"
            self.mode = "work"

        self.time_left = self.total_seconds()
        self._sync_ui_mode()
        self.update_display()
        self._set_start_btn(True)
        self.root.after(200, lambda: messagebox.showinfo("番茄钟提醒", msg))

    def _play_sound(self):
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except Exception:
            try:
                winsound.MessageBeep()
            except Exception:
                pass

    def _sync_ui_mode(self):
        cfg = MODE_CONFIG[self.mode]
        self.mode_label.config(text=cfg["label"], bg=cfg["bg"], fg=cfg["accent"])

    def update_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        total = self.total_seconds()
        self.progress['value'] = (self.time_left / total) * 100 if total > 0 else 0

    def on_closing(self):
        self._cancel_timer()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PomodoroApp().run()
