<script lang="ts">
	import { base } from '$app/paths';
	import type { Mushroom } from '$lib/data/types';
	import { dangerLevel } from '$lib/data/insights';
	import { presentKeysWithPrefix } from '$lib/data/loader';
	import StatusBadge from './StatusBadge.svelte';

	export let mushrooms: Mushroom[] = [];

	type QuizItem = {
		nom: string;
		hint: string;
	};

	const QUESTIONS: QuizItem[] = [
		{
			nom: 'AMANITE PHALLOÏDE',
			hint: "Indice : observe bien la base du pied et l'anneau."
		},
		{
			nom: 'CÈPE DE BORDEAUX',
			hint: "Indice : un classique des bois mixtes, avec des pores."
		},
		{
			nom: 'BOLET SATAN',
			hint: "Indice : la couleur des pores t'oriente très vite."
		},
		{
			nom: 'AGARIC DES JACHÈRES',
			hint: "Indice : sens-le. Que dit l'odeur ?"
		},
		{
			nom: 'AMANITE TUE-MOUCHES',
			hint: 'Indice : couleur ET pied — fais le tri.'
		}
	];

	$: items = QUESTIONS.map((q) => mushrooms.find((m) => m.nom === q.nom)).filter(
		(m): m is Mushroom => m !== undefined
	);

	let started = false;
	let currentIndex = 0;
	let answered = false;
	let lastCorrect = false;
	let answers: boolean[] = [];

	function start() {
		started = true;
		currentIndex = 0;
		answered = false;
		answers = [];
	}

	function answer(pickCueillir: boolean) {
		if (answered) return;
		const m = items[currentIndex];
		const correct = dangerLevel(m.statut) === 'safe';
		const isCorrect = pickCueillir === correct;
		lastCorrect = isCorrect;
		answers = [...answers, isCorrect];
		answered = true;
	}

	function next() {
		if (currentIndex < items.length - 1) {
			currentIndex++;
			answered = false;
		} else {
			currentIndex = items.length;
		}
	}

	function reset() {
		started = false;
		currentIndex = 0;
		answered = false;
		answers = [];
	}

	$: current = items[currentIndex];
	$: hint = QUESTIONS[currentIndex]?.hint ?? '';
	$: isFinished = started && currentIndex >= items.length;
	$: score = answers.filter((a) => a).length;

	function listFeatures(m: Mushroom) {
		const habitats = presentKeysWithPrefix(m, 'habitat_type_').slice(0, 4);
		const pied = presentKeysWithPrefix(m, 'pied_morpho_').slice(0, 4);
		const chapeauCol = presentKeysWithPrefix(m, 'chapeau_couleur_').slice(0, 3);
		const poresCol = presentKeysWithPrefix(m, 'pores_couleur_').slice(0, 2);
		const lamesCol = presentKeysWithPrefix(m, 'lames_couleur_').slice(0, 2);
		const odeur = presentKeysWithPrefix(m, 'odeur_type_').slice(0, 2);
		const saveur = presentKeysWithPrefix(m, 'saveur_type_').slice(0, 2);

		const sousChapeau =
			m.a_des_pores === true
				? `Pores${poresCol.length ? ' ' + poresCol.join('/') : ''}`
				: m.a_des_lames === true
					? `Lames${lamesCol.length ? ' ' + lamesCol.join('/') : ''}`
					: '—';

		const tailleC =
			typeof m.chapeau_taille_min_cm === 'number' && typeof m.chapeau_taille_max_cm === 'number'
				? `${m.chapeau_taille_min_cm}–${m.chapeau_taille_max_cm} cm`
				: '—';

		return [
			{ icon: '🌳', label: 'Habitat', value: habitats.length ? habitats.join(', ') : '—' },
			{ icon: '🎨', label: 'Couleurs du chapeau', value: chapeauCol.length ? chapeauCol.join(', ') : '—' },
			{ icon: '📏', label: 'Taille du chapeau', value: tailleC },
			{ icon: '🦠', label: 'Sous le chapeau', value: sousChapeau },
			{ icon: '🦴', label: 'Particularités du pied', value: pied.length ? pied.join(', ') : '—' },
			{ icon: '👃', label: 'Odeur', value: odeur.length ? odeur.join(', ') : '—' },
			{ icon: '👅', label: 'Saveur', value: saveur.length ? saveur.join(', ') : '—' }
		];
	}
</script>

