<script lang="ts">
	interface Props {
		tag: string;
		removable?: boolean;
		color?: string;
		onremove?: () => void;
	}

	let { tag, removable = false, color = 'pink', onremove }: Props = $props();

	function remove() {
		onremove?.();
		const event = new CustomEvent('remove', { detail: { tag } });
		window.dispatchEvent(event);
	}
</script>

<div
	class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap"
	style={color === 'pink'
		? 'background: rgba(236, 72, 153, 0.15); color: #EC4899; border: 1px solid #EC4899;'
		: 'background: rgba(217, 70, 239, 0.15); color: #D946EF; border: 1px solid #D946EF;'}
>
	<span>{tag}</span>
	{#if removable}
		<button
			class="text-xs hover:opacity-70 transition-opacity ml-1"
			onclick={remove}
			type="button"
			aria-label="Remove {tag}"
		>
			✕
		</button>
	{/if}
</div>

<style>
	button {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		font-size: inherit;
	}
</style>
