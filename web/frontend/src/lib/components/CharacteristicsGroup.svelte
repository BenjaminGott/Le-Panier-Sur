<script lang="ts">
	import { COULEUR_HEX } from '$lib/data/types';

	export let titre: string;
	export let icon = '';
	export let items: string[] = [];
	export let colorMode = false;

	function isCouleur(s: string): s is keyof typeof COULEUR_HEX {
		return s in COULEUR_HEX;
	}
</script>

<section class="card p-5">
	<header class="mb-3 flex items-center gap-2">
		{#if icon}<span class="text-lg" aria-hidden="true">{icon}</span>{/if}
		<h3 class="font-display text-lg font-semibold text-forest-900">{titre}</h3>
	</header>
	{#if items.length === 0}
		<p class="text-sm text-forest-500">Pas d'information.</p>
	{:else}
		<ul class="flex flex-wrap gap-1.5">
			{#each items as it}
				{@const niceLabel = it.replace(/_/g, ' ')}
				{#if colorMode && isCouleur(it)}
					<li
						class="chip border border-forest-200 bg-white text-xs text-forest-800"
						style="--c: {COULEUR_HEX[it]}"
					>
						<span
							class="inline-block h-3 w-3 rounded-full border border-forest-200"
							style="background-color: {COULEUR_HEX[it]}"
						></span>
						{niceLabel}
					</li>
				{:else}
					<li class="chip bg-forest-100 text-xs text-forest-800">{niceLabel}</li>
				{/if}
			{/each}
		</ul>
	{/if}
</section>
