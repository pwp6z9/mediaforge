use std::sync::{Arc, Mutex};
use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio};
use tauri::{AppHandle, Manager, Emitter};
use serde_json::{json, Value};
use std::collections::HashMap;
use log::{info, error, warn, debug};

pub struct SidecarState {
    pub stdin: Arc<Mutex<std::process::ChildStdin>>,
    pub pending: Arc<Mutex<HashMap<String, tokio::sync::oneshot::Sender<Value>>>>,
}

pub fn start_sidecar(app: AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    info!("Starting sidecar process...");

    let sidecar_path = if cfg!(debug_assertions) {
        let project_root = std::env::current_dir()?;
        let path = project_root.join("sidecar").join("main.py");
        info!("Dev mode: sidecar script at {}", path.display());
        if !path.exists() {
            error!("Sidecar script not found: {}", path.display());
            return Err(format!("Sidecar script not found: {}", path.display()).into());
        }
        path.to_string_lossy().to_string()
    } else {
        let resource_dir = app.path().resource_dir()
            .map_err(|e| format!("Failed to get resource dir: {}", e))?;
        let binary_name = if cfg!(target_os = "windows") {
            "sidecar.exe"
        } else {
            "sidecar"
        };
        let path = resource_dir.join("binaries").join(binary_name);
        info!("Production mode: sidecar binary at {}", path.display());
        if !path.exists() {
            error!("Sidecar binary not found: {}", path.display());
            if let Ok(entries) = std::fs::read_dir(&resource_dir) {
                for entry in entries.flatten() {
                    error!("  resource: {}", entry.path().display());
                }
            }
            return Err(format!("Sidecar binary not found: {}", path.display()).into());
        }
        path.to_string_lossy().to_string()
    };

    info!("Spawning sidecar process...");

    let mut child = if cfg!(debug_assertions) {
        let python_check = Command::new("python3").arg("--version").output();
        match python_check {
            Ok(output) => info!("Python version: {}", String::from_utf8_lossy(&output.stdout).trim()),
            Err(_) => {
                warn!("python3 not found, trying 'python'...");
                match Command::new("python").arg("--version").output() {
                    Ok(output) => info!("Python (fallback): {}", String::from_utf8_lossy(&output.stdout).trim()),
                    Err(e2) => {
                        error!("Neither python3 nor python found: {}", e2);
                        return Err("Python not found. Install Python 3.11+.".into());
                    }
                }
            }
        }
        Command::new("python3")
            .arg(&sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .or_else(|_| {
                warn!("python3 spawn failed, trying 'python'...");
                Command::new("python")
                    .arg(&sidecar_path)
                    .stdin(Stdio::piped())
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped())
                    .spawn()
            })?
    } else {
        Command::new(&sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?
    };

    info!("Sidecar process spawned (PID: {:?})", child.id());

    let stdin = child.stdin.take().ok_or("Failed to open sidecar stdin")?;
    let stdout = child.stdout.take().ok_or("Failed to open sidecar stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to open sidecar stderr")?;

    let stdin = Arc::new(Mutex::new(stdin));
    let pending: Arc<Mutex<HashMap<String, tokio::sync::oneshot::Sender<Value>>>> =
        Arc::new(Mutex::new(HashMap::new()));

    let state = SidecarState {
        stdin: stdin.clone(),
        pending: pending.clone(),
    };

    app.manage(state);

    // Spawn thread to read stdout (JSON-RPC responses)
    let app_handle = app.clone();
    let pending_clone = pending.clone();
    std::thread::spawn(move || {
        info!("Sidecar stdout reader thread started");
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    debug!("Sidecar stdout: {}", &line[..line.len().min(200)]);
                    match serde_json::from_str::<Value>(&line) {
                        Ok(value) => {
                            if let Some(event_type) = value.get("event").and_then(|e| e.as_str()) {
                                let data = value.get("data").cloned().unwrap_or(Value::Null);
                                debug!("Sidecar event: {}", event_type);
                                let _ = app_handle.emit(event_type, data);
                            } else if let Some(id) = value.get("id").and_then(|i| i.as_str()) {
                                let mut pending = pending_clone.lock().unwrap();
                                if let Some(sender) = pending.remove(id) {
                                    let _ = sender.send(value);
                                } else {
                                    warn!("No pending request for id: {}", id);
                                }
                            }
                        }
                        Err(e) => {
                            warn!("Sidecar non-JSON: {} (err: {})", &line[..line.len().min(100)], e);
                        }
                    }
                }
                Err(e) => {
                    error!("Sidecar stdout read error: {}", e);
                    break;
                }
            }
        }
        warn!("Sidecar stdout reader exited (sidecar may have crashed)");
    });

    // Spawn thread to read stderr (logging/errors)
    std::thread::spawn(move || {
        info!("Sidecar stderr reader thread started");
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    if line.contains("ERROR") || line.contains("Error") {
                        error!("[sidecar] {}", line);
                    } else if line.contains("WARNING") || line.contains("Warning") {
                        warn!("[sidecar] {}", line);
                    } else {
                        info!("[sidecar] {}", line);
                    }
                }
                Err(e) => {
                    error!("Sidecar stderr read error: {}", e);
                    break;
                }
            }
        }
        warn!("Sidecar stderr reader thread exited");
    });

    info!("Sidecar setup complete, all reader threads running");
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
        let mut stdin = state.stdin.lock().map_err(|e| {
            error!("Failed to lock sidecar stdin: {}", e);
            e.to_string()
        })?;
        let line = serde_json::to_string(&request).map_err(|e| {
            error!("Failed to serialize request: {}", e);
            e.to_string()
        })? + "\n";
        stdin.write_all(line.as_bytes()).map_err(|e| {
            error!("Failed to write to sidecar stdin: {}", e);
            e.to_string()
        })?;
        stdin.flush().map_err(|e| {
            error!("Failed to flush sidecar stdin: {}", e);
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
