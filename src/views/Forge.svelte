<script lang="ts">
	import { nsfwMode, contentMode } from '../lib/stores/settings';
	import { selectedFiles, currentMetadata } from '../lib/stores/files';
	import { openFileDialog, openFolderDialog, ipcCall } from '../lib/utils/ipc';
	import FileItem from '../lib/components/FileItem.svelte';
	import TagPill from '../lib/components/TagPill.svelte';
	import StarRating from '../lib/components/StarRating.svelte';
	import ToggleSwitch from '../lib/components/ToggleSwitch.svelte';

	let files = $state<any[]>([]);
	let dragActive = $state(false);
	let isApplying = $state(false);
	let showPreview = $state(false);
	let templates = $state<Array<{ name: string; fields: Record<string, any> }>>([]);
	let selectedTemplate = $state('');
	let toast = $state<{ message: string; type: 'success' | 'error' | 'info' }>({ message: '', type: 'info' });
	let showToast = $state(false);

	// Form state
	let formData = $state<Record<string, any>>({
		title: '',
		artist: '',
		album: '',
		albumArtist: '',
		trackNumber: '',
		discNumber: '',
		year: '',
		genre: [],
		composer: '',
		comment: '',
		bpm: '',
		compilation: false,

		director: '',
		producer: '',
		cast: [],
		description: '',
		rating: 0,
		season: '',
		episode: '',
		studio: '',
		thumbnailUrl: '',

		author: '',
		keywords: [],
		dateTaken: '',
		camera: '',

		performers: [],
		physicalAttributes: {},
		positions: [],
		acts: [],
		sceneNumber: '',
		sourceUrl: '',
		sceneStudio: '',
		series: ''
	});

	const contentModes = ['music', 'film', 'photo', 'custom'];

	function getActiveMode() {
		if ($nsfwMode && $contentMode === 'adult') return 'adult';
		if (!contentModes.includes($contentMode)) return 'film';
		return $contentMode;
	}

	async function handleBrowseFiles() {
		const path = await openFileDialog();
		if (path) {
			if (!files.find(f => f.path === path)) {
				files = [...files, { path, name: path.split('/').pop(), type: '' }];
				$selectedFiles = files.map(f => f.path);
			}
		}
	}

	async function handleBrowseFolder() {
		const path = await openFolderDialog();
		if (path) {
			try {
				const result = await ipcCall('search_files', { query: '*', filters: {}, limit: 1000, offset: 0 });
				const newFiles = result.files.filter((f: any) => !files.find(x => x.path === f.path));
				files = [...files, ...newFiles];
				$selectedFiles = files.map(f => f.path);
			} catch (err) {
				showNotification('Failed to scan folder', 'error');
			}
		}
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragActive = true;
	}

	function handleDragLeave() {
		dragActive = false;
	}

	async function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragActive = false;

		const items = e.dataTransfer?.items;
		if (!items) return;

		for (let i = 0; i < items.length; i++) {
			if (items[i].kind === 'file') {
				const file = items[i].getAsFile();
				if (file && !files.find(f => f.name === file.name)) {
					files = [
						...files,
						{
							path: file.path || file.name,
							name: file.name,
							type: file.type,
							size: file.size
						}
					];
				}
			}
		}
		$selectedFiles = files.map(f => f.path);
	}

	function removeFile(index: number) {
		files = files.filter((_, i) => i !== index);
		$selectedFiles = files.map(f => f.path);
	}

	async function handleAutoLookup() {
		// Would call appropriate API based on content mode
		showNotification('Auto-lookup feature requires API configuration', 'info');
	}

	async function handleApply() {
		if (files.length === 0) {
			showNotification('No files selected', 'error');
			return;
		}

		isApplying = true;
		let successCount = 0;
		let errorCount = 0;

		for (const file of files) {
			try {
				await ipcCall('write_metadata', {
					path: file.path,
					metadata: formData
				});
				successCount++;
			} catch (err) {
				console.error(`Failed to write metadata to ${file.path}:`, err);
				errorCount++;
			}
		}

		isApplying = false;
		if (errorCount === 0) {
			showNotification(`Applied metadata to ${successCount} files`, 'success');
		} else {
			showNotification(`Applied to ${successCount}, failed on ${errorCount}`, 'error');
		}
	}

	function showNotification(message: string, type: 'success' | 'error' | 'info') {
		toast = { message, type };
		showToast = true;
		setTimeout(() => {
			showToast = false;
		}, 3000);
	}

	function saveTemplate() {
		const name = prompt('Template name:');
		if (name) {
			templates = [...templates, { name, fields: { ...formData } }];
			selectedTemplate = name;
		}
	}

	function loadTemplate(templateName: string) {
		const template = templates.find(t => t.name === templateName);
		if (template) {
			formData = { ...template.fields };
		}
	}

	function addTag(field: string, value: string) {
		if (value && !formData[field].includes(value)) {
			formData[field] = [...formData[field], value];
		}
	}

	function removeTag(field: string, value: string) {
		formData[field] = formData[field].filter((t: string) => t !== value);
	}
