import { writable, derived } from 'svelte/store';
import { ipcCall } from '../utils/ipc';

export const nsfwMode = writable<boolean>(false);
export const contentMode = writable<string>('film'); // 'music' | 'film' | 'photo' | 'custom' | 'adult'
export const apiKeys = writable<Record<string, string>>({
	stashdb: '',
	tmdb: '',
	omdb: '',
	acoustid_client: ''
});
export const apiEnabled = writable<Record<string, boolean>>({
	stashdb: false,
	tmdb: false,
	omdb: false,
	musicbrainz: false,
	acoustid: false
});
export const theme = writable<string>('dark-pink');
export const watchFolders = writable<string[]>([]);
export const libraryFolders = writable<string[]>([]);
export const defaultAction = writable<string>('copy'); // 'copy' | 'move'
export const conflictResolution = writable<string>('rename_increment'); // 'rename_increment' | 'skip' | 'overwrite'
export const faceDetectionEnabled = writable<boolean>(false);
export const faceConfidenceThreshold = writable<number>(0.6);
export const peopleFolderPath = writable<string>('');

// Derived: effectiveContentMode falls back to 'film' if nsfwMode=false and contentMode='adult'
export const effectiveContentMode = derived(
	[nsfwMode, contentMode],
	([$nsfw, $mode]) => (!$nsfw && $mode === 'adult') ? 'film' : $mode
);

export async function loadSettings(): Promise<void> {
	try {
		const config = await ipcCall('get_config', {});
		if (config.nsfw_mode !== undefined) nsfwMode.set(config.nsfw_mode);
		if (config.content_mode !== undefined) contentMode.set(config.content_mode);
		if (config.api_keys !== undefined) apiKeys.set(config.api_keys);
		if (config.api_enabled !== undefined) apiEnabled.set(config.api_enabled);
		if (config.theme !== undefined) theme.set(config.theme);
		if (config.watch_folders !== undefined) watchFolders.set(config.watch_folders);
		if (config.library_folders !== undefined) libraryFolders.set(config.library_folders);
		if (config.default_action !== undefined) defaultAction.set(config.default_action);
		if (config.conflict_resolution !== undefined) conflictResolution.set(config.conflict_resolution);
		if (config.face_detection_enabled !== undefined) faceDetectionEnabled.set(config.face_detection_enabled);
		if (config.face_confidence_threshold !== undefined) faceConfidenceThreshold.set(config.face_confidence_threshold);
		if (config.people_folder_path !== undefined) peopleFolderPath.set(config.people_folder_path);
	} catch (err) {
		console.error('Failed to load settings:', err);
	}
}

export async function saveSettings(key: string, value: any): Promise<void> {
	try {
		const configKey = key.toLowerCase().replace(/([A-Z])/g, '_$1').toLowerCase();
		await ipcCall('set_config', { key: configKey, value });
	} catch (err) {
		console.error(`Failed to save setting ${key}:`, err);
	}
}
