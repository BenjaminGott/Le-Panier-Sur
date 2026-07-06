<script lang="ts">
	import { filters } from '$lib/stores/filters';
	import { onMount } from 'svelte';

	let value = '';
	let debounceTimer: ReturnType<typeof setTimeout>;
	let inputEl: HTMLInputElement;

	$: ($filters, syncFromStore());
	function syncFromStore() {
		if ($filters.search !== value) value = $filters.search;
	}

	function onInput() {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			filters.update((f) => ({ ...f, search: value }));
		}, 150);
	}

	onMount(() => {
		const handler = (e: KeyboardEvent) => {
			if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
				e.preventDefault();
				inputEl?.focus();
				inputEl?.select();
			}
		};
		window.addEventListener('keydown', handler);
		return () => window.removeEventListener('keydown', handler);
	});
</script>

<div class="relative w-full max-w-md">
	<svg
		class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-forest-500"
		fill="none"
		viewBox="0 0 24 24"
		stroke="currentColor"
		stroke-width="2"
		aria-hidden="true"
	>
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="M21 21l-4.35-4.35M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16Z"
		/>
	</svg>
	<input
		bind:this={inputEl}
		bind:value
		on:input={onInput}
		type="search"
		placeholder="Rechercher un champignon…"
		class="w-full rounded-xl border border-forest-200 bg-white/80 py-2 pl-9 pr-3 text-sm text-forest-900 shadow-sm placeholder:text-forest-400 focus:border-forest-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-forest-200"
	/>
</div>
