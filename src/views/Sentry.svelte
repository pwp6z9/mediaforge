<script lang="ts">
	import { sentryActive, sentryStatus, activityLog, undoQueue } from '../lib/stores/sentry';
	import { watchFolders } from '../lib/stores/settings';
	import { faceDbStats } from '../lib/stores/faces';
	import { ipcCall, openFolderDialog } from '../lib/utils/ipc';
	import { formatDate } from '../lib/utils/formatters';

	let isStarting = $state(false);
	let isStopping = $state(false);
	let showRuleEditor = $state(false);
	let newRuleName = $state('');
	let rules = $state<Array<{ name: string; conditions: string[]; actions: string[] }>>([]);
	let statusRefreshInterval: any;

	async function toggleSentry() {
		if ($sentryActive) {
			isStopping = true;
			try {
				await ipcCall('stop_sentry', {});
				$sentryActive = false;
				if (statusRefreshInterval) clearInterval(statusRefreshInterval);
			} catch (err) {
				console.error('Failed to stop sentry:', err);
			} finally {
				isStopping = false;
			}
		} else {
			isStarting = true;
			try {
				await ipcCall('start_sentry', {});
				$sentryActive = true;
				// Auto-refresh status
				statusRefreshInterval = setInterval(refreshStatus, 5000);
				refreshStatus();
			} catch (err) {
				console.error('Failed to start sentry:', err);
			} finally {
				isStarting = false;
			}
		}
	}

	async function refreshStatus() {
		try {
			const status = await ipcCall('sentry_status', {});
			$sentryStatus = status;
		} catch (err) {
			console.error('Failed to refresh sentry status:', err);
		}
	}

	async function addWatchFolder() {
		const path = await openFolderDialog();
		if (path && !$watchFolders.includes(path)) {
			$watchFolders = [...$watchFolders, path];
		}
	}

	function removeWatchFolder(path: string) {
		$watchFolders = $watchFolders.filter(f => f !== path);
	}

	function addRule() {
		if (newRuleName) {
			rules = [...rules, { name: newRuleName, conditions: [], actions: [] }];
			newRuleName = '';
			showRuleEditor = false;
		}
	}

	function removeRule(index: number) {
		rules = rules.filter((_, i) => i !== index);
	}

	async function undoLastAction() {
		try {
			await ipcCall('undo_last', {});
			// Refresh activity log
			await refreshStatus();
		} catch (err) {
			console.error('Undo failed:', err);
		}
	}

	async function rebuildFaceDb() {
		try {
			const result = await ipcCall('ipc_call', { method: 'rebuild_face_db', params: {} });
			$faceDbStats = result;
		} catch (err) {
			console.error('Face DB rebuild failed:', err);
		}
	}

	$effect.pre(async () => {
		if ($sentryActive) {
			refreshStatus();
			statusRefreshInterval = setInterval(refreshStatus, 5000);
		}

		return () => {
			if (statusRefreshInterval) clearInterval(statusRefreshInterval);
		};
	});
</script>

