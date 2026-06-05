<script lang="ts">
	import { base } from '$app/paths';
	import type { Mushroom } from '$lib/data/types';
	import { STATUT_VARIANT } from '$lib/data/types';

	export let mushroom: Mushroom;

	const VARIANT_BORDER: Record<string, string> = {
		excellent: 'border-status-excellent/40',
		bon: 'border-status-bon/40',
		mediocre: 'border-status-mediocre/40',
		rejeter: 'border-status-rejeter/40',
		toxique: 'border-status-toxique/40',
		mortel: 'border-status-mortel/50'
	};

	const VARIANT_DOT: Record<string, string> = {
		excellent: 'bg-status-excellent',
		bon: 'bg-status-bon',
		mediocre: 'bg-status-mediocre',
		rejeter: 'bg-status-rejeter',
		toxique: 'bg-status-toxique',
		mortel: 'bg-status-mortel'
	};

	$: variant = STATUT_VARIANT[mushroom.statut] ?? 'mediocre';
</script>

<a
	href="{base}/champignon/{mushroom.slug}"
	class="group flex items-center gap-3 rounded-lg border bg-white p-2 transition hover:-translate-y-0.5 hover:shadow-card focus:outline-none focus:ring-2 focus:ring-forest-400 {VARIANT_BORDER[
		variant
	] ?? VARIANT_BORDER.mediocre}"
>
	<div class="relative h-12 w-12 shrink-0 overflow-hidden rounded-md bg-forest-100">
		{#if mushroom.image}
			<img
				src="{base}{mushroom.image}"
				alt={mushroom.nom}
				loading="lazy"
				class="h-full w-full object-cover"
			/>
		{:else}
			<div class="flex h-full w-full items-center justify-center text-lg text-forest-300">🍄</div>
		{/if}
	</div>
	<div class="min-w-0 flex-1">
		<p
			class="truncate font-display text-xs font-semibold text-forest-900 group-hover:text-forest-700"
		>
			{mushroom.nom}
		</p>
		<p class="mt-0.5 flex items-center gap-1.5 text-[0.65rem] text-forest-600">
			<span
				class="h-1.5 w-1.5 shrink-0 rounded-full {VARIANT_DOT[variant] ?? VARIANT_DOT.mediocre}"
				aria-hidden="true"
			></span>
			<span class="truncate">{mushroom.statut}</span>
		</p>
	</div>
</a>
