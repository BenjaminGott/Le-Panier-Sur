<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { loadMushrooms } from '$lib/data/loader';
	import type { Mushroom } from '$lib/data/types';
	import { GUIDE_STEPS } from '$lib/data/guide';
	import GuideStep from '$lib/components/GuideStep.svelte';
	import GuideQuiz from '$lib/components/GuideQuiz.svelte';

	let mushrooms: Mushroom[] = [];
	let loading = true;
	let activeId = GUIDE_STEPS[0]?.id ?? '';

	let observer: IntersectionObserver | null = null;
	const visibleRatios = new Map<string, number>();

	onMount(async () => {
		mushrooms = await loadMushrooms();
		loading = false;
		await tick();

		observer = new IntersectionObserver(
			(entries) => {
				for (const e of entries) {
					const id = e.target.id.replace('step-', '');
					if (e.isIntersecting) visibleRatios.set(id, e.intersectionRatio);
					else visibleRatios.delete(id);
				}
				let best = '';
				let bestR = 0;
				for (const [id, r] of visibleRatios) {
					if (r > bestR) {
						bestR = r;
						best = id;
					}
				}
				if (best) activeId = best;
			},
			{ rootMargin: '-20% 0px -60% 0px', threshold: [0, 0.25, 0.5, 0.75, 1] }
		);

		for (const s of GUIDE_STEPS) {
			const el = document.getElementById(`step-${s.id}`);
			if (el) observer.observe(el);
		}
	});

	onDestroy(() => observer?.disconnect());

	function jumpTo(id: string) {
		activeId = id;
		const el = document.getElementById(`step-${id}`);
		if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	$: currentIdx = Math.max(
		0,
		GUIDE_STEPS.findIndex((s) => s.id === activeId)
	);
	$: progressNum = currentIdx + 1;
	$: progressPct = (progressNum / GUIDE_STEPS.length) * 100;
	$: currentTitle = GUIDE_STEPS[currentIdx]?.titre ?? '';
</script>

<svelte:head>
	<title>Guide pas à pas — Le Panier-Sûr</title>
</svelte:head>

{#if !loading}
	<div
		class="sticky top-14 z-20 border-b border-forest-100 bg-white/85 backdrop-blur-md sm:top-16"
		role="status"
		aria-live="polite"
	>
		<div class="mx-auto flex w-full max-w-6xl items-center gap-3 px-4 py-2.5 sm:px-6">
			<span class="shrink-0 font-mono text-xs font-bold text-forest-800">
				Étape {progressNum} / {GUIDE_STEPS.length}
			</span>
			<div class="h-2 flex-1 overflow-hidden rounded-full bg-forest-100">
				<div
					class="h-full rounded-full bg-gradient-to-r from-forest-500 to-earth-600 transition-all duration-500 ease-out"
					style="width: {progressPct}%"
				></div>
			</div>
			<span class="hidden truncate text-xs font-medium text-forest-700 sm:inline">
				{currentTitle}
			</span>
		</div>
	</div>
{/if}

<section class="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:py-10">
	<header class="mb-8 max-w-3xl">
		<p class="section-title">Apprendre des données</p>
		<h1 class="mt-1 font-display text-3xl font-bold text-forest-900 sm:text-4xl">
			Guide pas à pas du cueilleur
		</h1>
		<p class="mt-3 text-sm text-forest-700 sm:text-base">
			Sept étapes pour devenir un meilleur cueilleur, basées sur l'analyse statistique de
			<strong>{mushrooms.length || '…'}</strong> espèces du guide. Chaque étape t'apprend
			un réflexe à acquérir et te montre, chiffres à l'appui, pourquoi ce critère oriente vers
			la sécurité ou le danger.
		</p>
		<div class="mt-4 inline-flex items-center gap-2 rounded-full bg-forest-100 px-3 py-1.5 text-xs font-medium text-forest-700">
			<span aria-hidden="true">📊</span>
			Toutes les statistiques sont calculées en direct sur le dataset
		</div>
	</header>

	{#if loading}
		<p class="text-forest-600">Chargement…</p>
	{:else}
		<div class="flex gap-8">
			<nav
				class="card sticky top-32 hidden h-fit w-64 shrink-0 self-start p-4 lg:block"
				aria-label="Sommaire"
			>
				<h2 class="section-title mb-2">Parcours</h2>
				<ol class="flex flex-col gap-1">
					{#each GUIDE_STEPS as s}
						<li>
							<button
								type="button"
								on:click={() => jumpTo(s.id)}
								aria-current={activeId === s.id ? 'step' : undefined}
								class="flex w-full items-start gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition"
								class:bg-forest-100={activeId === s.id}
								class:text-forest-900={activeId === s.id}
								class:hover:bg-forest-50={activeId !== s.id}
								class:text-forest-700={activeId !== s.id}
							>
								<span
									class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full font-mono text-[0.7rem] font-bold transition"
									class:bg-forest-700={activeId === s.id}
									class:text-white={activeId === s.id}
									class:bg-forest-200={activeId !== s.id}
									class:text-forest-700={activeId !== s.id}
								>
									{s.numero}
								</span>
								<span class="leading-tight">{s.titre}</span>
							</button>
						</li>
					{/each}
				</ol>
				<div class="mt-4 rounded-lg border border-status-toxique/20 bg-status-toxique/5 p-3 text-[0.7rem] leading-snug text-earth-900">
					⚠ Aucun de ces critères pris isolément ne suffit. Les statistiques aident à
					orienter, jamais à conclure.
				</div>
			</nav>

			<div class="flex-1 space-y-8">
				{#each GUIDE_STEPS as s, i (s.id)}
					<div id="step-{s.id}" class="scroll-mt-32">
						<p class="mb-2 text-xs font-semibold uppercase tracking-wider text-forest-500">
							Étape {i + 1} / {GUIDE_STEPS.length}
						</p>
						<GuideStep step={s} {mushrooms} />
					</div>
				{/each}

				<div id="quiz" class="scroll-mt-32">
					<p class="mb-2 text-xs font-semibold uppercase tracking-wider text-forest-500">
						Mise en pratique
					</p>
					<GuideQuiz {mushrooms} />
				</div>

				<div class="card border-2 border-dashed border-forest-200 bg-forest-50/30 p-6 text-center">
					<p class="text-sm font-medium text-forest-800">
						🍄 Tu as terminé le guide. Mets-le en pratique avec l'outil
						<a href="/predict" class="font-semibold text-forest-700 underline hover:text-forest-900">
							Identifier
						</a>
						et garde toujours en tête : au moindre doute, on ne mange pas.
					</p>
				</div>
			</div>
		</div>
	{/if}
</section>
