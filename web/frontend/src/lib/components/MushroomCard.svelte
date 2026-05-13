<script lang="ts">
	import { base } from '$app/paths';
	import type { Mushroom } from '$lib/data/types';
	import StatusBadge from './StatusBadge.svelte';

	export let mushroom: Mushroom;

	$: chapeauRange =
		mushroom.chapeau_taille_min_cm != null && mushroom.chapeau_taille_max_cm != null
			? `${mushroom.chapeau_taille_min_cm}–${mushroom.chapeau_taille_max_cm} cm`
			: '';
</script>

<a
	href="{base}/champignon/{mushroom.slug}"
	class="card group flex flex-col overflow-hidden hover:shadow-card-hover hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-forest-400"
>
	<div class="relative aspect-[4/3] overflow-hidden bg-forest-100">
		{#if mushroom.image}
			<img
				src="{base}{mushroom.image}"
				alt={mushroom.nom}
				loading="lazy"
				class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
			/>
		{:else}
			<div class="flex h-full w-full items-center justify-center text-4xl text-forest-300">
				🍄
			</div>
		{/if}
		<div class="absolute left-3 top-3">
			<StatusBadge statut={mushroom.statut} />
		</div>
	</div>
	<div class="flex flex-1 flex-col gap-1.5 p-4">
		<h3 class="font-display text-base font-semibold leading-tight text-forest-900 line-clamp-2">
			{mushroom.nom}
		</h3>
		{#if chapeauRange}
			<p class="text-xs text-forest-600">Chapeau {chapeauRange}</p>
		{/if}
	</div>
</a>
