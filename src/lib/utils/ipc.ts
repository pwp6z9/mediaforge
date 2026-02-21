import { invoke } from '@tauri-apps/api/core';

export async function ipcCall(method: string, params: Record<string, any> = {}): Promise<any> {
	return invoke('ipc_call', { method, params });
}

export async function openFileDialog(): Promise<string | null> {
	return invoke('open_file_dialog', {});
}

export async function openFolderDialog(): Promise<string | null> {
	return invoke('open_folder_dialog', {});
}

export async function openInDefault(path: string): Promise<void> {
	return invoke('open_in_default', { path });
}
