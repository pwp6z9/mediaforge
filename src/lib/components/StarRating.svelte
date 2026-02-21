<script lang="ts">
	interface Props {
		rating?: number;
		readonly?: boolean;
		onchange?: (rating: number) => void;
	}

	let { rating = 0, readonly = false, onchange }: Props = $props();

	let currentRating = $state(rating);
	let hoverRating = $state(0);

	$effect(() => {
		currentRating = rating;
	});

	function handleClick(index: number, isHalf: boolean) {
		if (readonly) return;
		const newRating = isHalf ? index + 0.5 : index + 1;
		currentRating = newRating;
		onchange?.(newRating);
		const event = new CustomEvent('change', { detail: { rating: newRating } });
		window.dispatchEvent(event);
	}

	function handleMouseEnter(index: number) {
		if (readonly) return;
		hoverRating = index + 1;
	}

	function handleMouseLeave() {
		hoverRating = 0;
	}
</script>

<div class="flex gap-1" class:cursor-not-allowed={readonly}>
	{#each [0, 1, 2, 3, 4] as index (index)}
		<div
			class="relative w-6 h-6"
			onmouseenter={() => handleMouseEnter(index)}
			onmouseleave={handleMouseLeave}
		>
			<!-- Background star -->
			<button
				class="absolute inset-0 text-xl"
				style="color: #2A2A3E;"
				type="button"
				disabled={readonly}
				aria-label="Rate {index + 1} stars"
			>
				★
			</button>

			<!-- Half star -->
			<button
				class="absolute inset-0 w-1/2 text-xl overflow-hidden text-left"
				style={((hoverRating > 0 && hoverRating > index + 0.5) ||
				(hoverRating === 0 && currentRating > index + 0.5))
					? 'color: #EC4899;'
					: 'color: transparent;'}
				type="button"
				disabled={readonly}
				onclick={() => handleClick(index, true)}
				aria-label="Rate {index + 0.5} stars"
			>
				★
			</button>

			<!-- Full star -->
			<button
				class="absolute inset-0 text-xl"
				style={((hoverRating > 0 && hoverRating > index) ||
				(hoverRating === 0 && currentRating > index))
					? 'color: #EC4899;'
					: 'color: transparent;'}
				type="button"
				disabled={readonly}
				onclick={() => handleClick(index, false)}
				aria-label="Rate {index + 1} stars"
			>
				★
			</button>
		</div>
	{/each}
</div>

<style>
	button {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		font-size: inherit;
		transition: color 0.2s;
	}

	button:disabled {
		cursor: not-allowed;
	}

	div:hover button:nth-child(1) {
		opacity: 0.7;
	}
</style>
