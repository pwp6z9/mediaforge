<script lang="ts">
	import { getFileIcon, formatFileSize, formatDuration, truncate } from '../utils/formatters';

	interface Props {
		file: any;
		selected?: boolean;
		onclick?: () => void;
		ondblclick?: () => void;
	}

	let { file, selected = false, onclick, ondblclick }: Props = $props();
</script>

<div
	class="flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 cursor-pointer hover:bg-[#2A2A3E]"
	style={selected
		? 'border: 2px solid #EC4899; background: rgba(236, 72, 153, 0.1);'
		: 'border: 1px solid #2A2A3E; background: transparent;'}
	role="button"
	tabindex="0"
	{onclick}
	{ondblclick}
	onkeydown={(e) => {
		if (e.key === 'Enter') ondblclick?.();
	}}
>
	<!-- Thumbnail or Icon -->
	<div class="flex-shrink-0 w-16 h-16 rounded-lg bg-[#2A2A3E] flex items-center justify-center overflow-hidden">
		{#if file.thumbnail}
			<img src={file.thumbnail} alt={file.name} class="w-full h-full object-cover" />
		{:else}
			<span class="text-3xl">{getFileIcon(file.type || '')}</span>
		{/if}
	</div>

	<!-- File Info -->
	<div class="flex-1 min-w-0">
		<div class="text-sm font-medium text-[#F1F5F9] truncate" title={file.name}>
			{truncate(file.name, 50)}
		</div>
		<div class="text-xs text-[#A1A1B5] mt-1 space-y-1">
			<div>
				{file.size ? formatFileSize(file.size) : 'Unknown size'}
				{#if file.duration}
					• {formatDuration(file.duration)}
				{/if}
			</div>
			{#if file.type}
				<div class="uppercase">{file.type.split('/')[1] || file.type}</div>
			{/if}
		</div>
	</div>

	<!-- Rating -->
	{#if file.rating}
		<div class="flex-shrink-0 text-lg" style="color: #EC4899;">
			{'★'.repeat(Math.floor(file.rating))}
			{#if file.rating % 1 !== 0}
				<span style="opacity: 0.5;">★</span>
			{/if}
		</div>
	{/if}
</div>

<style>
	div[role='button']:focus {
		outline: 2px solid #EC4899;
		outline-offset: 2px;
	}
</style>