<section class="card overflow-hidden">
	<header class="border-b border-forest-100 bg-gradient-to-br from-forest-50 to-earth-50 p-5">
		<div class="flex items-start gap-3">
			<span
				class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-forest-600 to-earth-700 text-xl text-white shadow-card"
				aria-hidden="true">🎯</span
			>
			<div>
				<h2 class="font-display text-xl font-bold text-forest-900 sm:text-2xl">
					Mode quizz : cueillir ou laisser ?
				</h2>
				<p class="mt-1 max-w-2xl text-sm text-forest-700">
					{items.length} cas concrets pour mettre en pratique le guide. Pour chaque champignon,
					applique les 7 étapes et décide.
				</p>
			</div>
		</div>
	</header>

	<div class="p-5">
		{#if !started}
			<div class="flex flex-col items-center gap-3 py-6 text-center">
				<p class="max-w-md text-sm text-forest-700">
					Le nom de l'espèce est caché. À toi d'analyser les indices et de décider si tu mets
					ce champignon dans ton panier ou si tu le laisses sur place.
				</p>
				<button
					type="button"
					on:click={start}
					class="rounded-xl bg-forest-700 px-5 py-2.5 font-display text-sm font-semibold text-white shadow-card transition hover:bg-forest-800 focus:outline-none focus:ring-2 focus:ring-forest-400"
				>
					Lancer le quizz →
				</button>
			</div>
		{:else if isFinished}
			<div class="flex flex-col items-center gap-4 py-6 text-center">
				<div
					class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-forest-500 to-earth-600 font-display text-3xl font-bold text-white shadow-card"
				>
					{score}/{items.length}
				</div>
				<div>
					<h3 class="font-display text-xl font-bold text-forest-900">
						{#if score === items.length}
							Sans-faute ! 🌟
						{:else if score >= items.length - 1}
							Excellent score !
						{:else if score >= Math.ceil(items.length / 2)}
							Pas mal — quelques étapes à réviser
						{:else}
							Reprends le guide tranquillement avant ta prochaine sortie
						{/if}
					</h3>
					<p class="mt-2 max-w-md text-sm text-forest-700">
						{#if score === items.length}
							Tu maîtrises les réflexes de base. Garde en tête qu'aucun guide ne remplace une
							identification formelle par un mycologue.
						{:else}
							Chaque erreur est une occasion d'affiner. Reviens sur les étapes liées aux
							critères que tu as mal interprétés.
						{/if}
					</p>
				</div>
				<button
					type="button"
					on:click={reset}
					class="rounded-xl bg-white px-5 py-2.5 font-display text-sm font-semibold text-forest-700 shadow-card ring-1 ring-forest-200 transition hover:bg-forest-50"
				>
					Recommencer
				</button>
			</div>
		{:else if current}
			<div class="grid gap-5 lg:grid-cols-[220px_1fr]">
				<div class="flex flex-col gap-2">
					<div class="relative aspect-[4/3] overflow-hidden rounded-xl bg-forest-100">
						{#if current.image}
							<img
								src="{base}{current.image}"
								alt={answered ? current.nom : 'Champignon mystère'}
								class="h-full w-full object-cover"
							/>
						{:else}
							<div class="flex h-full w-full items-center justify-center text-5xl text-forest-300">
								🍄
							</div>
						{/if}
						{#if !answered}
							<div
								class="absolute inset-0 flex items-end justify-center bg-gradient-to-t from-forest-900/60 via-transparent to-transparent p-3"
							>
								<span class="rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-forest-900">
									? mystère ?
								</span>
							</div>
						{/if}
					</div>
					<p class="text-center text-xs font-medium text-forest-500">
						Question {currentIndex + 1} / {items.length}
					</p>
				</div>

				<div class="flex flex-col gap-3">
					<div>
						<h3 class="section-title mb-2">Indices à observer</h3>
						<dl class="grid grid-cols-1 gap-1.5 text-sm sm:grid-cols-2">
							{#each listFeatures(current) as f}
								<div class="flex items-start gap-2 rounded-md border border-forest-100 bg-forest-50/40 p-2">
									<span class="text-base" aria-hidden="true">{f.icon}</span>
									<div class="min-w-0">
										<dt class="text-[0.65rem] font-semibold uppercase tracking-wider text-forest-500">
											{f.label}
										</dt>
										<dd class="text-xs text-forest-800">{f.value}</dd>
									</div>
								</div>
							{/each}
						</dl>
					</div>

					{#if !answered}
						<p class="text-xs italic text-forest-500">{hint}</p>
						<div class="flex flex-col gap-2 sm:flex-row">
							<button
								type="button"
								on:click={() => answer(true)}
								class="flex-1 rounded-xl bg-status-excellent px-4 py-3 font-display text-sm font-bold text-white shadow-card transition hover:brightness-110"
							>
								🍄 Cueillir
							</button>
							<button
								type="button"
								on:click={() => answer(false)}
								class="flex-1 rounded-xl bg-status-toxique px-4 py-3 font-display text-sm font-bold text-white shadow-card transition hover:brightness-110"
							>
								🚫 Laisser
							</button>
						</div>
					{:else}
						<div
							class="rounded-xl border p-3 {lastCorrect
								? 'border-status-excellent/40 bg-status-excellent/5'
								: 'border-status-toxique/40 bg-status-toxique/5'}"
						>
							<p class="font-display text-sm font-bold {lastCorrect ? 'text-status-excellent' : 'text-status-toxique'}">
								{lastCorrect ? '✓ Bonne réponse !' : '✗ Mauvaise réponse'}
							</p>
							<p class="mt-1.5 text-xs text-forest-800">
								Cette espèce est <strong>{current.nom}</strong> —
							</p>
							<div class="mt-1.5">
								<StatusBadge statut={current.statut} size="sm" />
							</div>
							<p class="mt-2 text-xs leading-snug text-forest-700">
								{#if dangerLevel(current.statut) === 'deadly'}
									⚠ Espèce <strong>mortelle</strong> — la bonne décision était de la <strong>laisser</strong>.
								{:else if dangerLevel(current.statut) === 'risky'}
									Espèce toxique ou à rejeter — à <strong>laisser</strong> sur place.
								{:else}
									Espèce comestible (selon le guide) — pouvait être <strong>cueillie</strong> par
									un cueilleur expérimenté.
								{/if}
							</p>
						</div>
						<button
							type="button"
							on:click={next}
							class="self-end rounded-xl bg-forest-700 px-5 py-2 font-display text-sm font-semibold text-white shadow-card transition hover:bg-forest-800"
						>
							{currentIndex < items.length - 1 ? 'Question suivante →' : 'Voir mon score →'}
						</button>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</section>
