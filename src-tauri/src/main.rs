#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod sidecar;
mod tray;

use log::{info, error};
#[allow(unused_imports)]
use tauri::Manager;
use std::fs;
use std::io::Write;

/// Initialize file-based logging to ~/.mediaforge/logs/
fn init_logging() {
    let log_dir = dirs::home_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join(".mediaforge")
        .join("logs");

    fs::create_dir_all(&log_dir).ok();

    let timestamp = chrono::Local::now().format("%Y-%m-%d_%H-%M-%S");
    let log_file_path = log_dir.join(format!("mediaforge_{}.log", timestamp));
    let latest_path = log_dir.join("latest.log");

    let log_file = fs::File::create(&log_file_path).ok();
    let latest_file = fs::File::create(&latest_path).ok();

    env_logger::Builder::from_default_env()
        .filter_level(log::LevelFilter::Info)
        .format(move |buf, record| {
            let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S%.3f");
            let msg = format!(
                "[{} {} {}] {}\n",
                ts,
                record.level(),
                record.target(),
                record.args()
            );
            let _ = write!(buf, "{}", msg);
            if let Some(ref f) = log_file {
                let _ = (&*f).write_all(msg.as_bytes());
            }
            if let Some(ref f) = latest_file {
                let _ = (&*f).write_all(msg.as_bytes());
            }
            Ok(())
        })
        .init();

    info!("=== MediaForge v0.1.0 starting ===");
    info!("Log file: {}", log_file_path.display());
    info!("Platform: {} {}", std::env::consts::OS, std::env::consts::ARCH);
}

fn main() {
    init_logging();
    info!("Initializing Tauri application...");

    let result = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            commands::ipc_call,
            commands::open_file_dialog,
            commands::open_folder_dialog,
            commands::open_in_default,
        ])
        .setup(|app| {
            info!("Running Tauri setup...");
            match tray::setup_tray(app) {
                Ok(_) => info!("System tray initialized successfully"),
                Err(e) => {
                    error!("System tray setup failed: {}. Continuing without tray.", e);
                }
            }
            let handle = app.handle().clone();
            match sidecar::start_sidecar(handle) {
                Ok(_) => info!("Python sidecar launched successfully"),
                Err(e) => {
                    error!("FATAL: Sidecar launch failed: {}", e);
                    error!("Check that Python 3 is installed and the sidecar binary exists.");
                    return Err(Box::new(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        format!("Sidecar launch failed: {}", e),
                    )));
                }
            }
            info!("Tauri setup completed successfully");
            Ok(())
        })
        .run(tauri::generate_context!());

    match result {
        Ok(_) => info!("MediaForge exited normally"),
        Err(e) => {
            error!("MediaForge crashed: {}", e);
            let crash_path = dirs::home_dir()
                .unwrap_or_else(|| std::path::PathBuf::from("."))
                .join(".mediaforge")
                .join("logs")
                .join("crash.log");
            if let Ok(mut f) = fs::File::create(&crash_path) {
                let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
                let _ = writeln!(f, "[{}] CRASH: {}", ts, e);
                let _ = writeln!(f, "Platform: {} {}", std::env::consts::OS, std::env::consts::ARCH);
            }
            eprintln!("MediaForge crashed: {}. Check ~/.mediaforge/logs/ for details.", e);
            std::process::exit(1);
        }
    }
}