</script>

<div class="h-screen flex flex-col bg-[#0D0D0F]" style="color: #F1F5F9;">
	<!-- Top: Content Mode Tabs -->
	<div class="flex gap-2 border-b border-[#2A2A3E] px-6 py-4 bg-[#1A1A2E] flex-shrink-0">
		{#each contentModes as mode (mode)}
			<button
				class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
				style={getActiveMode() === mode
					? 'background: linear-gradient(135deg, #EC4899, #D946EF);'
					: 'background: transparent; border: 1px solid #2A2A3E;'}
				onclick={() => $contentMode = mode}
			>
				{mode.charAt(0).toUpperCase() + mode.slice(1)}
			</button>
		{/each}
		{#if $nsfwMode}
			<button
				class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
				style={getActiveMode() === 'adult'
					? 'background: linear-gradient(135deg, #EC4899, #D946EF);'
					: 'background: transparent; border: 1px solid #2A2A3E;'}
				onclick={() => $contentMode = 'adult'}
			>
				Adult
			</button>
		{/if}
	</div>

	<!-- Main Content -->
	<div class="flex-1 flex gap-4 p-6 overflow-hidden">
		<!-- Left Panel: File Picker -->
		<div class="w-1/3 flex flex-col gap-4 overflow-auto">
			<!-- Drag & Drop Zone -->
			<div
				class="border-2 border-dashed rounded-lg p-8 text-center transition-all"
				role="region"
				aria-label="Drag and drop zone for file uploads"
				style={dragActive
					? 'border-color: #EC4899; background: rgba(236, 72, 153, 0.1);'
					: 'border-color: #2A2A3E; background: transparent;'}
				ondragover={handleDragOver}
				ondragleave={handleDragLeave}
				ondrop={handleDrop}
			>
				<div class="text-4xl mb-3">📁</div>
				<p class="text-sm text-[#A1A1B5] mb-4">Drag files here or use buttons below</p>
				<div class="flex gap-2 justify-center">
					<button
						class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
						style="background: linear-gradient(135deg, #EC4899, #D946EF);"
						onclick={handleBrowseFiles}
					>
						Browse Files
					</button>
					<button
						class="px-4 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
						onclick={handleBrowseFolder}
					>
						Browse Folder
					</button>
				</div>
			</div>

			<!-- File List -->
			<div class="flex-1 overflow-y-auto space-y-2">
				{#each files as file, idx (file.path)}
					<div class="relative group">
						<FileItem {file} selected={$selectedFiles.includes(file.path)} onclick={() => {}} />
						<button
							class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-[#A1A1B5] hover:text-[#EC4899]"
							onclick={() => removeFile(idx)}
						>
							✕
						</button>
					</div>
				{/each}
				{#if files.length === 0}
					<div class="text-center text-[#A1A1B5] py-8">
						No files selected
					</div>
				{/if}
			</div>
		</div>

		<!-- Right Panel: Metadata Form -->
		<div class="w-2/3 flex flex-col gap-4 overflow-auto">
			<div class="space-y-4">
				{#if getActiveMode() === 'music'}
					<!-- Music Fields -->
					<input
						type="text"
						placeholder="Title"
						bind:value={formData.title}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Artist"
						bind:value={formData.artist}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Album"
						bind:value={formData.album}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Album Artist"
						bind:value={formData.albumArtist}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<div class="flex gap-2">
						<input
							type="number"
							placeholder="Track #"
							bind:value={formData.trackNumber}
							class="flex-1 px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
						<input
							type="number"
							placeholder="Disc #"
							bind:value={formData.discNumber}
							class="flex-1 px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
					</div>
					<input
						type="number"
						placeholder="Year"
						bind:value={formData.year}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Genre (comma-separated)"
						onchange={(e) => {
							const input = e.target as HTMLInputElement;
							formData.genre = input.value.split(',').map(g => g.trim()).filter(Boolean);
						}}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Composer"
						bind:value={formData.composer}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="number"
						placeholder="BPM"
						bind:value={formData.bpm}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<textarea
						placeholder="Comment"
						bind:value={formData.comment}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					></textarea>
					<div class="flex items-center gap-2">
						<input
							type="checkbox"
							id="compilation"
							bind:checked={formData.compilation}
							class="w-4 h-4"
						/>
						<label for="compilation" class="text-sm">Compilation</label>
					</div>
				{:else if getActiveMode() === 'film'}
					<!-- Film/TV Fields -->
					<input
						type="text"
						placeholder="Title"
						bind:value={formData.title}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Director"
						bind:value={formData.director}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Producer"
						bind:value={formData.producer}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<div>
						<label for="cast-input" class="text-xs text-[#A1A1B5] block mb-2">Cast</label>
						<div class="flex gap-2 mb-2">
							{#each formData.cast as actor (actor)}
								<TagPill tag={actor} removable onremove={() => removeTag('cast', actor)} />
							{/each}
						</div>
						<input
							id="cast-input"
							type="text"
							placeholder="Add cast member..."
							onkeypress={(e) => {
								if (e.key === 'Enter' && e.currentTarget.value) {
									addTag('cast', e.currentTarget.value);
									e.currentTarget.value = '';
								}
							}}
							class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
					</div>
					<input
						type="text"
						placeholder="Genre (comma-separated)"
						onchange={(e) => {
							const input = e.target as HTMLInputElement;
							formData.genre = input.value.split(',').map(g => g.trim()).filter(Boolean);
						}}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="number"
						placeholder="Year"
						bind:value={formData.year}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<textarea
						placeholder="Synopsis"
						bind:value={formData.description}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					></textarea>
					<div>
						<label class="text-xs text-[#A1A1B5] block mb-2" id="film-rating-label">Rating</label>
						<div aria-labelledby="film-rating-label">
							<StarRating rating={formData.rating} onchange={(r) => formData.rating = r} />
						</div>
					</div>
					<div class="flex gap-2">
						<input
							type="number"
							placeholder="Season"
							bind:value={formData.season}
							class="flex-1 px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
						<input
							type="number"
							placeholder="Episode"
							bind:value={formData.episode}
							class="flex-1 px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
					</div>
					<input
						type="text"
						placeholder="Studio"
						bind:value={formData.studio}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Thumbnail URL"
						bind:value={formData.thumbnailUrl}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
				{:else if getActiveMode() === 'photo'}
					<!-- Photo Fields -->
					<input
						type="text"
						placeholder="Title"
						bind:value={formData.title}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<textarea
						placeholder="Description"
						bind:value={formData.description}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					></textarea>
					<input
						type="text"
						placeholder="Author"
						bind:value={formData.author}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Copyright"
						bind:value={formData.copyright}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<div>
						<label for="keywords-input" class="text-xs text-[#A1A1B5] block mb-2">Keywords</label>
						<div class="flex gap-2 mb-2 flex-wrap">
							{#each formData.keywords as keyword (keyword)}
								<TagPill tag={keyword} removable onremove={() => removeTag('keywords', keyword)} />
							{/each}
						</div>
						<input
							id="keywords-input"
							type="text"
							placeholder="Add keyword..."
							onkeypress={(e) => {
								if (e.key === 'Enter' && e.currentTarget.value) {
									addTag('keywords', e.currentTarget.value);
									e.currentTarget.value = '';
								}
							}}
							class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
					</div>
					<input
						type="date"
						bind:value={formData.dateTaken}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Camera"
						bind:value={formData.camera}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
				{:else if getActiveMode() === 'adult'}
					<!-- Adult Content Fields -->
					<input
						type="text"
						placeholder="Title"
						bind:value={formData.title}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Studio"
						bind:value={formData.sceneStudio}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Director"
						bind:value={formData.director}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="number"
						placeholder="Year"
						bind:value={formData.year}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<div>
						<label for="performers-input" class="text-xs text-[#A1A1B5] block mb-2">Performers</label>
						<div class="flex gap-2 mb-2 flex-wrap">
							{#each formData.performers as performer (performer)}
								<TagPill tag={performer} removable onremove={() => removeTag('performers', performer)} />
							{/each}
						</div>
						<input
							id="performers-input"
							type="text"
							placeholder="Add performer..."
							onkeypress={(e) => {
								if (e.key === 'Enter' && e.currentTarget.value) {
									addTag('performers', e.currentTarget.value);
									e.currentTarget.value = '';
								}
							}}
							class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
					</div>
					<input
						type="text"
						placeholder="Genre (comma-separated)"
						onchange={(e) => {
							const input = e.target as HTMLInputElement;
							formData.genre = input.value.split(',').map(g => g.trim()).filter(Boolean);
						}}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<div>
						<label class="text-xs text-[#A1A1B5] block mb-2">Positions</label>
						<div class="flex gap-2 mb-2 flex-wrap">
							{#each formData.positions as position (position)}
								<TagPill tag={position} removable onremove={() => removeTag('positions', position)} />
							{/each}
						</div>
						<input
							type="text"
							placeholder="Add position..."
							onkeypress={(e) => {
								if (e.key === 'Enter' && e.currentTarget.value) {
									addTag('positions', e.currentTarget.value);
									e.currentTarget.value = '';
								}
							}}
							class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
					</div>
					<div>
						<label class="text-xs text-[#A1A1B5] block mb-2">Acts</label>
						<div class="flex gap-2 mb-2 flex-wrap">
							{#each formData.acts as act (act)}
								<TagPill tag={act} removable onremove={() => removeTag('acts', act)} />
							{/each}
						</div>
						<input
							type="text"
							placeholder="Add act..."
							onkeypress={(e) => {
								if (e.key === 'Enter' && e.currentTarget.value) {
									addTag('acts', e.currentTarget.value);
									e.currentTarget.value = '';
								}
							}}
							class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
						/>
					</div>
					<input
						type="text"
						placeholder="Scene Setting"
						bind:value={formData.sceneNumber}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Series"
						bind:value={formData.series}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<input
						type="text"
						placeholder="Source URL"
						bind:value={formData.sourceUrl}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9] placeholder-[#A1A1B5] focus:border-[#EC4899] outline-none"
					/>
					<div>
						<label class="text-xs text-[#A1A1B5] block mb-2">Rating</label>
						<StarRating rating={formData.rating} onchange={(r) => formData.rating = r} />
					</div>
				{:else}
					<!-- Custom Mode -->
					<div class="text-center py-8 text-[#A1A1B5]">
						Use Templates to define custom fields
					</div>
					<select bind:value={selectedTemplate} onchange={(e) => loadTemplate(e.currentTarget.value)}
						class="w-full px-3 py-2 rounded-lg bg-[#1A1A2E] border border-[#2A2A3E] text-[#F1F5F9]">
						<option value="">Select template...</option>
						{#each templates as template (template.name)}
							<option value={template.name}>{template.name}</option>
						{/each}
					</select>
				{/if}
			</div>
		</div>
	</div>

	<!-- Bottom Action Bar -->
	<div class="flex gap-4 border-t border-[#2A2A3E] px-6 py-4 bg-[#1A1A2E] flex-shrink-0">
		<button
			class="px-4 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
			onclick={handleAutoLookup}
		>
			Auto-Lookup
		</button>
		<button
			class="px-4 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
			onclick={() => showPreview = !showPreview}
		>
			Preview Changes
		</button>
		<button
			class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
			style="background: linear-gradient(135deg, #EC4899, #D946EF);"
			onclick={handleApply}
			disabled={isApplying}
		>
			{isApplying ? 'Applying...' : 'Apply to All Files'}
		</button>
		<button
			class="ml-auto px-4 py-2 rounded-lg text-sm font-medium border border-[#2A2A3E] transition-all hover:border-[#EC4899]"
			onclick={saveTemplate}
		>
			Save Template
		</button>
	</div>

	<!-- Toast Notification -->
	{#if showToast}
		<div
			class="fixed bottom-6 right-6 px-4 py-3 rounded-lg text-sm font-medium transition-all"
			style={toast.type === 'success'
				? 'background: rgba(16, 185, 129, 0.2); border: 1px solid #10B981; color: #10B981;'
				: toast.type === 'error'
					? 'background: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #EF4444;'
					: 'background: rgba(59, 130, 246, 0.2); border: 1px solid #3B82F6; color: #3B82F6;'}
		>
			{toast.message}
		</div>
	{/if}
</div>
