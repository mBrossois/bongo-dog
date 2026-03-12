#!/usr/bin/env python3
"""
BongoDog 🐾 - PyQt5 desktop idle widget
Transparent background, draggable. Uses PNG assets for animation.

Requirements:
    pip install PyQt5

Assets expected in assets/ folder (PNG format):
    Dog-no-tongue.png
    Dog-with-tongue.png
    Dog-eyes-closed-no-tongue.png
    Dog-eyes-closed-tongue.png
    Dog-paw-left-down.png
    Dog-paw-right-down.png

Run:
    python bongodog.py
"""

import sys
import threading
import platform
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap

IS_MAC = platform.system() == "Darwin"

# ── Resolve asset paths ───────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

def asset(name):
    return os.path.join(ASSETS_DIR, name)

# PNG asset filenames
PNG_FILES = {
    "idle_normal":        "Dog-no-tongue.png",
    "idle_tongue":        "Dog-with-tongue.png",
    "eyes_closed":        "Dog-eyes-closed-no-tongue.png",
    "eyes_closed_tongue": "Dog-eyes-closed-tongue.png",
    "paw_left":           "Dog-paw-left-down.png",
    "paw_right":          "Dog-paw-right-down.png",
}

# Idle animation sequence: (frame_key, duration_in_ticks_at_60fps)
IDLE_SEQUENCE = [
    ("idle_normal",        90),   # ~1.5 s
    ("idle_tongue",        40),   # ~0.7 s
    ("idle_normal",        60),   # ~1.0 s
    ("eyes_closed",        50),   # ~0.8 s
    ("eyes_closed_tongue", 30),   # ~0.5 s
    ("eyes_closed",        30),   # ~0.5 s
    ("idle_normal",        70),   # ~1.2 s
]

# ── Window size ───────────────────────────────────────────────────────────────
# SVG viewBox is 600x640. Paw/drum impact is ~y=450 = 70% down.
# Scale image to widget width: img_h = 110 * (640/600) = ~117px
# Counter bar sits at the paw line: 117 * 0.70 = ~82px
IMG_SCALE     = 640 / 600          # SVG aspect ratio
DOG_W         = 110
IMG_H         = int(DOG_W * IMG_SCALE)   # ~117px — full scaled image height
PAW_Y         = int(IMG_H * 0.80)        # ~82px — where paws hit drum
COUNTER_H     = 28                       # counter bar height
D_W           = DOG_W
D_H           = PAW_Y + COUNTER_H       # widget clips below the drum
FPS = 60

# ── Colours ───────────────────────────────────────────────────────────────────
GOLD         = QColor(249, 196, 107)
CLOSE_HOT    = QColor(220, 80, 80)
CLOSE_NORMAL = QColor(160, 160, 180, 180)
WHITE        = QColor(255, 255, 255)

# ── Shared input state ────────────────────────────────────────────────────────
state = dict(keys=0, clicks=0, left_paw=False, right_paw=False)
_lock = threading.Lock()

# ── PNG loading ───────────────────────────────────────────────────────────────
def load_pixmaps():
    """Load each PNG asset into a QPixmap. Returns a dict of key -> QPixmap."""
    pixmaps = {}
    for key, png_filename in PNG_FILES.items():
        path = asset(png_filename)
        pm   = QPixmap(path)
        if pm.isNull():
            print(f"Warning: Failed to load {path}")
        pixmaps[key] = pm
    return pixmaps


# ── Global event monitoring (macOS) ───────────────────────────────────────────
_global_monitor       = None
_global_monitor_setup = False

def setup_global_event_monitor():
    global _global_monitor, _global_monitor_setup
    if not IS_MAC or _global_monitor_setup:
        return
    _global_monitor_setup = True
    try:
        from AppKit import (NSEvent, NSKeyDownMask, NSKeyUpMask,
                            NSLeftMouseDownMask, NSRightMouseDownMask,
                            NSLeftMouseUpMask, NSRightMouseUpMask)

        def handle_event(event):
            t = event.type()
            if t == 10:        # NSKeyDown
                with _lock:
                    state["keys"] += 1
                    if state["keys"] % 2 == 0:
                        state["left_paw"] = True;  state["right_paw"] = False
                    else:
                        state["right_paw"] = True; state["left_paw"]  = False
            elif t == 11:      # NSKeyUp
                with _lock:
                    state["left_paw"] = state["right_paw"] = False
            elif t in (1, 3):  # Mouse down
                with _lock:
                    state["clicks"] += 1
                    if state["clicks"] % 2 == 0:
                        state["left_paw"] = True;  state["right_paw"] = False
                    else:
                        state["right_paw"] = True; state["left_paw"]  = False
            elif t in (2, 4):  # Mouse up
                with _lock:
                    state["left_paw"] = state["right_paw"] = False

        mask = (NSKeyDownMask | NSKeyUpMask |
                NSLeftMouseDownMask | NSRightMouseDownMask |
                NSLeftMouseUpMask   | NSRightMouseUpMask)
        _global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, handle_event)
        print("Global event monitoring enabled")
    except ImportError as e:
        print(f"PyObjC not available: {e}")
    except Exception as e:
        print(f"Global event monitor error: {e}")


