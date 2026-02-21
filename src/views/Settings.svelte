<script lang="ts">
	import {
		nsfwMode,
		contentMode,
		theme,
		watchFolders,
		libraryFolders,
		apiKeys,
		apiEnabled,
		defaultAction,
		conflictResolution,
		faceDetectionEnabled,
		faceConfidenceThreshold,
		peopleFolderPath,
		loadSettings,
		saveSettings
	} from '../lib/stores/settings';
	import { openFolderDialog, ipcCall } from '../lib/utils/ipc';
	import ToggleSwitch from '../lib/components/ToggleSwitch.svelte';

	let showToast = $state(false);
	let toastMessage = $state('');
	let toastType = $state<'success' | 'error' | 'info'>('success');

	function showNotification(message: string, type: 'success' | 'error' | 'info') {
		toastMessage = message;
		toastType = type;
		showToast = true;
		setTimeout(() => {
			showToast = false;
		}, 3000);
	}

	async function handleNsfwToggle(checked: boolean) {
		$nsfwMode = checked;
		if (!checked) {
			$contentMode = 'film';
		}
		try {
			await saveSettings('nsfw_mode', checked);
			showNotification('Settings saved', 'success');
		} catch (err) {
			showNotification('Failed to save settings', 'error');
		}
	}

	async function addLibraryFolder() {
		const path = await openFolderDialog();
		if (path && !$libraryFolders.includes(path)) {
			$libraryFolders = [...$libraryFolders, path];
			try {
				await saveSettings('library_folders', $libraryFolders);
				showNotification('Library folder added', 'success');
			} catch (err) {
				showNotification('Failed to add folder', 'error');
			}
		}
	}

	async function removeLibraryFolder(path: string) {
		$libraryFolders = $libraryFolders.filter(f => f !== path);
		try {
			await saveSettings('library_folders', $libraryFolders);
			showNotification('Library folder removed', 'success');
		} catch (err) {
			showNotification('Failed to remove folder', 'error');
		}
	}

	async function addWatchFolder() {
		const path = await openFolderDialog();
		if (path && !$watchFolders.includes(path)) {
			$watchFolders = [...$watchFolders, path];
			try {
				await saveSettings('watch_folders', $watchFolders);
				showNotification('Watch folder added', 'success');
			} catch (err) {
				showNotification('Failed to add folder', 'error');
			}
		}
	}

	async function removeWatchFolder(path: string) {
		$watchFolders = $watchFolders.filter(f => f !== path);
		try {
			await saveSettings('watch_folders', $watchFolders);
			showNotification('Watch folder removed', 'success');
		} catch (err) {
			showNotification('Failed to remove folder', 'error');
		}
	}

	async function updateApiKey(api: string, key: string) {
		const updatedKeys = { ...$apiKeys, [api]: key };
		$apiKeys = updatedKeys;
		try {
			await saveSettings('api_keys', updatedKeys);
			showNotification('API key saved', 'success');
		} catch (err) {
			showNotification('Failed to save API key', 'error');
		}
	}

	async function updateApiEnabled(api: string, enabled: boolean) {
		const updatedEnabled = { ...$apiEnabled, [api]: enabled };
		$apiEnabled = updatedEnabled;
		try {
			await saveSettings('api_enabled', updatedEnabled);
			showNotification('API setting updated', 'success');
		} catch (err) {
			showNotification('Failed to update API setting', 'error');
		}
	}

	async function updateDefaultAction(action: string) {
		$defaultAction = action;
		try {
			await saveSettings('default_action', action);
			showNotification('Setting saved', 'success');
		} catch (err) {
			showNotification('Failed to save setting', 'error');
		}
	}

	async function updateConflictResolution(resolution: string) {
		$conflictResolution = resolution;
		try {
			await saveSettings('conflict_resolution', resolution);
			showNotification('Setting saved', 'success');
		} catch (err) {
			showNotification('Failed to save setting', 'error');
		}
	}

	async function updateFaceDetection(enabled: boolean) {
		$faceDetectionEnabled = enabled;
		try {
			await saveSettings('face_detection_enabled', enabled);
			showNotification('Setting saved', 'success');
		} catch (err) {
			showNotification('Failed to save setting', 'error');
		}
	}

	async function updateFaceThreshold(threshold: number) {
		$faceConfidenceThreshold = threshold;
		try {
			await saveSettings('face_confidence_threshold', threshold);
		} catch (err) {
			console.error('Failed to save threshold:', err);
		}
	}

	async function updatePeoplePath(path: string) {
		$peopleFolderPath = path;
		try {
			await saveSettings('people_folder_path', path);
			showNotification('Path updated', 'success');
		} catch (err) {
			showNotification('Failed to update path', 'error');
		}
	}

	$effect.pre(async () => {
		await loadSettings();
	});
