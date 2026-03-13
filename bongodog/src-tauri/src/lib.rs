use tauri::Emitter;
use std::sync::{Arc, Mutex};
use std::time::Duration;

#[derive(Default, Clone)]
struct InputState {
    keys: u64,
    clicks: u64,
    left_paw: bool,
    right_paw: bool,
}

#[derive(Clone, serde::Serialize)]
struct PawEvent {
    left_paw: bool,
    right_paw: bool,
    total: u64,
}

#[tauri::command]
fn quit() {
    std::process::exit(0);
}

pub fn run() {
    let input_state = Arc::new(Mutex::new(InputState::default()));

    let (tx, rx) = std::sync::mpsc::channel::<tauri::AppHandle>();
    let state_for_tick = input_state.clone();

    // Tick thread: emit paw state at ~60fps
    std::thread::spawn(move || {
        let app_handle = rx.recv().unwrap();
        loop {
            std::thread::sleep(Duration::from_millis(16));
            let s = state_for_tick.lock().unwrap().clone();
            let _ = app_handle.emit("paw-state", PawEvent {
                left_paw: s.left_paw,
                right_paw: s.right_paw,
                total: s.keys + s.clicks,
            });
        }
    });

    // Global input thread
    #[cfg(target_os = "macos")]
    {
        let state_for_input = input_state.clone();
        std::thread::spawn(move || {
            macos_event_tap(state_for_input);
        });
    }

    tauri::Builder::default()
        .manage(input_state.clone())
        .invoke_handler(tauri::generate_handler![quit])
        .setup(move |app| {
            tx.send(app.handle().clone()).unwrap();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(target_os = "macos")]
fn macos_event_tap(state: Arc<Mutex<InputState>>) {
    use core_foundation::runloop::{kCFRunLoopCommonModes, CFRunLoop};
    use core_graphics::event::{
        CGEventTap, CGEventTapLocation, CGEventTapOptions,
        CGEventTapPlacement, CGEventType,
    };

    let state_clone = state.clone();

    let tap = CGEventTap::new(
        CGEventTapLocation::HID,
        CGEventTapPlacement::HeadInsertEventTap,
        CGEventTapOptions::ListenOnly,
        vec![
            CGEventType::KeyDown,
            CGEventType::KeyUp,
            CGEventType::LeftMouseDown,
            CGEventType::LeftMouseUp,
            CGEventType::RightMouseDown,
            CGEventType::RightMouseUp,
        ],
        move |_, event_type, _| {
            let mut s = state_clone.lock().unwrap();
            match event_type {
                CGEventType::KeyDown => {
                    s.keys += 1;
                    s.left_paw  = s.keys % 2 == 0;
                    s.right_paw = !s.left_paw;
                }
                CGEventType::KeyUp => {
                    s.left_paw  = false;
                    s.right_paw = false;
                }
                CGEventType::LeftMouseDown | CGEventType::RightMouseDown => {
                    s.clicks += 1;
                    s.left_paw  = s.clicks % 2 == 0;
                    s.right_paw = !s.left_paw;
                }
                CGEventType::LeftMouseUp | CGEventType::RightMouseUp => {
                    s.left_paw  = false;
                    s.right_paw = false;
                }
                _ => {}
            }
            None
        },
    );

    match tap {
        Ok(tap) => {
            let loop_source = tap.mach_port.create_runloop_source(0).unwrap();
            let run_loop = CFRunLoop::get_current();
            run_loop.add_source(&loop_source, unsafe { kCFRunLoopCommonModes });
            tap.enable();
            CFRunLoop::run_current();
        }
        Err(_) => {
            eprintln!("Could not create CGEventTap — grant Accessibility + Input Monitoring in System Settings > Privacy & Security");
        }
    }
}