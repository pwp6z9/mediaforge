<script lang="ts">
	import { nsfwMode } from '../lib/stores/settings';
	import { searchQuery, searchFilters, searchResults, dbStats, isIndexing, indexProgress, totalResults } from '../lib/stores/files';
	import { ipcCall, openFolderDialog, openInDefault } from '../lib/utils/ipc';
	import { formatDate, formatFileSize, formatDuration } from '../lib/utils/formatters';
	import FileItem from '../lib/components/FileItem.svelte';

	let viewMode = $state<'grid' | 'list'>('grid');
	let selectedFile = $state<any>(null);
	let query = $state('');
	let isScanning = $state(false);
	let debounceTimer: any;

	const filterOptions = {
		genre: [] as string[],
		yearMin: 1900,
		yearMax: new Date().getFullYear(),
		ratingMin: 0,
		performers: [] as string[]
	};

	let filters = $state({ ...filterOptions });

	async function performSearch() {
		try {
			const result = await ipcCall('search_files', {
				query: query || '*',
				filters,
				limit: 100,
				offset: 0
			});
			$searchResults = result.files || [];
			$totalResults = result.total || 0;
		} catch (err) {
			console.error('Search failed:', err);
		}
	}

	function handleQueryChange(q: string) {
		query = q;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(performSearch, 300);
	}

	async function handleScanLibrary() {
		const path = await openFolderDialog();
		if (path) {
			isScanning = true;
			try {
				const interval = setInterval(async () => {
					const status = await ipcCall('sentry_status', {});
					if (status.progress) {
						$indexProgress = status.progress;
					}
				}, 500);

				await ipcCall('scan_library', { path, recursive: true });

				clearInterval(interval);
				const stats = await ipcCall('get_stats', {});
				$dbStats = stats;
				performSearch();
			} catch (err) {
				console.error('Scan failed:', err);
			} finally {
				isScanning = false;
			}
		}
	}

	function selectFile(file: any) {
		selectedFile = file;
	}

	async function openInPlayer() {
		if (selectedFile?.path) {
			await openInDefault(selectedFile.path);
		}
	}

	function editInForge() {
		const event = new CustomEvent('viewChange', { detail: { view: 'forge' } });
		window.dispatchEvent(event);
	}

	$effect(() => {
		performSearch();
	});

	$effect.pre(async () => {
		const stats = await ipcCall('get_stats', {});
		$dbStats = stats;
	});
</script>

