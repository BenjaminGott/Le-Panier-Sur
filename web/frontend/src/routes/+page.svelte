<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { loadMushrooms } from '$lib/data/loader';
	import type { Mushroom } from '$lib/data/types';
	import { filters, makeFiltered, activeFilterCount, resetFilters } from '$lib/stores/filters';
	import MushroomCard from '$lib/components/MushroomCard.svelte';
	import FilterSidebar from '$lib/components/FilterSidebar.svelte';

	let loading = true;
	let error = '';
	const mushrooms = writable<Mushroom[]>([]);
	const filtered = makeFiltered(mushrooms);

	let availableStatuts: string[] = [];
	let drawerOpen = false;

	const PAGE_SIZE = 24;

	// La page courante est lue depuis l'URL (?page=N) — survit aux retours navigateur
	$: urlPage = (() => {
		const raw = $page.url.searchParams.get('page');
		const n = raw ? parseInt(raw, 10) : 1;
		return Number.isFinite(n) && n >= 1 ? n : 1;
	})();

	onMount(async () => {
		try {
			const items = await loadMushrooms();
			mushrooms.set(items);
			availableStatuts = [...new Set(items.map((i) => i.statut))].filter(Boolean);
			loading = false;
		} catch (e) {
			error = String(e);
			loading = false;
		}
	});

	let prevFilterKey = '';
	$: filterKey = JSON.stringify($filters);
	$: if (prevFilterKey && prevFilterKey !== filterKey) {
		// Reset to page 1 when filters change (but not on initial mount)
		setPage(1, true);
	}
	$: prevFilterKey = filterKey;

	$: count = activeFilterCount($filters);
	$: totalPages = Math.max(1, Math.ceil($filtered.length / PAGE_SIZE));
	$: currentPage = Math.min(Math.max(1, urlPage), totalPages);
	$: startIdx = (currentPage - 1) * PAGE_SIZE;
	$: pageItems = $filtered.slice(startIdx, startIdx + PAGE_SIZE);

	function setPage(p: number, replace = false) {
		const target = Math.min(totalPages, Math.max(1, p));
		const params = new URLSearchParams($page.url.searchParams);
		if (target <= 1) params.delete('page');
		else params.set('page', String(target));
		const qs = params.toString();
		goto(qs ? `?${qs}` : '?', {
			keepFocus: true,
			noScroll: true,
			replaceState: replace
		});
	}

	function goToPage(p: number) {
		setPage(p);
		if (typeof window !== 'undefined') {
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}

	function pageNumbers(current: number, total: number): (number | '…')[] {
		if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
		const out: (number | '…')[] = [1];
		const start = Math.max(2, current - 1);
		const end = Math.min(total - 1, current + 1);
		if (start > 2) out.push('…');
		for (let i = start; i <= end; i++) out.push(i);
		if (end < total - 1) out.push('…');
		out.push(total);
		return out;
	}

	$: pages = pageNumbers(currentPage, totalPages);
</script>

<svelte:head>
	<title>Le Panier-Sûr — Galerie</title>
</svelte:head>

<section class="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:py-10">
	<div class="mb-6 flex flex-col gap-2 sm:mb-8">
		<p class="section-title">Bienvenue dans</p>
		<h1 class="font-display text-3xl font-bold text-forest-900 sm:text-4xl">
			Le Panier-Sûr 🍄
		</h1>
		<p class="max-w-2xl text-sm text-forest-700 sm:text-base">
			Explore une collection de
			<strong>{$mushrooms.length}</strong> champignons. Filtre par statut, saison, habitat ou
			couleur de chapeau, et consulte la fiche détaillée pour identifier au mieux ta cueillette.
		</p>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-20 text-forest-600">Chargement…</div>
	{:else if error}
		<div class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
			Erreur de chargement : {error}
		</div>
	{:else}
		<div class="flex gap-6">
			<aside class="card hidden w-72 shrink-0 self-start p-5 lg:block">
				<FilterSidebar
					{availableStatuts}
					totalCount={$mushrooms.length}
					visibleCount={$filtered.length}
				/>
			</aside>

			<div class="flex-1">
				<div class="mb-4 flex items-center justify-between gap-3">
					<button
						class="btn-ghost relative lg:hidden"
						on:click={() => (drawerOpen = true)}
						aria-label="Ouvrir les filtres"
					>
						<svg
							class="h-4 w-4"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							viewBox="0 0 24 24"
							aria-hidden="true"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M3 6h18M6 12h12M10 18h4"
							/>
						</svg>
						Filtres
						{#if count > 0}
							<span
								class="ml-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-forest-600 px-1.5 text-[0.65rem] font-semibold text-white"
								>{count}</span
							>
						{/if}
					</button>
					<p class="text-sm text-forest-700">
						<strong>{$filtered.length}</strong>
						{#if $filtered.length === $mushrooms.length}
							champignons
						{:else}
							/ {$mushrooms.length} champignons
						{/if}
					</p>
					{#if count > 0}
						<button class="btn-ghost text-xs" on:click={resetFilters}>Effacer filtres</button>
					{/if}
				</div>

				{#if $filtered.length === 0}
					<div class="card p-10 text-center text-forest-600">
						Aucun champignon ne correspond aux filtres.
					</div>
				{:else}
					<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
						{#each pageItems as m (m.slug)}
							<MushroomCard mushroom={m} />
						{/each}
					</div>

					{#if totalPages > 1}
						<nav class="mt-10 flex flex-col items-center gap-3" aria-label="Pagination">
							<p class="text-xs text-forest-600">
								Page <strong>{currentPage}</strong> / {totalPages} —
								affichage {startIdx + 1}–{Math.min(startIdx + PAGE_SIZE, $filtered.length)}
								sur {$filtered.length}
							</p>
							<div class="flex flex-wrap items-center justify-center gap-1.5">
								<button
									class="btn-ghost px-3 text-sm disabled:cursor-not-allowed disabled:opacity-40"
									disabled={currentPage === 1}
									on:click={() => goToPage(currentPage - 1)}
									aria-label="Page précédente"
								>
									‹ Préc.
								</button>
								{#each pages as p}
									{#if p === '…'}
										<span class="px-2 text-forest-400">…</span>
									{:else}
										<button
											class="h-9 min-w-9 rounded-lg px-2 text-sm font-medium transition"
											class:bg-forest-600={p === currentPage}
											class:text-white={p === currentPage}
											class:shadow-card={p === currentPage}
											class:bg-white={p !== currentPage}
											class:text-forest-700={p !== currentPage}
											class:hover:bg-forest-100={p !== currentPage}
											aria-current={p === currentPage ? 'page' : undefined}
											on:click={() => goToPage(p)}
										>
											{p}
										</button>
									{/if}
								{/each}
								<button
									class="btn-ghost px-3 text-sm disabled:cursor-not-allowed disabled:opacity-40"
									disabled={currentPage === totalPages}
									on:click={() => goToPage(currentPage + 1)}
									aria-label="Page suivante"
								>
									Suiv. ›
								</button>
							</div>
						</nav>
					{/if}
				{/if}
			</div>
		</div>

		{#if drawerOpen}
			<div class="fixed inset-0 z-50 flex lg:hidden" role="presentation">
				<button
					type="button"
					class="absolute inset-0 cursor-default bg-forest-950/40 backdrop-blur-sm"
					aria-label="Fermer les filtres"
					on:click={() => (drawerOpen = false)}
				></button>
				<div
					class="relative ml-auto flex h-full w-[min(360px,90vw)] flex-col gap-4 overflow-y-auto bg-white p-5 shadow-2xl"
					role="dialog"
					aria-modal="true"
					tabindex="-1"
				>
					<header class="flex items-center justify-between">
						<h2 class="font-display text-lg font-semibold text-forest-900">Filtres</h2>
						<button class="btn-ghost" on:click={() => (drawerOpen = false)}>Fermer</button>
					</header>
					<FilterSidebar
						{availableStatuts}
						totalCount={$mushrooms.length}
						visibleCount={$filtered.length}
					/>
				</div>
			</div>
		{/if}
	{/if}
</section>
