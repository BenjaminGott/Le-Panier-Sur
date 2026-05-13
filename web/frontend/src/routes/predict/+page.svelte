<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { loadMushrooms } from '$lib/data/loader';
	import { COULEURS, COULEUR_HEX, HABITATS } from '$lib/data/types';
	import type { Mushroom } from '$lib/data/types';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import SectionStatus from '$lib/components/SectionStatus.svelte';
	import { checkAvailability, predict } from '$lib/ml/predictor';
	import {
		predictForm,
		predictResults,
		resetPredictForm,
		type Porteur
	} from '$lib/stores/predict';

	let mushrooms: Mushroom[] = [];
	let availability: { available: boolean; reason?: string } = { available: false };
	let loading = true;

	const PORTEUR_OPTIONS: { v: Porteur; l: string }[] = [
		{ v: 'lames', l: 'Lames' },
		{ v: 'pores', l: 'Pores' },
		{ v: 'aucun', l: 'Aucun' }
	];

	// Textures / morpho / attaches / consistance / odeur / saveur
	const TEXTURES_CHAPEAU = [
		'lisse', 'meches', 'floconneux', 'visqueux', 'velours', 'ecailleux', 'craquele', 'strie'
	];
	const TEXTURES_PIED = [
		'lisse', 'meches', 'floconneux', 'visqueux', 'velours', 'ecailleux', 'craquele', 'strie'
	];
	const MORPHOS = [
		'anneau', 'volve', 'bulbe', 'massue', 'creux', 'elance', 'cylindrique', 'reseau'
	];
	const ATTACHES = [
		'libres', 'adnees', 'decurrentes', 'echancrees', 'serrees', 'espacees'
	];
	const CONSISTANCES = [
		'ferme', 'tendre', 'molle', 'cassante', 'elastique', 'epaisse', 'fibreuse', 'spongieuse'
	];
	const ODEURS = [
		'anise', 'phenol', 'iode', 'radis', 'farine', 'amande', 'terre', 'fruitee', 'desagreable'
	];
	const SAVEURS = [
		'douce', 'amere', 'acide', 'piquante', 'poivree', 'iodee', 'desagreable', 'sans_saveur'
	];

	const MOIS_LABELS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];

	let busy = false;
	let predError = '';

	onMount(async () => {
		[mushrooms, availability] = await Promise.all([loadMushrooms(), checkAvailability()]);
		loading = false;
	});

	/** Applique le principe : section vide → NaN (laissée hors du dict),
	 * section avec sélection → 0/1 explicites pour TOUTES les options du domaine. */
	function fillSection(
		v: Record<string, number>,
		prefix: string,
		domain: readonly string[],
		selected: string[]
	) {
		if (selected.length === 0) return; // unknown → NaN
		for (const opt of domain) {
			v[`${prefix}${opt}`] = selected.includes(opt) ? 1 : 0;
		}
	}

	const ATTACHE_DOMAIN = ATTACHES;
	const TEX_CHAPEAU_DOMAIN = TEXTURES_CHAPEAU;
	const TEX_PIED_DOMAIN = TEXTURES_PIED;
	const MORPHO_DOMAIN = MORPHOS;
	const CONSIST_DOMAIN = CONSISTANCES;
	const ODEUR_DOMAIN = ODEURS;
	const SAVEUR_DOMAIN = SAVEURS;
	const HABITAT_DOMAIN = HABITATS as readonly string[];
	const COULEUR_DOMAIN = COULEURS as readonly string[];
	const MOIS_DOMAIN = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];

	function buildValues(): Record<string, number> {
		const f = $predictForm;
		const a_des_lames = f.porteur === 'lames';
		const a_des_pores = f.porteur === 'pores';
		const v: Record<string, number> = {
			chapeau_taille_cm: f.chapeau_taille_cm,
			pied_taille_cm: f.a_un_pied ? f.pied_taille_cm : 0,
			a_un_chapeau: f.a_un_chapeau ? 1 : 0,
			a_des_pores: a_des_pores ? 1 : 0,
			a_des_lames: a_des_lames ? 1 : 0,
			a_un_pied: f.a_un_pied ? 1 : 0,
			a_de_la_chair: f.a_de_la_chair ? 1 : 0
		};
		if (f.a_un_chapeau) {
			fillSection(v, 'chapeau_couleur_', COULEUR_DOMAIN, f.chapeauCouleurs);
			fillSection(v, 'chapeau_texture_', TEX_CHAPEAU_DOMAIN, f.chapeauTextures);
		}
		if (a_des_lames) {
			fillSection(v, 'lames_couleur_', COULEUR_DOMAIN, f.lamesCouleurs);
			fillSection(v, 'lames_attache_', ATTACHE_DOMAIN, f.lamesAttaches);
		}
		if (a_des_pores) {
			fillSection(v, 'pores_couleur_', COULEUR_DOMAIN, f.poresCouleurs);
			fillSection(v, 'pores_attache_', ATTACHE_DOMAIN, f.poresAttaches);
		}
		if (f.a_un_pied) {
			fillSection(v, 'pied_couleur_', COULEUR_DOMAIN, f.piedCouleurs);
			fillSection(v, 'pied_texture_', TEX_PIED_DOMAIN, f.piedTextures);
			fillSection(v, 'pied_morpho_', MORPHO_DOMAIN, f.piedMorpho);
		}
		if (f.a_de_la_chair) {
			fillSection(v, 'chair_couleur_', COULEUR_DOMAIN, f.chairCouleurs);
			fillSection(v, 'chair_consistance_', CONSIST_DOMAIN, f.chairConsistance);
		}
		fillSection(v, 'odeur_type_', ODEUR_DOMAIN, f.odeur);
		fillSection(v, 'saveur_type_', SAVEUR_DOMAIN, f.saveur);
		fillSection(v, 'habitat_type_', HABITAT_DOMAIN, f.habitats);
		fillSection(
			v,
			'saison_mois_',
			MOIS_DOMAIN,
			f.mois.map((m) => m.toString().padStart(2, '0'))
		);
		return v;
	}

	function reset() {
		resetPredictForm();
		predError = '';
	}

	function toggleField(field: keyof typeof $predictForm, v: string | number) {
		predictForm.update((f) => {
			const arr = f[field] as (string | number)[];
			const next = arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
			return { ...f, [field]: next };
		});
	}

	async function runPredict() {
		predError = '';
		predictResults.set(null);
		busy = true;
		try {
			const result = await predict(buildValues(), 5);
			predictResults.set(result);
		} catch (e) {
			predError = String(e);
		} finally {
			busy = false;
		}
	}

	function findMushroom(nom: string): Mushroom | undefined {
		return mushrooms.find((m) => m.nom.toUpperCase() === nom.toUpperCase());
	}
