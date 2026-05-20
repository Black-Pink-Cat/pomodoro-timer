from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.utils import platform

WORK_TIME = 25 * 60
SHORT_BREAK = 5 * 60
LONG_BREAK = 15 * 60
POMODOROS_BEFORE_LONG_BREAK = 4
CUSTOM_DEFAULT = 30 * 60

MODE_CONFIG = {
    "work":        {"accent": (1, 0.388, 0.278, 1), "label": "工作中"},
    "short_break": {"accent": (0.878, 0.333, 0.251, 1), "label": "短休息"},
    "long_break":  {"accent": (0.753, 0.224, 0.169, 1), "label": "长休息"},
    "custom":      {"accent": (0.851, 0.306, 0.216, 1), "label": "自定义"},
}

BG_COLOR = (1, 0.965, 0.957, 1)
TEXT_DARK = (0.361, 0.118, 0.086, 1)
TEXT_MUTED = (0.769, 0.584, 0.541, 1)


class TomatoButton(Button):
    def __init__(self, bg_color=(0.878, 0.333, 0.251, 1), **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            Rectangle(size=self.size, pos=self.pos)


class PomodoroRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(8)

        self.mode = "work"
        self.custom_seconds = CUSTOM_DEFAULT
        self.time_left = WORK_TIME
        self.completed = 0
        self.total_pomodoros = 0
        self.is_running = False
        self.timer_event = None
        self.sound = None

        self._init_sound()
        self._build_ui()
        self._update_display()

    def _init_sound(self):
        try:
            self.sound = SoundLoader.load("beep.wav")
        except Exception:
            self.sound = None

    def _build_ui(self):
        # 背景色
        with self.canvas.before:
            Color(*BG_COLOR)
            Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        # 标题
        self.title_label = Label(
            text="番茄钟",
            font_size=dp(24),
            color=TEXT_DARK,
            bold=True,
            size_hint=(1, None),
            height=dp(44),
        )
        self.add_widget(self.title_label)

        # 模式标签
        cfg = MODE_CONFIG[self.mode]
        self.mode_label = Label(
            text=cfg["label"],
            font_size=dp(16),
            color=cfg["accent"],
            bold=True,
            size_hint=(1, None),
            height=dp(32),
        )
        self.add_widget(self.mode_label)

        # 模式选择按钮行
        mode_btns = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(36),
            spacing=dp(4),
        )
        self.mode_buttons = {}
        for key, cfg in MODE_CONFIG.items():
            btn = Button(
                text=cfg["label"],
                font_size=dp(11),
                background_color=cfg["accent"] if key == self.mode else (0.91, 0.773, 0.733, 1),
                background_normal="",
                color=(1, 1, 1, 1),
                bold=True,
            )
            btn.bind(on_press=lambda _, k=key: self.switch_mode(k))
            mode_btns.add_widget(btn)
            self.mode_buttons[key] = btn
        self.add_widget(mode_btns)

        # 自定义时长选择器
        self.custom_box = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(36),
            spacing=dp(6),
        )
        self.custom_box.add_widget(Label(
            text="时长（分钟）:",
            font_size=dp(13),
            color=TEXT_MUTED,
            size_hint=(0.5, 1),
            halign="right",
            valign="middle",
        ))
        self.custom_spinner = Spinner(
            text="30",
            values=[str(i) for i in range(1, 121)],
            size_hint=(0.5, 1),
            font_size=dp(14),
            background_color=(0.878, 0.333, 0.251, 0.15),
            color=TEXT_DARK,
            sync_height=True,
        )
        self.custom_spinner.bind(text=self._on_custom_change)
        self.custom_box.add_widget(self.custom_spinner)
        self.add_widget(self.custom_box)
        self.custom_box.opacity = 0
        self.custom_box.disabled = True

        # 计时器
        self.timer_label = Label(
            text="25:00",
            font_size=dp(72),
            color=TEXT_DARK,
            bold=True,
            size_hint=(1, None),
            height=dp(100),
        )
        self.add_widget(self.timer_label)

        # 进度条
        self.progress = ProgressBar(
            max=100,
            value=100,
            size_hint=(1, None),
            height=dp(10),
            background_color=(0.91, 0.773, 0.733, 0.4),
        )
        self.add_widget(self.progress)

        # 计数
        self.counter_label = Label(
            text="已完成: 0 个番茄",
            font_size=dp(12),
            color=TEXT_MUTED,
            size_hint=(1, None),
            height=dp(24),
        )
        self.add_widget(self.counter_label)

        # 按钮
        btn_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(8),
        )
        self.btn_start = Button(
            text="开始",
            font_size=dp(15),
            background_color=MODE_CONFIG["work"]["accent"],
            background_normal="",
            color=(1, 1, 1, 1),
            bold=True,
        )
        self.btn_start.bind(on_press=self.start_timer)
        self.btn_pause = Button(
            text="暂停",
            font_size=dp(15),
            background_color=(1, 0.388, 0.278, 1),
            background_normal="",
            color=(1, 1, 1, 1),
            bold=True,
        )
        self.btn_pause.bind(on_press=self.pause_timer)
        self.btn_reset = Button(
            text="重置",
            font_size=dp(15),
            background_color=(0.831, 0.518, 0.459, 1),
            background_normal="",
            color=(1, 1, 1, 1),
            bold=True,
        )
        self.btn_reset.bind(on_press=self.reset_timer)
        btn_row.add_widget(self.btn_start)
        btn_row.add_widget(self.btn_pause)
        btn_row.add_widget(self.btn_reset)
        self.add_widget(btn_row)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*BG_COLOR)
            Rectangle(size=self.size, pos=self.pos)

    def _update_mode_btn_styles(self):
        for key, btn in self.mode_buttons.items():
            if key == self.mode:
                btn.background_color = MODE_CONFIG[key]["accent"]
            else:
                btn.background_color = (0.91, 0.773, 0.733, 1)

    def switch_mode(self, mode):
        if self.is_running:
            self._cancel_timer()
            self.is_running = False
            self.btn_start.text = "开始"
        self.mode = mode
        if mode == "custom":
            self.custom_seconds = int(self.custom_spinner.text) * 60
            self.custom_box.opacity = 1
            self.custom_box.disabled = False
        else:
            self.custom_box.opacity = 0
            self.custom_box.disabled = True
        self.time_left = self.total_seconds()
        self._sync_ui_mode()
        self._update_display()

    def _on_custom_change(self, _, text):
        if self.mode == "custom":
            self.custom_seconds = int(text) * 60
            self.time_left = self.custom_seconds
            self._update_display()

    def total_seconds(self):
        if self.mode == "custom":
            return self.custom_seconds
        return {
            "work": WORK_TIME,
            "short_break": SHORT_BREAK,
            "long_break": LONG_BREAK,
        }[self.mode]

    def _sync_ui_mode(self):
        cfg = MODE_CONFIG[self.mode]
        self.mode_label.text = cfg["label"]
        self.mode_label.color = cfg["accent"]
        self._update_mode_btn_styles()

    def _set_start_btn(self, enabled):
        cfg = MODE_CONFIG[self.mode]
        if enabled:
            self.btn_start.background_color = cfg["accent"]
            self.btn_start.disabled = False
        else:
            self.btn_start.background_color = (0.941, 0.816, 0.784, 1)
            self.btn_start.disabled = True

    def start_timer(self, *args):
        if self.is_running:
            return
        self.is_running = True
        self.btn_start.text = "运行中"
        self._set_start_btn(False)
        self.timer_event = Clock.schedule_interval(self._tick, 1)

    def pause_timer(self, *args):
        if not self.is_running:
            return
        self._cancel_timer()
        self.is_running = False
        self.btn_start.text = "开始"
        self._set_start_btn(True)

    def reset_timer(self, *args):
        self._cancel_timer()
        self.is_running = False
        self.btn_start.text = "开始"
        self.time_left = self.total_seconds()
        self._set_start_btn(True)
        self._update_display()

    def _cancel_timer(self):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def _tick(self, dt):
        if self.time_left <= 0:
            self._timer_finished()
            return False
        self.time_left -= 1
        self._update_display()

    def _timer_finished(self):
        self.is_running = False
        self.timer_event = None
        self.btn_start.text = "开始"
        self._play_sound()

        if self.mode == "work":
            self.completed += 1
            self.total_pomodoros += 1
            self.counter_label.text = f"已完成: {self.total_pomodoros} 个番茄"
            if self.completed % POMODOROS_BEFORE_LONG_BREAK == 0:
                self.mode = "long_break"
            else:
                self.mode = "short_break"
        else:
            self.mode = "work"

        self.time_left = self.total_seconds()
        self._sync_ui_mode()
        self._update_display()
        self._set_start_btn(True)

    def _play_sound(self):
        if self.sound:
            try:
                self.sound.play()
            except Exception:
                pass

    def _update_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.timer_label.text = f"{mins:02d}:{secs:02d}"
        total = self.total_seconds()
        self.progress.value = (self.time_left / total) * 100 if total > 0 else 0


class PomodoroApp(App):
    def build(self):
        return PomodoroRoot()


if __name__ == "__main__":
    PomodoroApp().run()
