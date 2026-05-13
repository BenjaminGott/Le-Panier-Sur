<script lang="ts">
	import { onMount } from 'svelte';
	import { loadMushrooms } from '$lib/data/loader';
	import type { Mushroom } from '$lib/data/types';
	import { STATUT_VARIANT } from '$lib/data/types';
	import PieStatuts from '$lib/components/charts/PieStatuts.svelte';
	import BarSaisons from '$lib/components/charts/BarSaisons.svelte';
	import BarHabitats from '$lib/components/charts/BarHabitats.svelte';

	let mushrooms: Mushroom[] = [];
	let loading = true;

	onMount(async () => {
		mushrooms = await loadMushrooms();
		loading = false;
	});

	$: total = mushrooms.length;
	$: comestibles = mushrooms.filter((m) =>
		['excellent', 'bon', 'mediocre'].includes(STATUT_VARIANT[m.statut])
	).length;
	$: dangereux = mushrooms.filter((m) =>
		['toxique', 'mortel'].includes(STATUT_VARIANT[m.statut])
	).length;
	$: arejeter = mushrooms.filter((m) => STATUT_VARIANT[m.statut] === 'rejeter').length;
</script>

<svelte:head>
	<title>Statistiques — Le Panier-Sûr</title>
</svelte:head>

<section class="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:py-10">
	<header class="mb-6">
		<p class="section-title">Vue d'ensemble</p>
		<h1 class="font-display text-3xl font-bold text-forest-900 sm:text-4xl">Statistiques</h1>
	</header>

	{#if loading}
		<p class="text-forest-600">Chargement…</p>
	{:else}
		<div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
			<div class="card p-5">
				<p class="section-title">Total</p>
				<p class="font-display text-3xl font-bold text-forest-900">{total}</p>
			</div>
			<div class="card p-5">
				<p class="section-title">Comestibles</p>
				<p class="font-display text-3xl font-bold text-status-excellent">{comestibles}</p>
			</div>
			<div class="card p-5">
				<p class="section-title">À rejeter</p>
				<p class="font-display text-3xl font-bold text-status-rejeter">{arejeter}</p>
			</div>
			<div class="card p-5">
				<p class="section-title">Toxiques / Mortels</p>
				<p class="font-display text-3xl font-bold text-status-toxique">{dangereux}</p>
			</div>
		</div>

		<div class="grid gap-5 lg:grid-cols-2">
			<div class="card p-5 lg:col-span-1">
				<h2 class="mb-4 font-display text-lg font-semibold text-forest-900">
					Répartition par statut
				</h2>
				<PieStatuts {mushrooms} />
			</div>
			<div class="card p-5 lg:col-span-1">
				<h2 class="mb-4 font-display text-lg font-semibold text-forest-900">
					Espèces actives par mois
				</h2>
				<BarSaisons {mushrooms} />
			</div>
			<div class="card p-5 lg:col-span-2">
				<h2 class="mb-4 font-display text-lg font-semibold text-forest-900">
					Top 10 des habitats
				</h2>
				<BarHabitats {mushrooms} />
			</div>
		</div>
	{/if}
</section>