</script>

<svelte:head>
	<title>Identifier — Le Panier-Sûr</title>
</svelte:head>

<section class="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:py-10">
	<header class="mb-6">
		<p class="section-title">Aide à l'identification</p>
		<h1 class="font-display text-3xl font-bold text-forest-900 sm:text-4xl">
			Identifier un champignon
		</h1>
		<p class="mt-2 max-w-2xl text-sm text-forest-700">
			Décris ce que tu observes — <strong>laisse vide ce que tu ignores</strong>. Le modèle
			XGBoost propose les espèces les plus probables. <em>Cet outil ne remplace pas l'avis d'un
				mycologue.</em>
		</p>
		<div
			class="mt-3 max-w-2xl rounded-xl border border-forest-200 bg-forest-50/70 p-3 text-xs text-forest-800"
		>
			<p class="font-semibold">Comment le modèle interprète tes choix :</p>
			<ul class="mt-1 space-y-0.5 leading-relaxed">
				<li>
					<span class="chip bg-forest-600 px-1.5 py-0 text-[0.65rem] text-white">Observé</span>
					au moins 1 sélection dans la section ⇒ les autres options sont marquées
					<strong>absentes</strong>.
				</li>
				<li>
					<span class="chip bg-forest-100 px-1.5 py-0 text-[0.65rem] text-forest-700"
						>Inconnu</span
					>
					section vide ⇒ ignorée par le modèle (mieux que de mentir avec des « non »).
				</li>
			</ul>
		</div>
	</header>

	{#if loading}
		<p class="text-forest-600">Chargement…</p>
	{:else}
		{#if !availability.available}
			<div class="card mb-6 border border-ocher-300 bg-ocher-50 p-5 text-sm text-earth-900">
				<p class="font-semibold">Le modèle ONNX n'est pas encore disponible.</p>
				<p class="mt-1 text-earth-700">{availability.reason ?? ''}</p>
				<pre class="mt-3 overflow-x-auto rounded-lg bg-earth-900/90 p-3 text-xs text-ocher-100">cd web/frontend
python scripts/export_onnx.py</pre>
			</div>
		{/if}

		<div class="grid gap-6 lg:grid-cols-[1fr_360px]">
			<div class="space-y-5">
				<!-- Anatomie -->
				<div class="card p-5">
					<h2 class="mb-3 font-display text-lg font-semibold text-forest-900">Anatomie</h2>
					<div class="grid gap-3 sm:grid-cols-2">
						<label class="flex items-center gap-2 text-sm text-forest-800">
							<input type="checkbox" bind:checked={$predictForm.a_un_chapeau} class="h-4 w-4 accent-forest-600" />
							A un chapeau
						</label>
						<label class="flex items-center gap-2 text-sm text-forest-800">
							<input type="checkbox" bind:checked={$predictForm.a_un_pied} class="h-4 w-4 accent-forest-600" />
							A un pied
						</label>
						<label class="flex items-center gap-2 text-sm text-forest-800">
							<input type="checkbox" bind:checked={$predictForm.a_de_la_chair} class="h-4 w-4 accent-forest-600" />
							A de la chair
						</label>
					</div>
					<div class="mt-3">
						<p class="section-title mb-1.5">Sous le chapeau</p>
						<div class="flex flex-wrap gap-1.5">
							{#each PORTEUR_OPTIONS as opt (opt.v)}
								{@const sel = $predictForm.porteur === opt.v}
								<button
									type="button"
									on:click={() => predictForm.update((f) => ({ ...f, porteur: opt.v }))}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{opt.l}
								</button>
							{/each}
						</div>
					</div>
				</div>

				<!-- Tailles -->
				<div class="card p-5">
					<h2 class="mb-3 font-display text-lg font-semibold text-forest-900">Tailles</h2>
					<div class="grid gap-4 sm:grid-cols-2">
						{#if $predictForm.a_un_chapeau}
							<label class="text-sm">
								<span class="section-title"
									>Chapeau : <strong>{$predictForm.chapeau_taille_cm} cm</strong></span
								>
								<input
									type="range"
									min="1"
									max="40"
									bind:value={$predictForm.chapeau_taille_cm}
									class="mt-2 w-full"
								/>
							</label>
						{/if}
						{#if $predictForm.a_un_pied}
							<label class="text-sm">
								<span class="section-title"
									>Pied : <strong>{$predictForm.pied_taille_cm} cm</strong></span
								>
								<input
									type="range"
									min="1"
									max="30"
									bind:value={$predictForm.pied_taille_cm}
									class="mt-2 w-full"
								/>
							</label>
						{/if}
					</div>
				</div>

				<!-- Chapeau -->
				{#if $predictForm.a_un_chapeau}
					<div class="card p-5">
						<header class="mb-3 flex items-center justify-between gap-2">
							<h2 class="font-display text-lg font-semibold text-forest-900">🍄 Chapeau</h2>
							<SectionStatus
								observed={$predictForm.chapeauCouleurs.length > 0 ||
									$predictForm.chapeauTextures.length > 0}
							/>
						</header>
						<p class="section-title mb-1.5">Couleurs</p>
						<div class="mb-4 flex flex-wrap gap-1.5">
							{#each COULEURS as c}
								{@const sel = $predictForm.chapeauCouleurs.includes(c)}
								<button
									type="button"
									title={c}
									aria-label={c}
									on:click={() => toggleField('chapeauCouleurs', c)}
									class="h-7 w-7 rounded-full border-2 transition"
									class:border-forest-700={sel}
									class:scale-110={sel}
									class:border-white={!sel}
									style="background-color: {COULEUR_HEX[c]}"
								></button>
							{/each}
						</div>
						<p class="section-title mb-1.5">Texture</p>
						<div class="flex flex-wrap gap-1.5">
							{#each TEXTURES_CHAPEAU as t}
								{@const sel = $predictForm.chapeauTextures.includes(t)}
								<button
									type="button"
									on:click={() => toggleField('chapeauTextures', t)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{t}
								</button>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Lames -->
				{#if $predictForm.porteur === 'lames'}
					<div class="card p-5">
						<header class="mb-3 flex items-center justify-between gap-2">
							<h2 class="font-display text-lg font-semibold text-forest-900">🌿 Lames</h2>
							<SectionStatus
								observed={$predictForm.lamesCouleurs.length > 0 ||
									$predictForm.lamesAttaches.length > 0}
							/>
						</header>
						<p class="section-title mb-1.5">Couleurs</p>
						<div class="mb-4 flex flex-wrap gap-1.5">
							{#each COULEURS as c}
								{@const sel = $predictForm.lamesCouleurs.includes(c)}
								<button
									type="button"
									title={c}
									aria-label={c}
									on:click={() => toggleField('lamesCouleurs', c)}
									class="h-7 w-7 rounded-full border-2 transition"
									class:border-forest-700={sel}
									class:scale-110={sel}
									class:border-white={!sel}
									style="background-color: {COULEUR_HEX[c]}"
								></button>
							{/each}
						</div>
						<p class="section-title mb-1.5">Attaches</p>
						<div class="flex flex-wrap gap-1.5">
							{#each ATTACHES as a}
								{@const sel = $predictForm.lamesAttaches.includes(a)}
								<button
									type="button"
									on:click={() => toggleField('lamesAttaches', a)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{a}
								</button>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Pores -->
				{#if $predictForm.porteur === 'pores'}
					<div class="card p-5">
						<header class="mb-3 flex items-center justify-between gap-2">
							<h2 class="font-display text-lg font-semibold text-forest-900">• Pores</h2>
							<SectionStatus
								observed={$predictForm.poresCouleurs.length > 0 ||
									$predictForm.poresAttaches.length > 0}
							/>
						</header>
						<p class="section-title mb-1.5">Couleurs</p>
						<div class="mb-4 flex flex-wrap gap-1.5">
							{#each COULEURS as c}
								{@const sel = $predictForm.poresCouleurs.includes(c)}
								<button
									type="button"
									title={c}
									aria-label={c}
									on:click={() => toggleField('poresCouleurs', c)}
									class="h-7 w-7 rounded-full border-2 transition"
									class:border-forest-700={sel}
									class:scale-110={sel}
									class:border-white={!sel}
									style="background-color: {COULEUR_HEX[c]}"
								></button>
							{/each}
						</div>
						<p class="section-title mb-1.5">Attaches</p>
						<div class="flex flex-wrap gap-1.5">
							{#each ATTACHES as a}
								{@const sel = $predictForm.poresAttaches.includes(a)}
								<button
									type="button"
									on:click={() => toggleField('poresAttaches', a)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{a}
								</button>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Pied -->
				{#if $predictForm.a_un_pied}
					<div class="card p-5">
						<header class="mb-3 flex items-center justify-between gap-2">
							<h2 class="font-display text-lg font-semibold text-forest-900">🌱 Pied</h2>
							<SectionStatus
								observed={$predictForm.piedCouleurs.length > 0 ||
									$predictForm.piedTextures.length > 0 ||
									$predictForm.piedMorpho.length > 0}
							/>
						</header>
						<p class="section-title mb-1.5">Couleur</p>
						<div class="mb-4 flex flex-wrap gap-1.5">
							{#each COULEURS as c}
								{@const sel = $predictForm.piedCouleurs.includes(c)}
								<button
									type="button"
									title={c}
									aria-label={c}
									on:click={() => toggleField('piedCouleurs', c)}
									class="h-7 w-7 rounded-full border-2 transition"
									class:border-forest-700={sel}
									class:scale-110={sel}
									class:border-white={!sel}
									style="background-color: {COULEUR_HEX[c]}"
								></button>
							{/each}
						</div>
						<p class="section-title mb-1.5">Texture</p>
						<div class="mb-4 flex flex-wrap gap-1.5">
							{#each TEXTURES_PIED as t}
								{@const sel = $predictForm.piedTextures.includes(t)}
								<button
									type="button"
									on:click={() => toggleField('piedTextures', t)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{t}
								</button>
							{/each}
						</div>
						<p class="section-title mb-1.5">Morphologie</p>
						<div class="flex flex-wrap gap-1.5">
							{#each MORPHOS as t}
								{@const sel = $predictForm.piedMorpho.includes(t)}
								<button
									type="button"
									on:click={() => toggleField('piedMorpho', t)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{t}
								</button>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Chair -->
				{#if $predictForm.a_de_la_chair}
					<div class="card p-5">
						<header class="mb-3 flex items-center justify-between gap-2">
							<h2 class="font-display text-lg font-semibold text-forest-900">🥩 Chair</h2>
							<SectionStatus
								observed={$predictForm.chairCouleurs.length > 0 ||
									$predictForm.chairConsistance.length > 0}
							/>
						</header>
						<p class="section-title mb-1.5">Couleur</p>
						<div class="mb-4 flex flex-wrap gap-1.5">
							{#each COULEURS as c}
								{@const sel = $predictForm.chairCouleurs.includes(c)}
								<button
									type="button"
									title={c}
									aria-label={c}
									on:click={() => toggleField('chairCouleurs', c)}
									class="h-7 w-7 rounded-full border-2 transition"
									class:border-forest-700={sel}
									class:scale-110={sel}
									class:border-white={!sel}
									style="background-color: {COULEUR_HEX[c]}"
								></button>
							{/each}
						</div>
						<p class="section-title mb-1.5">Consistance</p>
						<div class="flex flex-wrap gap-1.5">
							{#each CONSISTANCES as t}
								{@const sel = $predictForm.chairConsistance.includes(t)}
								<button
									type="button"
									on:click={() => toggleField('chairConsistance', t)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{t}
								</button>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Odeur / Saveur -->
				<div class="grid gap-5 sm:grid-cols-2">
					<div class="card p-5">
						<header class="mb-3 flex items-center justify-between gap-2">
							<h2 class="font-display text-lg font-semibold text-forest-900">👃 Odeur</h2>
							<SectionStatus observed={$predictForm.odeur.length > 0} />
						</header>
						<div class="flex flex-wrap gap-1.5">
							{#each ODEURS as t}
								{@const sel = $predictForm.odeur.includes(t)}
								<button
									type="button"
									on:click={() => toggleField('odeur', t)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{t}
								</button>
							{/each}
						</div>
					</div>
					<div class="card p-5">
						<header class="mb-3 flex items-center justify-between gap-2">
							<h2 class="font-display text-lg font-semibold text-forest-900">👅 Saveur</h2>
							<SectionStatus observed={$predictForm.saveur.length > 0} />
						</header>
						<div class="flex flex-wrap gap-1.5">
							{#each SAVEURS as t}
								{@const sel = $predictForm.saveur.includes(t)}
								<button
									type="button"
									on:click={() => toggleField('saveur', t)}
									class="chip border text-xs transition"
									class:bg-forest-600={sel}
									class:text-white={sel}
									class:bg-white={!sel}
									class:border-forest-200={!sel}
									class:text-forest-700={!sel}
								>
									{t.replace(/_/g, ' ')}
								</button>
							{/each}
						</div>
					</div>
				</div>

				<!-- Habitat -->
				<div class="card p-5">
					<header class="mb-3 flex items-center justify-between gap-2">
						<h2 class="font-display text-lg font-semibold text-forest-900">🌳 Habitat</h2>
						<SectionStatus observed={$predictForm.habitats.length > 0} />
					</header>
					<div class="flex flex-wrap gap-1.5">
						{#each HABITATS as h}
							{@const sel = $predictForm.habitats.includes(h)}
							<button
								type="button"
								on:click={() => toggleField('habitats', h)}
								class="chip border text-xs transition"
								class:bg-forest-600={sel}
								class:text-white={sel}
								class:bg-white={!sel}
								class:border-forest-200={!sel}
								class:text-forest-700={!sel}
							>
								{h.replace(/_/g, ' ')}
							</button>
						{/each}
					</div>
				</div>

				<!-- Saison -->
				<div class="card p-5">
					<header class="mb-3 flex items-center justify-between gap-2">
						<h2 class="font-display text-lg font-semibold text-forest-900">📅 Saison</h2>
						<SectionStatus observed={$predictForm.mois.length > 0} />
					</header>
					<div class="grid grid-cols-12 gap-1">
						{#each MOIS_LABELS as m, i}
							{@const month = i + 1}
							{@const sel = $predictForm.mois.includes(month)}
							<button
								type="button"
								on:click={() => toggleField('mois', month)}
								class="rounded-md py-1.5 text-[0.7rem] font-medium transition"
								class:bg-forest-600={sel}
								class:text-white={sel}
								class:bg-white={!sel}
								class:text-forest-700={!sel}
							>
								{m}
							</button>
						{/each}
					</div>
				</div>
			</div>

			<aside class="space-y-3 lg:sticky lg:top-24 lg:self-start">
				<button
					class="btn-primary w-full py-3 text-base disabled:cursor-not-allowed disabled:opacity-60"
					disabled={busy || !availability.available}
					on:click={runPredict}
				>
					{#if busy}Analyse…{:else}Identifier 🔍{/if}
				</button>
				<button class="btn-ghost w-full text-sm" on:click={reset}>Réinitialiser</button>

				{#if predError}
					<div class="card border border-red-200 bg-red-50 p-4 text-sm text-red-800">
						{predError}
					</div>
				{/if}

				{#if $predictResults}
					<div class="card p-5">
						<h2 class="mb-3 font-display text-lg font-semibold text-forest-900">
							Top 5 espèces probables
						</h2>
						<ol class="space-y-3">
							{#each $predictResults as p, i}
								{@const m = findMushroom(p.espece)}
								<li>
									<a
										href={m ? `${base}/champignon/${m.slug}` : '#'}
										class="flex items-center gap-3 rounded-xl border border-forest-100 p-2 transition hover:bg-forest-50"
									>
										<span
											class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-forest-600 text-xs font-bold text-white"
											>{i + 1}</span
										>
										{#if m?.image}
											<img
												src="{base}{m.image}"
												alt={p.espece}
												class="h-10 w-10 rounded-lg object-cover"
											/>
										{/if}
										<div class="flex-1 min-w-0">
											<p class="truncate text-sm font-semibold text-forest-900">
												{p.espece}
											</p>
											<div class="mt-0.5 flex items-center gap-2">
												{#if m?.statut}<StatusBadge statut={m.statut} />{/if}
												<span class="text-xs text-forest-600"
													>{(p.confiance * 100).toFixed(1)} %</span
												>
											</div>
										</div>
									</a>
								</li>
							{/each}
						</ol>
						<p class="mt-3 text-[0.7rem] italic text-forest-500">
							⚠ Outil indicatif — ne consomme jamais un champignon sans validation par un
							mycologue.
						</p>
					</div>
				{/if}
			</aside>
		</div>
	{/if}
</section>
