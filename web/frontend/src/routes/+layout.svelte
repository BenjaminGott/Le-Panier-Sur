<script lang="ts">
	import '../app.css';
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import SearchBar from '$lib/components/SearchBar.svelte';

	const links = [
		{ href: '/', label: 'Galerie' },
		{ href: '/astuces', label: 'Astuces' },
		{ href: '/stats', label: 'Statistiques' },
		{ href: '/predict', label: 'Identifier' }
	];

	$: currentPath = $page.url.pathname.replace(base, '') || '/';
</script>

<div class="flex min-h-screen flex-col">
	<header
		class="sticky top-0 z-30 border-b border-forest-100/80 bg-white/70 backdrop-blur-md"
	>
		<div class="mx-auto flex w-full max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
			<a href="{base}/" class="flex shrink-0 items-center gap-2">
				<span
					class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-forest-500 to-earth-600 text-lg shadow-card"
					aria-hidden="true">🍄</span
				>
				<div class="hidden flex-col leading-tight sm:flex">
					<span class="font-display text-base font-bold text-forest-900">Le Panier-Sûr</span>
					<span class="text-[0.65rem] uppercase tracking-widest text-forest-500"
						>Guide des champignons</span
					>
				</div>
			</a>

			<nav class="ml-2 hidden items-center gap-1 md:flex">
				{#each links as l}
					{@const active =
						l.href === '/' ? currentPath === '/' : currentPath.startsWith(l.href)}
					<a
						href="{base}{l.href}"
						class="rounded-lg px-3 py-1.5 text-sm font-medium transition"
						class:bg-forest-100={active}
						class:text-forest-900={active}
						class:text-forest-600={!active}
						class:hover:bg-forest-50={!active}
					>
						{l.label}
					</a>
				{/each}
			</nav>

			<div class="ml-auto"><SearchBar /></div>
		</div>

		<nav class="flex items-center justify-around border-t border-forest-100 px-2 py-1.5 md:hidden">
			{#each links as l}
				{@const active =
					l.href === '/' ? currentPath === '/' : currentPath.startsWith(l.href)}
				<a
					href="{base}{l.href}"
					class="rounded-lg px-3 py-1.5 text-xs font-medium transition"
					class:bg-forest-100={active}
					class:text-forest-900={active}
					class:text-forest-600={!active}
				>
					{l.label}
				</a>
			{/each}
		</nav>
	</header>

	<main class="flex-1">
		<slot />
	</main>

	<footer class="mt-12 border-t border-forest-100 bg-white/40">
		<div
			class="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-2 px-4 py-4 text-xs text-forest-600 sm:flex-row sm:px-6"
		>
			<p>Projet pédagogique — Ynov B3 SPE Data &amp; IA</p>
		</div>
	</footer>
</div>
