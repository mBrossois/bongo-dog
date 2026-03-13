# 🐾 BongoDog — Tauri Desktop Widget

A transparent, always-on-top desktop idle widget that animates a dog and reacts to keyboard/mouse events. Built with Tauri 2 (Rust + HTML/JS), ported from the original PyQt5 version.

## Window
- **110 × 145 px** — frameless, transparent background
- Always on top, draggable by the dog image
- Close button (bottom-right ×)
- Gold counter bar shows total key + click count

## Animation
- Idle loop cycles through SVG frames automatically (~60 fps)
- On keydown or mousedown: switches to left/right paw frames (alternating)
- On keyup / mouseup: returns to idle loop

---

## Project Structure

```
bongodog/
├── index.html               ← Frontend (HTML/CSS/JS — all animation logic)
├── vite.config.js
├── package.json
├── assets/                  ← ⚠️  PUT YOUR SVG FILES HERE
│   ├── Dog-no-tongue.svg
│   ├── Dog-with-tongue.svg
│   ├── Dog-eyes-closed-no-tongue.svg
│   ├── Dog-eyes-closed-tongue.svg
│   ├── Dog-paw-left-down.svg
│   └── Dog-paw-right-down.svg
└── src-tauri/
    ├── tauri.conf.json
    ├── Cargo.toml
    └── src/
        ├── main.rs
        └── lib.rs
```

---

## Prerequisites

Install these once:

### 1. Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. Node.js (v18+)
Download from https://nodejs.org or use nvm:
```bash
nvm install 18
```

### 3. Tauri system dependencies

**macOS:**
```bash
xcode-select --install
```

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf
```

**Windows:**
Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

---

## Setup & Run

```bash
# 1. Install JS dependencies
npm install

# 2. Add your SVG assets to the assets/ folder (see filenames above)

# 3. Run in dev mode (hot reload)
npm run tauri dev

# 4. Build a release binary
npm run tauri build
```

The built app will be in `src-tauri/target/release/`.

---

## SVG Assets

Place your 6 SVG files in the `assets/` folder with **exactly these filenames**:

| File | Used when |
|------|-----------|
| `Dog-no-tongue.svg` | Default idle |
| `Dog-with-tongue.svg` | Idle with tongue |
| `Dog-eyes-closed-no-tongue.svg` | Eyes closed |
| `Dog-eyes-closed-tongue.svg` | Eyes closed + tongue |
| `Dog-paw-left-down.svg` | Left paw hit (even key/click) |
| `Dog-paw-right-down.svg` | Right paw hit (odd key/click) |

The SVGs are rendered at **110 × 117 px** — they can have any internal `viewBox`.

---

## Idle Animation Sequence

The idle loop (when no keys/mouse are pressed) cycles through frames at ~60 fps:

| Frame | Duration |
|-------|----------|
| idle_normal | ~1.5 s |
| idle_tongue | ~0.7 s |
| idle_normal | ~1.0 s |
| eyes_closed | ~0.8 s |
| eyes_closed_tongue | ~0.5 s |
| eyes_closed | ~0.5 s |
| idle_normal | ~1.2 s |

---

## Customisation

All animation timing is in `index.html` in the `IDLE_SEQUENCE` array:
```js
const IDLE_SEQUENCE = [
  { frame: 'idle_normal',        ticks: 90 },  // ticks at 60fps
  { frame: 'idle_tongue',        ticks: 40 },
  ...
];
```

Window size is set in `src-tauri/tauri.conf.json` under `app.windows[0]`.

---

## Notes on Global Input (outside the window)

The Python version used `NSEvent` (macOS-only) to capture global keyboard/mouse events even when the app was not focused. In Tauri the widget only counts input **while the window has focus** on all three platforms.

To add true global input capture:
- **macOS**: Use the `tauri-plugin-global-shortcut` plugin for keys, and a custom Rust `CGEvent` tap for mouse
- **Windows**: Add a Rust `SetWindowsHookEx` call in `lib.rs`
- **Linux**: Use `evdev` or `X11 XRecord`

These are advanced additions. For an idle widget that sits on screen, the in-window counting is usually sufficient.
