<script lang="ts">
	import type { Mushroom } from '$lib/data/types';
	import { bucketize, splitBy, lift, type Bucket } from '$lib/data/insights';
	import type { GuideStep } from '$lib/data/guide';
	import StackedDangerBar from '$lib/components/charts/StackedDangerBar.svelte';
	import HabitatDangerBar from '$lib/components/charts/HabitatDangerBar.svelte';
	import SizeDistributionBar from '$lib/components/charts/SizeDistributionBar.svelte';
	import MushroomMiniCard from '$lib/components/MushroomMiniCard.svelte';

	export let step: GuideStep;
	export let mushrooms: Mushroom[] = [];

	$: baseline = bucketize(mushrooms, 'Base : ensemble du dataset');

	$: buckets = (() => {
		const out: Bucket[] = [baseline];
		for (const p of step.predicates) {
			const split = splitBy(mushrooms, p);
			out.push({ ...split.with, label: `Avec ${p.label}` });
		}
		return out;
	})();

	$: highlights = step.predicates.map((p) => {
		const split = splitBy(mushrooms, p);
		return {
			label: p.label,
			n: split.with.total,
			liftDeadly: lift(split, 'deadly'),
			liftRisky: lift(split, 'risky'),
			pctDanger: split.with.pctRisky + split.with.pctDeadly,
			pctSafe: split.with.pctSafe
		};
	});

	$: especesMatched = step.especes
		.map((nom) => mushrooms.find((m) => m.nom === nom))
		.filter((m): m is Mushroom => m !== undefined);
</script>

<article class="card overflow-hidden">
	<header class="flex items-start gap-4 border-b border-forest-100 p-5">
		<div class="flex shrink-0 flex-col items-center">
			<span
				class="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-forest-600 to-earth-700 font-display text-xl font-bold text-white shadow-card"
			>
				{step.numero.toString().padStart(2, '0')}
			</span>
			<span class="mt-1 text-[0.65rem] font-semibold uppercase tracking-wider text-forest-500">
				Étape
			</span>
		</div>
		<div class="flex-1">
			<div class="flex items-center gap-2">
				<span aria-hidden="true" class="text-xl">{step.icon}</span>
				<h2 class="font-display text-xl font-bold text-forest-900 sm:text-2xl">
					{step.titre}
				</h2>
			</div>
			<p class="mt-0.5 text-sm font-medium text-earth-700">{step.sousTitre}</p>
			<p class="mt-2 max-w-2xl text-sm leading-relaxed text-forest-700">
				{step.intro}
			</p>
		</div>
	</header>

	<div class="grid gap-5 p-5 lg:grid-cols-[1fr_280px]">
		<div>
			<h3 class="section-title mb-2">
				{#if step.chart === 'habitat'}
					Habitats classés du moins risqué au plus risqué
				{:else if step.chart === 'size'}
					Distribution des tailles de chapeau par niveau de danger
				{:else}
					Répartition par danger (en %)
				{/if}
			</h3>
			<div class="h-[320px]">
				{#if step.chart === 'habitat'}
					<HabitatDangerBar {mushrooms} />
				{:else if step.chart === 'size'}
					<SizeDistributionBar {mushrooms} />
				{:else}
					<StackedDangerBar {buckets} />
				{/if}
			</div>
		</div>

		{#if highlights.length > 0}
			<aside class="flex flex-col gap-2">
				<h3 class="section-title">Indicateurs clés</h3>
				{#each highlights as h}
					<div class="rounded-lg border border-forest-100 bg-forest-50/50 p-3 text-xs">
						<p class="font-semibold text-forest-900">{h.label}</p>
						<p class="text-forest-600">n = {h.n} espèces</p>
						<dl class="mt-1.5 grid grid-cols-2 gap-1">
							<dt class="text-forest-500">% dangereux</dt>
							<dd class="text-right font-mono font-semibold text-status-toxique">
								{h.pctDanger.toFixed(0)}%
							</dd>
							<dt class="text-forest-500">×risque mortel</dt>
							<dd
								class="text-right font-mono font-semibold"
								class:text-status-mortel={h.liftDeadly >= 1.5}
								class:text-forest-700={h.liftDeadly < 1.5}
							>
								{h.liftDeadly.toFixed(1)}×
							</dd>
						</dl>
					</div>
				{/each}
				<p class="text-[0.65rem] italic leading-snug text-forest-500">
					Lecture : un « ×risque » de 2.0 signifie que le risque est doublé par rapport à la
					moyenne du dataset.
				</p>
			</aside>
		{:else}
			<aside class="flex flex-col gap-2">
				<h3 class="section-title">Lecture du graphique</h3>
				<div class="rounded-lg border border-forest-100 bg-forest-50/50 p-3 text-xs leading-snug text-forest-700">
					<p>
						Chaque barre représente un habitat avec son nombre d'espèces (<code>n=</code>) et
						la part d'espèces dangereuses (toxiques, à rejeter ou mortelles).
					</p>
					<p class="mt-2">
						Plus la barre est <strong class="text-status-toxique">rouge et longue</strong>,
						plus l'habitat concentre d'espèces dangereuses.
					</p>
				</div>
			</aside>
		{/if}
	</div>

	{#if especesMatched.length > 0}
		<div class="border-t border-forest-100 p-5">
			<h3 class="section-title mb-3">Espèces emblématiques de cette étape</h3>
			<div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
				{#each especesMatched as m (m.slug)}
					<MushroomMiniCard mushroom={m} />
				{/each}
			</div>
		</div>
	{/if}

	<div class="grid gap-4 border-t border-forest-100 p-5 sm:grid-cols-2">
		<div class="rounded-xl border border-status-excellent/30 bg-status-excellent/5 p-4">
			<h3 class="mb-2 flex items-center gap-1.5 font-display text-sm font-bold text-status-excellent">
				<span aria-hidden="true">✓</span> À faire
			</h3>
			<ul class="flex flex-col gap-1.5 text-sm leading-snug text-forest-800">
				{#each step.aFaire as item}
					<li class="flex gap-1.5">
						<span class="text-status-excellent" aria-hidden="true">•</span>
						<span>{item}</span>
					</li>
				{/each}
			</ul>
		</div>

		<div class="rounded-xl border border-status-toxique/30 bg-status-toxique/5 p-4">
			<h3 class="mb-2 flex items-center gap-1.5 font-display text-sm font-bold text-status-toxique">
				<span aria-hidden="true">✗</span> À éviter
			</h3>
			<ul class="flex flex-col gap-1.5 text-sm leading-snug text-forest-800">
				{#each step.aEviter as item}
					<li class="flex gap-1.5">
						<span class="text-status-toxique" aria-hidden="true">•</span>
						<span>{item}</span>
					</li>
				{/each}
			</ul>
		</div>
	</div>

	<footer class="border-t border-forest-100 bg-forest-50/40 p-5 text-sm leading-relaxed text-forest-800">
		<p>
			<span class="font-display font-semibold text-forest-900">À retenir —</span>
			{step.conclusion}
		</p>
	</footer>
</article>