<div class="h-screen flex flex-col bg-[#0D0D0F]" style="color: #F1F5F9;">
	<!-- Status Bar -->
	<div class="flex items-center justify-between border-b border-[#2A2A3E] px-6 py-4 bg-[#1A1A2E] flex-shrink-0">
		<div class="flex items-center gap-3">
			<div
				class="w-3 h-3 rounded-full"
				style={`background: ${$sentryActive ? '#10B981' : '#6B7280'};`}
			></div>
			<span class="text-sm">
				{#if $sentryActive}
					Watching {$watchFolders.length} folder{$watchFolders.length !== 1 ? 's' : ''}
				{:else}
					Sentry inactive
				{/if}
			</span>
		</div>

		<button
			class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
			style={$sentryActive
				? 'background: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #EF4444;'
				: 'background: linear-gradient(135deg, #EC4899, #D946EF);'}
			onclick={toggleSentry}
			disabled={isStarting || isStopping}
		>
			{#if isStarting}
				Starting...
			{:else if isStopping}
				Stopping...
			{:else}
				{$sentryActive ? 'Stop' : 'Start'} Sentry
			{/if}
		</button>
	</div>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto px-6 py-6 space-y-6">
		<!-- Watch Folders Section -->
		<section>
			<h2 class="text-lg font-semibold text-[#F1F5F9] mb-4">Watch Folders</h2>
			<div class="space-y-2 mb-4">
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

		<!-- Rules Section -->
		<section>
			<h2 class="text-lg font-semibold text-[#F1F5F9] mb-4">Rules</h2>
			<div class="space-y-3 mb-4">
				{#each rules as rule, idx (rule.name)}
					<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4">
						<div class="flex items-start justify-between mb-3">
							<h3 class="font-medium text-[#EC4899]">{rule.name}</h3>
							<button
								class="text-xs px-2 py-1 rounded bg-red-500 bg-opacity-20 text-red-400 hover:bg-opacity-30"
								onclick={() => removeRule(idx)}
							>
								Delete
							</button>
						</div>
						<div class="text-xs text-[#A1A1B5] space-y-1">
							<div>Conditions: {rule.conditions.length > 0 ? rule.conditions.join(', ') : 'None'}</div>
							<div>Actions: {rule.actions.length > 0 ? rule.actions.join(', ') : 'None'}</div>
						</div>
					</div>
				{/each}
			</div>
			<button
				class="px-4 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
				onclick={() => showRuleEditor = !showRuleEditor}
			>
				Add Rule
			</button>

			{#if showRuleEditor}
				<div class="mt-4 bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4">
					<input
						type="text"
						placeholder="Rule name..."
						bind:value={newRuleName}
						class="w-full px-3 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none mb-3"
					/>
					<div class="flex gap-2">
						<button
							class="px-3 py-2 rounded-lg text-sm font-medium transition-all"
							style="background: linear-gradient(135deg, #EC4899, #D946EF);"
							onclick={addRule}
						>
							Create Rule
						</button>
						<button
							class="px-3 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E]"
							onclick={() => showRuleEditor = false}
						>
							Cancel
						</button>
					</div>
				</div>
			{/if}
		</section>

		<!-- Activity Log Section -->
		<section>
			<h2 class="text-lg font-semibold text-[#F1F5F9] mb-4">Activity Log</h2>
			<div class="space-y-2 max-h-64 overflow-y-auto">
				{#each $activityLog as log, idx (idx)}
					<div
						class="bg-[#1A1A2E] border-l-4 rounded-lg p-3 text-xs"
						style={`border-color: ${log.status === 'success' ? '#10B981' : log.status === 'error' ? '#EF4444' : '#F59E0B'};`}
					>
						<div class="flex justify-between mb-1">
							<span class="font-medium">{log.filename}</span>
							<span class="text-[#A1A1B5]">{log.timestamp}</span>
						</div>
						<div class="text-[#A1A1B5]">{log.action}</div>
						{#if log.destination}
							<div class="text-[#A1A1B5]">→ {log.destination}</div>
						{/if}
						{#if log.person}
							<div class="text-[#EC4899]">📸 {log.person}</div>
						{/if}
					</div>
				{/each}
				{#if $activityLog.length === 0}
					<div class="text-center text-[#A1A1B5] py-8">
						No activity yet
					</div>
				{/if}
			</div>
		</section>

		<!-- Undo Queue -->
		{#if $undoQueue.length > 0}
			<section>
				<h2 class="text-lg font-semibold text-[#F1F5F9] mb-4">Recent Actions</h2>
				<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4">
					<p class="text-sm text-[#A1A1B5] mb-3">{$undoQueue[0]?.description}</p>
					<button
						class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
						style="background: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #EF4444;"
						onclick={undoLastAction}
					>
						Undo Last Action
					</button>
				</div>
			</section>
		{/if}

		<!-- Face Detection Section -->
		<section>
			<h2 class="text-lg font-semibold text-[#F1F5F9] mb-4">Face Detection</h2>
			<div class="bg-[#1A1A2E] border border-[#2A2A3E] rounded-lg p-4 space-y-3">
				<div class="grid grid-cols-2 gap-4 text-sm">
					<div>
						<span class="text-[#A1A1B5]">People in DB:</span>
						<span class="text-[#F1F5F9] ml-2 font-medium">{$faceDbStats.total_people}</span>
					</div>
					<div>
						<span class="text-[#A1A1B5]">Encodings:</span>
						<span class="text-[#F1F5F9] ml-2 font-medium">{$faceDbStats.total_encodings}</span>
					</div>
				</div>
				<button
					class="w-full px-4 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
					onclick={rebuildFaceDb}
				>
					Rebuild Face DB
				</button>
			</div>
		</section>
	</div>
</div>

<style>
	div::-webkit-scrollbar {
		width: 6px;
	}

	div::-webkit-scrollbar-track {
		background: transparent;
	}

	div::-webkit-scrollbar-thumb {
		background: #2A2A3E;
		border-radius: 3px;
	}

	div::-webkit-scrollbar-thumb:hover {
		background: #3A3A4E;
	}
</style>
