<script lang="ts">
	import { MOIS } from '$lib/data/types';
	export let active: number[] = [];
</script>

<div class="card p-5">
	<header class="mb-3 flex items-center gap-2">
		<span class="text-lg" aria-hidden="true">📅</span>
		<h3 class="font-display text-lg font-semibold text-forest-900">Saison</h3>
	</header>
	<div class="grid grid-cols-12 gap-1">
		{#each MOIS as m, i}
			{@const on = active.includes(i + 1)}
			<div
				class="flex flex-col items-center gap-1 rounded-md py-2 text-[0.7rem] font-medium transition"
				class:bg-forest-600={on}
				class:text-white={on}
				class:bg-forest-100={!on}
				class:text-forest-500={!on}
			>
				<span>{m}</span>
			</div>
		{/each}
	</div>
</div>
