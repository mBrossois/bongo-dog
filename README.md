# BongoDog 🐾

A desktop idle widget inspired by Bongo Cat — but make it a dog. BongoDog sits transparently on top of all your windows, animating through a sequence of adorable poses while you work. When you type or click, the dog reacts by banging its paws on a drum, and a counter tracks your total keypresses and clicks.

---

## Features

- **Always-on-top** transparent overlay — lives above every window
- **Idle animation** cycles through resting, panting, blinking, and dozing poses
- **Reactive paws** — left/right paw animations trigger on keystrokes and mouse clicks
- **Input counter** displays your total key + click count
- **Draggable** — click and drag to reposition anywhere on screen
- **macOS global event monitoring** — reacts to input even when another app is focused (requires PyObjC)

---

## Requirements

```bash
pip install PyQt5
```

For macOS global input monitoring (optional but recommended):

```bash
pip install pyobjc pyobjc-framework-AppKit
```

---

## How to Use

### Running the app

```bash
python bongodog.py
```

The dog will appear in the top-left corner of your screen. You can drag it anywhere.

### Controls

| Action | Effect |
|---|---|
| **Type anything** | Dog reacts — paws alternate left/right |
| **Click anywhere** | Same paw reaction as typing |
| **Click and drag** | Move the widget around your screen |
| **Click ✕ button** | Close the app (bottom-right corner of widget) |
| **Escape key** | Also closes the app |

### Asset layout

The app expects an `assets/` folder next to `bongodog.py` containing these PNGs:

```
assets/
├── Dog-no-tongue.png
├── Dog-with-tongue.png
├── Dog-eyes-closed-no-tongue.png
├── Dog-eyes-closed-tongue.png
├── Dog-paw-left-down.png
└── Dog-paw-right-down.png
```

Export them at 2× your intended display size (e.g. 600×640) for crisp rendering on retina displays. Make sure to export with a transparent background.

### Idle animation sequence

When you're not typing or clicking, the dog cycles through:

1. **Resting** (`Dog-no-tongue.png`) — ~1.5 s
2. **Panting** (`Dog-with-tongue.png`) — ~0.7 s
3. **Resting** — ~1 s
4. **Eyes closed** (`Dog-eyes-closed-no-tongue.png`) — ~0.8 s
5. **Eyes closed + tongue** (`Dog-eyes-closed-tongue.png`) — ~0.5 s
6. **Eyes closed** — ~0.5 s
7. **Resting** — ~1.2 s
8. *(loops)*

### macOS notes

On macOS, the app uses PyObjC to:
- Float above all windows, including full-screen apps
- Monitor keyboard and mouse input **globally** (so the dog reacts even when another app is focused)
- Run as an accessory app (no Dock icon, no Cmd+Tab entry)

You may be prompted to grant **Accessibility permissions** in System Settings → Privacy & Security → Accessibility. This is required for global input monitoring.

---

## Troubleshooting

**Dog doesn't react when another app is focused (macOS)**
Grant Accessibility permissions to Terminal (or whichever app you used to launch the script) in System Settings → Privacy & Security → Accessibility.

**Images not showing**
Make sure the `assets/` folder is in the same directory as `bongodog.py` and all six PNG files are present. Check the terminal output on launch for any per-file warnings.

**Window disappears behind other windows**
On non-macOS platforms, `WindowStaysOnTopHint` should keep it on top. If not, try relaunching — some compositors handle this inconsistently.