</script>

<div class="h-screen overflow-y-auto bg-[#0D0D0F]" style="color: #F1F5F9;">
	<div class="max-w-4xl mx-auto px-6 py-6 space-y-8">
		<!-- NSFW Mode Section -->
		<section class="rounded-lg border-2" style="border-color: #EC4899; background: rgba(236, 72, 153, 0.1); padding: 20px;">
			<div class="flex items-start gap-3 mb-4">
				<span class="text-2xl">🔒</span>
				<div class="flex-1">
					<h2 class="text-lg font-semibold text-[#EC4899]">NSFW Mode</h2>
					<p class="text-xs text-[#A1A1B5] mt-1">Enable adult content features. When disabled, adult content is hidden.</p>
				</div>
			</div>
			<ToggleSwitch
				label="Enable Adult Content"
				checked={$nsfwMode}
				onchange={handleNsfwToggle}
			/>
		</section>

		<!-- General Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold text-[#F1F5F9]">General</h2>

			<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4">
				<label class="text-sm font-medium text-[#F1F5F9] block mb-2">Theme</label>
				<select
					value={$theme}
					class="w-full px-3 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] focus:border-[#EC4899] outline-none"
				>
					<option value="dark-pink">Dark Pink</option>
				</select>
			</div>

			<div class="space-y-3">
				<label class="text-sm font-medium text-[#F1F5F9] block">Default Action</label>
				<div class="space-y-2">
					{#each ['copy', 'move'] as action}
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="radio"
								name="default-action"
								value={action}
								checked={$defaultAction === action}
								onchange={() => updateDefaultAction(action)}
								class="w-4 h-4"
							/>
							<span class="text-sm">{action.charAt(0).toUpperCase() + action.slice(1)}</span>
						</label>
					{/each}
				</div>
			</div>

			<div class="space-y-3">
				<label class="text-sm font-medium text-[#F1F5F9] block">Conflict Resolution</label>
				<div class="space-y-2">
					{#each ['rename_increment', 'skip', 'overwrite'] as resolution}
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="radio"
								name="conflict-resolution"
								value={resolution}
								checked={$conflictResolution === resolution}
								onchange={() => updateConflictResolution(resolution)}
								class="w-4 h-4"
							/>
							<span class="text-sm">{resolution.replace(/_/g, ' ').toUpperCase()}</span>
						</label>
					{/each}
				</div>
			</div>
		</section>

		<!-- Library Folders Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold text-[#F1F5F9]">Library Folders</h2>
			<div class="space-y-2">
				{#each $libraryFolders as folder (folder)}
					<div class="flex items-center justify-between bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-3">
						<span class="text-sm truncate">{folder}</span>
						<button
							class="text-xs px-3 py-1 rounded bg-red-500 bg-opacity-20 text-red-400 hover:bg-opacity-30"
							onclick={() => removeLibraryFolder(folder)}
						>
							Remove
						</button>
					</div>
				{/each}
			</div>
			<button
				class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
				style="background: linear-gradient(135deg, #EC4899, #D946EF);"
				onclick={addLibraryFolder}
			>
				Add Library Folder
			</button>
		</section>

		<!-- Watch Folders Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold text-[#F1F5F9]">Watch Folders</h2>
			<div class="space-y-2">
				{#each $watchFolders as folder (folder)}
					<div class="flex items-center justify-between bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-3">
						<span class="text-sm truncate">{folder}</span>
						<button
							class="text-xs px-3 py-1 rounded bg-red-500 bg-opacity-20 text-red-400 hover:bg-opacity-30"
							onclick={() => removeWatchFolder(folder)}
						>
							Remove
						</button>
					</div>
				{/each}
			</div>
			<button
				class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
				style="background: linear-gradient(135deg, #EC4899, #D946EF);"
				onclick={addWatchFolder}
			>
				Add Watch Folder
			</button>
		</section>

		<!-- API Configuration Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold text-[#F1F5F9]">API Configuration</h2>

			{#each ['tmdb', 'omdb', 'acoustid', 'musicbrainz', 'stashdb'] as api}
				{#if api !== 'stashdb' || $nsfwMode}
					<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4 space-y-3">
						<div class="flex items-center justify-between">
							<label class="text-sm font-medium text-[#F1F5F9]">{api.toUpperCase()}</label>
							<label class="flex items-center gap-2 cursor-pointer">
								<input
									type="checkbox"
									checked={$apiEnabled[api] || false}
									onchange={(e) => updateApiEnabled(api, e.currentTarget.checked)}
									class="w-4 h-4"
								/>
								<span class="text-xs text-[#A1A1B5]">Enabled</span>
							</label>
						</div>
						<input
							type="password"
							placeholder={`${api.toUpperCase()} API Key`}
							value={$apiKeys[api] || ''}
							onchange={(e) => updateApiKey(api, e.currentTarget.value)}
							class="w-full px-3 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none text-sm"
						/>
					</div>
				{/if}
			{/each}
		</section>

		<!-- Face Detection Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold text-[#F1F5F9]">Face Detection</h2>

			<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4">
				<ToggleSwitch
					label="Enable Face Detection"
					checked={$faceDetectionEnabled}
					onchange={updateFaceDetection}
				/>
			</div>

			{#if $faceDetectionEnabled}
				<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4 space-y-3">
					<div>
						<label class="text-sm font-medium text-[#F1F5F9] block mb-2">
							Confidence Threshold: {$faceConfidenceThreshold.toFixed(2)}
						</label>
						<input
							type="range"
							min="0.4"
							max="0.8"
							step="0.05"
							value={$faceConfidenceThreshold}
							onchange={(e) => updateFaceThreshold(parseFloat(e.currentTarget.value))}
							class="w-full"
						/>
					</div>
				</div>

				<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4">
					<label class="text-sm font-medium text-[#F1F5F9] block mb-2">People Folder</label>
					<input
						type="text"
						placeholder="Path to people folder..."
						value={$peopleFolderPath}
						onchange={(e) => updatePeoplePath(e.currentTarget.value)}
						class="w-full px-3 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none mb-3"
					/>
					<button
						class="px-4 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
						onclick={() => {}}
					>
						Browse Folder
					</button>
				</div>
			{/if}
		</section>

		<!-- About Section -->
		<section class="space-y-4">
			<h2 class="text-lg font-semibold text-[#F1F5F9]">About</h2>
			<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4 space-y-2 text-sm">
				<div>
					<span class="text-[#A1A1B5]">MediaForge</span>
					<span class="text-[#F1F5F9] ml-2">v1.0.0</span>
				</div>
				<div>
					<span class="text-[#A1A1B5]">Built with</span>
					<span class="text-[#F1F5F9] ml-2">Tauri v2 + Svelte 5 + Tailwind CSS</span>
				</div>
				<div class="text-[#A1A1B5]">
					🎨 Dark theme with pink/magenta accents
				</div>
			</div>
		</section>
	</div>

	<!-- Toast Notification -->
	{#if showToast}
		<div
			class="fixed bottom-6 right-6 px-4 py-3 rounded-lg text-sm font-medium transition-all"
			style={toastType === 'success'
				? 'background: rgba(16, 185, 129, 0.2); border: 1px solid #10B981; color: #10B981;'
				: toastType === 'error'
					? 'background: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #EF4444;'
					: 'background: rgba(59, 130, 246, 0.2); border: 1px solid #3B82F6; color: #3B82F6;'}
		>
			{toastMessage}
		</div>
	{/if}
</div>

<style>
	div::-webkit-scrollbar {
		width: 8px;
	}

	div::-webkit-scrollbar-track {
		background: transparent;
	}

	div::-webkit-scrollbar-thumb {
		background: #2A2A3E;
		border-radius: 4px;
	}

	div::-webkit-scrollbar-thumb:hover {
		background: #3A3A4E;
	}
</style>