<div class="h-screen flex flex-col bg-[#0D0D0F]" style="color: #F1F5F9;">
	<!-- Top Bar -->
	<div class="flex items-center gap-4 border-b border-[#2A2A3E] px-6 py-4 bg-[#1A1A2E] flex-shrink-0">
		<input
			type="text"
			placeholder="Search library..."
			value={query}
			onchange={(e) => handleQueryChange(e.currentTarget.value)}
			class="flex-1 px-4 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
		/>
		
		<div class="flex gap-2">
			<button
				class="px-3 py-2 rounded-lg text-sm"
				style={viewMode === 'grid'
					? 'background: linear-gradient(135deg, #EC4899, #D946EF);'
					: 'background: transparent; border: 1px solid #2A2A3E;'}
				onclick={() => viewMode = 'grid'}
			>
				🔲 Grid
			</button>
			<button
				class="px-3 py-2 rounded-lg text-sm"
				style={viewMode === 'list'
					? 'background: linear-gradient(135deg, #EC4899, #D946EF);'
					: 'background: transparent; border: 1px solid #2A2A3E;'}
				onclick={() => viewMode = 'list'}
			>
				☰ List
			</button>
		</div>

		<button
			class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
			style="background: linear-gradient(135deg, #EC4899, #D946EF);"
			onclick={handleScanLibrary}
		>
			Scan Library
		</button>
	</div>

	<!-- Main Content -->
	<div class="flex-1 flex gap-4 p-6 overflow-hidden">
		<!-- Left Filter Panel -->
		<div class="w-64 flex flex-col gap-4 overflow-y-auto bg-[#1A1A2E] rounded-lg p-4 border border-[#2A2A3E]">
			<h3 class="text-sm font-semibold text-[#EC4899]">Filters</h3>
			
			<div>
				<label class="text-xs text-[#A1A1B5] block mb-2">Genre</label>
				<input
					type="text"
					placeholder="Filter by genre..."
					class="w-full px-3 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none text-sm"
				/>
			</div>

			<div>
				<label class="text-xs text-[#A1A1B5] block mb-2">
					Year: {filters.yearMin} - {filters.yearMax}
				</label>
				<input
					type="range"
					min="1900"
					max={new Date().getFullYear()}
					bind:value={filters.yearMin}
					class="w-full"
				/>
				<input
					type="range"
					min="1900"
					max={new Date().getFullYear()}
					bind:value={filters.yearMax}
					class="w-full mt-2"
				/>
			</div>

			<div>
				<label class="text-xs text-[#A1A1B5] block mb-2">Min Rating: {filters.ratingMin}</label>
				<input
					type="range"
					min="0"
					max="5"
					step="0.5"
					bind:value={filters.ratingMin}
					class="w-full"
				/>
			</div>

			{#if $nsfwMode}
				<div>
					<label class="text-xs text-[#A1A1B5] block mb-2">Performer</label>
					<input
						type="text"
						placeholder="Search performer..."
						class="w-full px-3 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none text-sm"
					/>
				</div>
				<div>
					<label class="text-xs text-[#A1A1B5] block mb-2">Studio</label>
					<input
						type="text"
						placeholder="Filter by studio..."
						class="w-full px-3 py-2 rounded-lg bg-[#0D0D0F] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none text-sm"
					/>
				</div>
			{/if}
		</div>

		<!-- Main Area: Grid or List -->
		<div class="flex-1 flex flex-col overflow-hidden">
			{#if isScanning}
				<div class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 rounded-lg">
					<div class="bg-[#1A1A2E] p-8 rounded-lg border border-[#2A2A3E]">
						<p class="text-[#F1F5F9] mb-4">Scanning: {$indexProgress.current_file}</p>
						<div class="w-64 h-2 bg-[#2A2A3E] rounded-full overflow-hidden">
							<div
								class="h-full transition-all"
								style={`width: ${($indexProgress.processed / $indexProgress.total) * 100}%; background: linear-gradient(135deg, #EC4899, #D946EF);`}
							></div>
						</div>
						<p class="text-sm text-[#A1A1B5] mt-2">
							{$indexProgress.processed} / {$indexProgress.total}
						</p>
					</div>
				</div>
			{/if}

			{#if viewMode === 'grid'}
				<!-- Grid View -->
				<div class="grid grid-cols-4 gap-4 overflow-y-auto">
					{#each $searchResults as file (file.path)}
						<div
							class="rounded-lg overflow-hidden cursor-pointer border-2 transition-all"
							style={selectedFile?.path === file.path
								? 'border-color: #EC4899; background: rgba(236, 72, 153, 0.1);'
								: 'border-color: #2A2A3E; background: transparent;'}
							onclick={() => selectFile(file)}
						>
							<div class="aspect-square bg-[#2A2A3E] flex items-center justify-center overflow-hidden">
								{#if file.thumbnail}
									<img src={file.thumbnail} alt={file.name} class="w-full h-full object-cover" />
								{:else}
									<span class="text-4xl">📁</span>
								{/if}
							</div>
							<div class="p-3">
								<p class="text-xs font-medium text-[#F1F5F9] truncate">{file.name}</p>
								{#if file.rating}
									<p class="text-xs text-[#EC4899]">{'★'.repeat(Math.floor(file.rating))}</p>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<!-- List View -->
				<div class="space-y-2 overflow-y-auto">
					{#each $searchResults as file (file.path)}
						<div onclick={() => selectFile(file)}>
							<FileItem {file} selected={selectedFile?.path === file.path} />
						</div>
					{/each}
				</div>
			{/if}

			{#if $searchResults.length === 0}
				<div class="flex-1 flex items-center justify-center text-[#A1A1B5]">
					No files found
				</div>
			{/if}
		</div>

		<!-- Right Detail Panel -->
		{#if selectedFile}
			<div class="w-80 flex flex-col gap-4 bg-[#1A1A2E] rounded-lg p-4 border border-[#2A2A3E] overflow-y-auto">
				<h3 class="text-lg font-semibold text-[#F1F5F9]">{selectedFile.name}</h3>

				{#if selectedFile.thumbnail}
					<img src={selectedFile.thumbnail} alt={selectedFile.name} class="w-full h-48 object-cover rounded-lg" />
				{/if}

				<div class="space-y-3 text-sm">
					{#if selectedFile.type}
						<div>
							<span class="text-[#A1A1B5]">Type:</span>
							<span class="text-[#F1F5F9] ml-2">{selectedFile.type}</span>
						</div>
					{/if}
					
					{#if selectedFile.size}
						<div>
							<span class="text-[#A1A1B5]">Size:</span>
							<span class="text-[#F1F5F9] ml-2">{formatFileSize(selectedFile.size)}</span>
						</div>
					{/if}

					{#if selectedFile.duration}
						<div>
							<span class="text-[#A1A1B5]">Duration:</span>
							<span class="text-[#F1F5F9] ml-2">{formatDuration(selectedFile.duration)}</span>
						</div>
					{/if}

					{#if selectedFile.rating}
						<div>
							<span class="text-[#A1A1B5]">Rating:</span>
							<span class="text-[#F1F5F9] ml-2" style="color: #EC4899;">
								{'★'.repeat(Math.floor(selectedFile.rating))}
							</span>
						</div>
					{/if}

					{#if selectedFile.title}
						<div>
							<span class="text-[#A1A1B5]">Title:</span>
							<span class="text-[#F1F5F9] ml-2">{selectedFile.title}</span>
						</div>
					{/if}

					{#if selectedFile.artist}
						<div>
							<span class="text-[#A1A1B5]">Artist:</span>
							<span class="text-[#F1F5F9] ml-2">{selectedFile.artist}</span>
						</div>
					{/if}

					{#if selectedFile.genre}
						<div>
							<span class="text-[#A1A1B5]">Genre:</span>
							<span class="text-[#F1F5F9] ml-2">{Array.isArray(selectedFile.genre) ? selectedFile.genre.join(', ') : selectedFile.genre}</span>
						</div>
					{/if}
				</div>

				<div class="flex gap-2 pt-4 border-t border-[#2A2A3E]">
					<button
						class="flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all"
						style="background: linear-gradient(135deg, #EC4899, #D946EF);"
						onclick={openInPlayer}
					>
						Open
					</button>
					<button
						class="flex-1 px-3 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
						onclick={editInForge}
					>
						Edit
					</button>
				</div>
			</div>
		{/if}
	</div>

	<!-- Stats Bar -->
	<div class="flex gap-6 border-t border-[#2A2A3E] px-6 py-3 bg-[#1A1A2E] text-xs text-[#A1A1B5] flex-shrink-0">
		<div>
			Total: <span class="text-[#F1F5F9]">{$totalResults}</span> files
		</div>
		{#if $dbStats?.total_size}
			<div>
				Storage: <span class="text-[#F1F5F9]">{formatFileSize($dbStats.total_size)}</span>
			</div>
		{/if}
		{#if $dbStats?.last_scan}
			<div>
				Last scan: <span class="text-[#F1F5F9]">{formatDate($dbStats.last_scan)}</span>
			</div>
		{/if}
	</div>
</div>
