<script lang="ts">
	import { sentryActive } from '../stores/sentry';

	interface Props {
		activeView: string;
	}

	let { activeView }: Props = $props();

	const views = [
		{ name: 'forge', icon: '⚡', label: 'Forge' },
		{ name: 'vault', icon: '📚', label: 'Vault' },
		{ name: 'sentry', icon: '👁', label: 'Sentry' },
		{ name: 'settings', icon: '⚙', label: 'Settings' }
	];

	function handleClick(viewName: string) {
		const event = new CustomEvent('viewChange', {
			detail: { view: viewName }
		});
		window.dispatchEvent(event);
	}
</script>

<aside
	class="flex flex-col items-center gap-6 bg-[#1A1A2E] border-r border-[#2A2A3E] py-8 px-4 h-screen"
	style="width: 60px;"
>
	{#each views as view (view.name)}
		<div class="relative">
			<button
				class="flex items-center justify-center w-12 h-12 rounded-lg transition-all duration-200 relative"
				class:active={activeView === view.name}
				style={activeView === view.name
					? 'background: linear-gradient(135deg, #EC4899, #D946EF);'
					: 'background: transparent;'}
				onclick={() => handleClick(view.name)}
				title={view.label}
			>
				<span class="text-xl">{view.icon}</span>
			</button>
			
			{#if view.name === 'sentry' && $sentryActive}
				<div
					class="absolute top-2 right-2 w-2 h-2 rounded-full"
					style="background: #10B981;"
				></div>
			{/if}
		</div>
	{/each}
</aside>

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

	aside {
		scrollbar-width: thin;
		scrollbar-color: var(--bg-tertiary) var(--bg-secondary);
	}

	aside::-webkit-scrollbar {
		width: 6px;
	}

	aside::-webkit-scrollbar-track {
		background: var(--bg-secondary);
	}

	aside::-webkit-scrollbar-thumb {
		background: var(--bg-tertiary);
		border-radius: 3px;
	}
</style>
