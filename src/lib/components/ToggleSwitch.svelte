<script lang="ts">
	interface Props {
		checked?: boolean;
		label: string;
		description?: string;
		color?: string;
		onchange?: (value: boolean) => void;
	}

	let { checked = false, label, description, color = 'pink', onchange }: Props = $props();

	let isChecked = $derived(checked);

	function toggle() {
		onchange?.(!isChecked);
		const event = new CustomEvent('change', {
			detail: { checked: !isChecked }
		});
		window.dispatchEvent(event);
	}
</script>

<div class="flex items-center justify-between gap-4">
	<div class="flex-1">
		<label for="toggle-switch" class="block text-sm font-medium text-[#F1F5F9] cursor-pointer">
			{label}
		</label>
		{#if description}
			<p class="text-xs text-[#A1A1B5] mt-1">{description}</p>
		{/if}
	</div>

	<button
		id="toggle-switch"
		role="switch"
		aria-checked={isChecked}
		aria-label="{label}: {isChecked ? 'enabled' : 'disabled'}"
		class="relative inline-flex h-6 w-11 rounded-full transition-all duration-300"
		style={isChecked
			? 'background: linear-gradient(135deg, #EC4899, #D946EF);'
			: 'background: #2A2A3E;'}
		onclick={toggle}
	>
		<span
			class="inline-block h-5 w-5 transform rounded-full bg-white transition-all duration-300"
			style={`margin-top: 2px; ${isChecked ? 'margin-left: 22px;' : 'margin-left: 2px;'}`}
		></span>
	</button>
</div>

<style>
	button:hover {
		opacity: 0.9;
	}
</style>
