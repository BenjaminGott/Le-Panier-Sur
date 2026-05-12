<script lang="ts">
	import { filters, resetFilters, activeFilterCount } from '$lib/stores/filters';
	import {
		COULEURS,
		COULEUR_HEX,
		HABITATS,
		MOIS,
		STATUT_ORDER,
		STATUT_LABEL,
		STATUT_VARIANT
	} from '$lib/data/types';

	export let availableStatuts: string[] = [];
	export let totalCount = 0;
	export let visibleCount = 0;

	const VARIANT_COLOR: Record<string, string> = {
		excellent: '#2e7d32',
		bon: '#66a44e',
		mediocre: '#cda434',
		rejeter: '#e07c2a',
		toxique: '#c1333d',
		mortel: '#7a0e1a'
	};

	$: count = activeFilterCount($filters);

	function toggle<T>(arr: T[], v: T): T[] {
		return arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
	}

	function toggleStatut(s: string) {
		filters.update((f) => ({ ...f, statuts: toggle(f.statuts, s) }));
	}
	function toggleHabitat(h: string) {
		filters.update((f) => ({ ...f, habitats: toggle(f.habitats, h) }));
	}
	function toggleMois(m: number) {
		filters.update((f) => ({ ...f, mois: toggle(f.mois, m) }));
	}
	function toggleCouleur(c: string) {
		filters.update((f) => ({ ...f, couleursChapeau: toggle(f.couleursChapeau, c) }));
	}

	// Toujours afficher les 6 statuts ; on grise ceux absents du dataset
	$: orderedStatuts = STATUT_ORDER;
	function isAvailable(s: string) {
		return availableStatuts.length === 0 || availableStatuts.includes(s);
	}
</script>

<aside class="flex flex-col gap-6 p-1">
	<header class="flex items-center justify-between">
		<div>
			<h2 class="font-display text-lg font-semibold text-forest-900">Filtres</h2>
			<p class="text-xs text-forest-600">
				{visibleCount} / {totalCount} champignons
			</p>
		</div>
		{#if count > 0}
			<button class="btn-ghost text-xs" on:click={resetFilters}>Réinitialiser</button>
		{/if}
	</header>

	<section>
		<h3 class="section-title mb-2">Statut</h3>
		<div class="flex flex-col gap-1">
			{#each orderedStatuts as s}
				{@const checked = $filters.statuts.includes(s)}
				{@const variant = STATUT_VARIANT[s] ?? 'mediocre'}
				{@const dot = VARIANT_COLOR[variant]}
				{@const enabled = isAvailable(s)}
				<button
					type="button"
					on:click={() => toggleStatut(s)}
					disabled={!enabled}
					class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition"
					class:bg-forest-100={checked}
					class:text-forest-900={checked}
					class:hover:bg-forest-50={!checked && enabled}
					class:opacity-40={!enabled}
					class:cursor-not-allowed={!enabled}
					title={enabled ? '' : 'Aucune espèce dans ce statut'}
				>
					<span
						class="flex h-4 w-4 shrink-0 items-center justify-center rounded border-2 transition"
						class:border-forest-700={checked}
						class:bg-forest-700={checked}
						class:border-forest-300={!checked}
						class:bg-white={!checked}
					>
						{#if checked}
							<svg class="h-3 w-3 text-white" viewBox="0 0 12 12" aria-hidden="true">
								<path
									d="M2 6l3 3 5-6"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							</svg>
						{/if}
					</span>
					<span
						class="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
						style="background-color: {dot}"
					></span>
					<span class="flex-1 text-forest-800">{STATUT_LABEL[s] ?? s}</span>
				</button>
			{/each}
		</div>
	</section>

	<section>
		<h3 class="section-title mb-2">Saison</h3>
		<div class="grid grid-cols-6 gap-1">
			{#each MOIS as m, i}
				{@const month = i + 1}
				{@const active = $filters.mois.includes(month)}
				<button
					type="button"
					on:click={() => toggleMois(month)}
					class="rounded-md px-1 py-1.5 text-[0.7rem] font-medium transition"
					class:bg-forest-600={active}
					class:text-white={active}
					class:bg-white={!active}
					class:text-forest-700={!active}
					class:hover:bg-forest-100={!active}
				>
					{m}
				</button>
			{/each}
		</div>
	</section>

	<section>
		<h3 class="section-title mb-2">Couleur du chapeau</h3>
		<div class="flex flex-wrap gap-1.5">
			{#each COULEURS as c}
				{@const active = $filters.couleursChapeau.includes(c)}
				<button
					type="button"
					on:click={() => toggleCouleur(c)}
					title={c}
					aria-label="Couleur {c}"
					class="h-7 w-7 rounded-full border-2 transition"
					class:border-forest-700={active}
					class:scale-110={active}
					class:border-white={!active}
					style="background-color: {COULEUR_HEX[c]}"
				></button>
			{/each}
		</div>
	</section>

	<section>
		<h3 class="section-title mb-2">Habitat</h3>
		<div class="flex flex-wrap gap-1.5">
			{#each HABITATS as h}
				{@const active = $filters.habitats.includes(h)}
				<button
					type="button"
					on:click={() => toggleHabitat(h)}
					class="chip border text-xs transition"
					class:bg-forest-600={active}
					class:text-white={active}
					class:border-forest-600={active}
					class:bg-white={!active}
					class:border-forest-200={!active}
					class:text-forest-700={!active}
					class:hover:bg-forest-100={!active}
				>
					{h.replace(/_/g, ' ')}
				</button>
			{/each}
		</div>
	</section>
</aside>