# ── macOS always-on-top ───────────────────────────────────────────────────────
_ns_window  = None
_setup_done = False

def mac_set_window_level(widget):
    global _ns_window, _setup_done
    if not IS_MAC:
        return
    try:
        import ctypes, objc
        from ctypes import c_void_p
        if _ns_window is None:
            ns_view    = objc.objc_object(c_void_p=c_void_p(int(widget.winId())))
            _ns_window = ns_view.window()
        if _ns_window:
            _ns_window.orderFrontRegardless()
            if not _setup_done:
                from AppKit import NSApp, NSApplicationActivationPolicyAccessory
                NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
                _ns_window.setLevel_(2000)
                _ns_window.setCollectionBehavior_(1 | 16)
                _ns_window.setFloatingPanel_(True)
                _ns_window.setHidesOnDeactivate_(False)
                _setup_done = True
    except Exception:
        _setup_done = True


# ── Widget ────────────────────────────────────────────────────────────────────
class BongoDogWidget(QWidget):
    def __init__(self, pixmaps):
        super().__init__()
        self.pixmaps = pixmaps

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground,    True)
        self.setFixedSize(D_W, D_H)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.idle_seq_idx   = 0
        self.idle_seq_ticks = 0
        self.tick           = 0

        self.dragging   = False
        self.drag_start = QPoint()

        self.f_counter = QFont("Georgia", 10)
        self.f_counter.setBold(True)

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(1000 // FPS)

        self.move(100, 100)

    def showEvent(self, event):
        super().showEvent(event)
        if IS_MAC:
            QTimer.singleShot(100, lambda: mac_set_window_level(self))

    def on_tick(self):
        self.tick += 1
        if IS_MAC:
            mac_set_window_level(self)

        with _lock:
            paw_active = state["left_paw"] or state["right_paw"]

        if not paw_active:
            self.idle_seq_ticks += 1
            _, duration = IDLE_SEQUENCE[self.idle_seq_idx]
            if self.idle_seq_ticks >= duration:
                self.idle_seq_ticks = 0
                self.idle_seq_idx   = (self.idle_seq_idx + 1) % len(IDLE_SEQUENCE)

        self.update()

    def _current_frame_key(self, s):
        if s["left_paw"]:
            return "paw_left"
        if s["right_paw"]:
            return "paw_right"
        frame_name, _ = IDLE_SEQUENCE[self.idle_seq_idx]
        return frame_name

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        with _lock:
            s = dict(state)

        # Counter bar drawn FIRST so the dog renders on top of it
        bar_rect = QRectF(0, PAW_Y, D_W, COUNTER_H)
        p.setBrush(QColor(60, 60, 60, 210))
        p.setPen(Qt.NoPen)
        p.drawRect(bar_rect)
        total = s["keys"] + s["clicks"]
        p.setFont(self.f_counter)
        p.setPen(GOLD)
        p.drawText(bar_rect, Qt.AlignCenter, f"{total:,}")

        # Dog image drawn AFTER so paws appear in front of the counter bar
        key = self._current_frame_key(s)
        pm  = self.pixmaps.get(key)
        if pm and not pm.isNull():
            pm_scaled = pm.scaled(
                DOG_W,
                IMG_H,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation,
            )
            p.drawPixmap(0, 0, pm_scaled)

        # Close button
        cx, cy = D_W - 16, D_H - 16
        mx = self.mapFromGlobal(self.cursor().pos()).x()
        my = self.mapFromGlobal(self.cursor().pos()).y()
        hot   = abs(mx - cx) < 9 and abs(my - cy) < 9
        color = CLOSE_HOT if hot else CLOSE_NORMAL
        p.setBrush(color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 7, cy - 7, 14, 14)
        p.setPen(QPen(WHITE, 1.5))
        p.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
        p.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        mx, my = event.pos().x(), event.pos().y()
        if abs(mx - (D_W - 16)) < 10 and abs(my - (D_H - 16)) < 10:
            QApplication.quit()
            return
        with _lock:
            state["clicks"] += 1
            if state["clicks"] % 2 == 0:
                state["left_paw"]  = True;  state["right_paw"] = False
            else:
                state["right_paw"] = True;  state["left_paw"]  = False
        self.dragging   = True
        self.drag_start = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_start)
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        with _lock:
            state["left_paw"] = state["right_paw"] = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QApplication.quit()
            return
        with _lock:
            state["keys"] += 1
            if state["keys"] % 2 == 0:
                state["left_paw"]  = True;  state["right_paw"] = False
            else:
                state["right_paw"] = True;  state["left_paw"]  = False

    def keyReleaseEvent(self, event):
        with _lock:
            state["left_paw"] = state["right_paw"] = False


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    pixmaps = load_pixmaps()
    widget = BongoDogWidget(pixmaps)
    widget.show()
    setup_global_event_monitor()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()