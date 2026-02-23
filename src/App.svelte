<script lang="ts">
	import { onMount } from 'svelte';
	import { listen } from '@tauri-apps/api/event';
	import { ipcCall } from './lib/utils/ipc';
	import { loadSettings } from './lib/stores/settings';
	import { activityLog } from './lib/stores/sentry';
	import Sidebar from './lib/components/Sidebar.svelte';
	import Forge from './views/Forge.svelte';
	import Vault from './views/Vault.svelte';
	import Sentry from './views/Sentry.svelte';
	import Settings from './views/Settings.svelte';

	let activeView = $state<string>('vault');
	let isHealthy = $state(false);
	let showToast = $state(false);
	let toastMessage = $state('');
	let toastType = $state<'success' | 'error' | 'info'>('info');

	let connectionAttempt = $state(0);
	let connectionError = $state('');
	let maxRetries = 5;

	async function checkBackend() {
		for (let i = 1; i <= maxRetries; i++) {
			connectionAttempt = i;
			try {
				await ipcCall('ping', {});
				isHealthy = true;
				connectionError = '';
				return;
			} catch (err: any) {
				console.error(`Backend check attempt ${i}/${maxRetries} failed:`, err);
				connectionError = err?.message || String(err);
				if (i < maxRetries) {
					await new Promise(r => setTimeout(r, 1500 * i));
				}
			}
		}
		showNotification('Failed to connect to backend after ' + maxRetries + ' attempts', 'error');
	}

	onMount(async () => {
		await checkBackend();

		// Load settings
		try {
			const settings = await ipcCall('get_config', {});
			console.log('Settings loaded:', settings);
		} catch (err) {
			console.error('Failed to load settings:', err);
		}

		// Listen for sentry events
		const unlistenSentry = await listen('sentry_log', (event: any) => {
			const log = event.payload;
			$activityLog = [log, ...$activityLog].slice(0, 50); // Keep last 50
		});

		// Listen for view change events
		const handleViewChange = (event: CustomEvent) => {
			activeView = event.detail.view;
		};

		window.addEventListener('viewChange', handleViewChange);

		return () => {
			unlistenSentry();
			window.removeEventListener('viewChange', handleViewChange);
		};
	});

	function showNotification(message: string, type: 'success' | 'error' | 'info') {
		toastMessage = message;
		toastType = type;
		showToast = true;
		setTimeout(() => {
			showToast = false;
		}, 3000);
	}
</script>

<div class="flex h-screen w-screen overflow-hidden bg-[#0D0D0F]">
	{#if isHealthy}
		<Sidebar {activeView} />

		<div class="flex-1 overflow-hidden">
			{#if activeView === 'forge'}
				<Forge />
			{:else if activeView === 'vault'}
				<Vault />
			{:else if activeView === 'sentry'}
				<Sentry />
			{:else if activeView === 'settings'}
				<Settings />
			{/if}
		</div>
	{:else}
		<div class="flex-1 flex items-center justify-center">
			<div class="text-center max-w-md">
				{#if connectionAttempt > 0 && connectionAttempt <= maxRetries && !connectionError}
					<div class="text-4xl mb-4 animate-pulse">⏳</div>
					<p class="text-[#F1F5F9] text-lg mb-2">Connecting to backend...</p>
					<p class="text-[#A1A1B5] text-sm">Attempt {connectionAttempt} of {maxRetries}</p>
				{:else}
					<div class="text-4xl mb-4">❌</div>
					<p class="text-[#F1F5F9] text-lg mb-2">Backend Connection Failed</p>
					{#if connectionError}
						<div class="bg-[#1A1A2E] rounded-lg p-3 mb-4 text-left">
							<p class="text-[#EF4444] text-xs font-mono break-all">{connectionError}</p>
						</div>
					{/if}
					<button
						onclick={() => { isHealthy = false; connectionError = ''; checkBackend(); }}
						class="px-4 py-2 rounded-lg text-sm font-medium"
						style="background: linear-gradient(135deg, #EC4899, #D946EF); color: white;"
					>
						Retry Connection
					</button>
					<p class="text-[#A1A1B5] text-xs mt-4">Check ~/.mediaforge/logs/ for detailed diagnostics</p>
				{/if}
			</div>
		</div>
	{/if}

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
	:global(:root) {
		--bg-primary: #0D0D0F;
		--bg-secondary: #1A1A2E;
		--bg-tertiary: #2A2A3E;
		--primary-gradient: linear-gradient(135deg, #EC4899, #D946EF);
		--pink-500: #EC4899;
		--magenta-500: #D946EF;
		--rose-400: #FB7185;
		--text-primary: #F1F5F9;
		--text-secondary: #A1A1B5;
	}

	:global(*) {
		box-sizing: border-box;
	}

	:global(body) {
		background: var(--bg-primary);
		color: var(--text-primary);
		font-family: system-ui, -apple-system, sans-serif;
		margin: 0;
		padding: 0;
		overflow: hidden;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
		height: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: var(--bg-secondary);
	}

	:global(::-webkit-scrollbar-thumb) {
		background: var(--bg-tertiary);
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: #3A3A4E;
	}
</style>
