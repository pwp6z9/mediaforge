use tauri::{AppHandle, State, Manager};
use serde_json::Value;
use crate::sidecar::{SidecarState, call_sidecar};

#[tauri::command]
pub async fn ipc_call(
    app: AppHandle,
    method: String,
    params: Value,
) -> Result<Value, String> {
    let state = app.state::<SidecarState>();
    call_sidecar(&state, &method, params).await
}

#[tauri::command]
pub async fn open_file_dialog(app: AppHandle) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;
    let path = app
        .dialog()
        .file()
        .add_filter(
            "Media Files",
            &[
                "mkv", "mp4", "avi", "mov", "webm", "mp3", "flac", "m4a", "ogg", "jpg",
                "jpeg", "png", "tiff", "webp", "zip", "rar", "7z", "gz", "tar",
            ],
        )
        .blocking_pick_file();
    Ok(path.map(|p| p.to_string_lossy().to_string()))
}

#[tauri::command]
pub async fn open_folder_dialog(app: AppHandle) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;
    let path = app
        .dialog()
        .file()
        .blocking_pick_folder();
    Ok(path.map(|p| p.to_string_lossy().to_string()))
}

#[tauri::command]
pub async fn open_in_default(app: AppHandle, path: String) -> Result<(), String> {
    use tauri_plugin_shell::ShellExt;
    app.shell()
        .open(&path, None)
        .map_err(|e| format!("Failed to open path: {}", e))?;
    Ok(())
}
