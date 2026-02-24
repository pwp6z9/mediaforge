use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Manager, Emitter};
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use serde_json::{json, Value};
use std::collections::HashMap;
use log::{info, error, warn, debug};

pub struct SidecarState {
    pub child: Arc<Mutex<CommandChild>>,
    pub pending: Arc<Mutex<HashMap<String, tokio::sync::oneshot::Sender<Value>>>>,
}

pub fn start_sidecar(app: AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    info!("Starting sidecar process via Tauri shell API...");

    let sidecar_command = app.shell().sidecar("sidecar")
        .map_err(|e| {
            error!("Failed to create sidecar command: {}", e);
            error!("Ensure 'binaries/sidecar' is in externalBin config and binary exists");
            format!("Sidecar command creation failed: {}", e)
        })?;

    info!("Sidecar command created, spawning...");

    let (mut rx, child) = sidecar_command.spawn()
        .map_err(|e| {
            error!("Failed to spawn sidecar: {}", e);
            error!("Check that sidecar binary exists with correct target-triple suffix");
            format!("Sidecar spawn failed: {}", e)
        })?;

    info!("Sidecar process spawned successfully");

    let child = Arc::new(Mutex::new(child));
    let pending: Arc<Mutex<HashMap<String, tokio::sync::oneshot::Sender<Value>>>> =
        Arc::new(Mutex::new(HashMap::new()));

    let state = SidecarState {
        child: child.clone(),
        pending: pending.clone(),
    };

    app.manage(state);

    // Spawn async task to handle stdout/stderr events from sidecar
    let app_handle = app.clone();
    let pending_clone = pending.clone();

    tauri::async_runtime::spawn(async move {
        info!("Sidecar event listener started");
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    let line = line.trim();
                    if line.is_empty() {
                        continue;
                    }
                    debug!("Sidecar stdout: {}", &line[..line.len().min(200)]);

                    match serde_json::from_str::<Value>(line) {
                        Ok(value) => {
                            // Check if it's an event emission
                            if let Some(event_type) = value.get("event").and_then(|e| e.as_str()) {
                                let data = value.get("data").cloned().unwrap_or(Value::Null);
                                debug!("Sidecar event: {}", event_type);
                                let _ = app_handle.emit(event_type, data);
                            }
                            // Check if it's a response to a pending request
                            else if let Some(id) = value.get("id").and_then(|i| i.as_str()) {
                                let mut pending = pending_clone.lock().unwrap();
                                if let Some(sender) = pending.remove(id) {
                                    let _ = sender.send(value);
                                } else {
                                    warn!("No pending request for id: {}", id);
                                }
                            }
                        }
                        Err(e) => {
                            warn!("Sidecar non-JSON output: {} (err: {})", &line[..line.len().min(100)], e);
                        }
                    }
                }
                CommandEvent::Stderr(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    let line = line.trim();
                    if line.is_empty() {
                        continue;
                    }
                    if line.contains("ERROR") || line.contains("Error") {
                        error!("[sidecar] {}", line);
                    } else if line.contains("WARNING") || line.contains("Warning") {
                        warn!("[sidecar] {}", line);
                    } else {
                        info!("[sidecar] {}", line);
                    }
                }
                CommandEvent::Error(err) => {
                    error!("Sidecar process error: {}", err);
                }
                CommandEvent::Terminated(status) => {
                    warn!("Sidecar process terminated with status: {:?}", status);
                    break;
                }
                _ => {}
            }
        }
        warn!("Sidecar event listener exited (sidecar may have stopped)");
    });

    info!("Sidecar setup complete, event listener running");
    Ok(())
}

pub async fn call_sidecar(
    state: &SidecarState,
    method: &str,
    params: serde_json::Value,
) -> Result<serde_json::Value, String> {
    debug!("IPC call: {} params={}", method, &params.to_string()[..params.to_string().len().min(200)]);

    let id = uuid::Uuid::new_v4().to_string();
    let request = json!({
        "id": id,
        "method": method,
        "params": params,
    });

    let (tx, rx) = tokio::sync::oneshot::channel::<serde_json::Value>();

    {
        let mut pending = state.pending.lock().map_err(|e| {
            error!("Failed to lock pending map: {}", e);
            e.to_string()
        })?;
        pending.insert(id.clone(), tx);
    }

    {
        let mut child = state.child.lock().map_err(|e| {
            error!("Failed to lock sidecar child: {}", e);
            e.to_string()
        })?;
        let line = serde_json::to_string(&request).map_err(|e| {
            error!("Failed to serialize request: {}", e);
            e.to_string()
        })? + "\n";
        child.write(line.as_bytes()).map_err(|e| {
            error!("Failed to write to sidecar stdin: {}", e);
            e.to_string()
        })?;
    }

    let response = rx.await.map_err(|e| {
        error!("Sidecar response channel closed for '{}': {}", method, e);
        format!("Sidecar communication failed for '{}': {}", method, e)
    })?;

    if let Some(err) = response.get("error").filter(|e| !e.is_null()) {
        warn!("Sidecar returned error for '{}': {}", method, err);
        return Err(err.to_string());
    }

    debug!("IPC call '{}' succeeded", method);
    Ok(response.get("result").cloned().unwrap_or(serde_json::Value::Null))
}
