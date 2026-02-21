use std::sync::{Arc, Mutex};
use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio};
use tauri::{AppHandle, Manager, Emitter};
use serde_json::{json, Value};
use std::collections::HashMap;

pub struct SidecarState {
    pub stdin: Arc<Mutex<std::process::ChildStdin>>,
    pub pending: Arc<Mutex<HashMap<String, tokio::sync::oneshot::Sender<Value>>>>,
}

pub fn start_sidecar(app: AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let sidecar_path = if cfg!(debug_assertions) {
        // Dev mode: use python3 with sidecar/main.py
        let project_root = std::env::current_dir().unwrap();
        let path = project_root.join("sidecar/main.py");
        path.to_string_lossy().to_string()
    } else {
        // Production: use bundled sidecar binary
        let resource_dir = app.path().resource_dir().unwrap();
        let path = resource_dir.join("binaries/sidecar");
        path.to_string_lossy().to_string()
    };

    let mut child = if cfg!(debug_assertions) {
        Command::new("python3")
            .arg(&sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()?
    } else {
        Command::new(&sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()?
    };

    let stdin = child.stdin.take().ok_or("Failed to open stdin")?;
    let stdout = child.stdout.take().ok_or("Failed to open stdout")?;

    let stdin = Arc::new(Mutex::new(stdin));
    let pending: Arc<Mutex<HashMap<String, tokio::sync::oneshot::Sender<Value>>>> =
        Arc::new(Mutex::new(HashMap::new()));

    let state = SidecarState {
        stdin: stdin.clone(),
        pending: pending.clone(),
    };

    app.manage(state);

    // Spawn thread to read stdout from sidecar
    let app_handle = app.clone();
    let pending_clone = pending.clone();
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line) = line {
                if let Ok(value) = serde_json::from_str::<Value>(&line) {
                    // Check if it's an event or a response
                    if let Some(event_type) = value.get("event").and_then(|e| e.as_str()) {
                        // Emit Tauri event
                        let data = value.get("data").cloned().unwrap_or(Value::Null);
                        let _ = app_handle.emit(event_type, data);
                    } else if let Some(id) = value.get("id").and_then(|i| i.as_str()) {
                        // Route to pending request
                        let mut pending = pending_clone.lock().unwrap();
                        if let Some(sender) = pending.remove(id) {
                            let _ = sender.send(value);
                        }
                    }
                }
            }
        }
    });

    Ok(())
}

pub async fn call_sidecar(
    state: &SidecarState,
    method: &str,
    params: serde_json::Value,
) -> Result<serde_json::Value, String> {
    let id = uuid::Uuid::new_v4().to_string();

    let request = json!({
        "id": id,
        "method": method,
        "params": params,
    });

    let (tx, rx) = tokio::sync::oneshot::channel::<serde_json::Value>();

    {
        let mut pending = state.pending.lock().map_err(|e| e.to_string())?;
        pending.insert(id.clone(), tx);
    }

    {
        let mut stdin = state.stdin.lock().map_err(|e| e.to_string())?;
        let line = serde_json::to_string(&request).map_err(|e| e.to_string())? + "\n";
        stdin.write_all(line.as_bytes()).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;
    }

    let response = rx.await.map_err(|e| e.to_string())?;

    if let Some(error) = response.get("error").filter(|e| !e.is_null()) {
        return Err(error.to_string());
    }

    Ok(response
        .get("result")
        .cloned()
        .unwrap_or(serde_json::Value::Null))
}
