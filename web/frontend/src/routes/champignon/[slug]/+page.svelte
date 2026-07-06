<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { loadMushrooms, presentKeysWithPrefix, activeMois, bySlug } from '$lib/data/loader';
	import type { Mushroom } from '$lib/data/types';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import InfoSection from '$lib/components/InfoSection.svelte';
	import SaisonStrip from '$lib/components/SaisonStrip.svelte';

	let mushroom: Mushroom | undefined;
	let loading = true;
	let error = '';
	let canGoBack = false;

	$: slug = $page.params.slug ?? '';

	function goBack() {
		if (canGoBack) {
			history.back();
		} else {
			window.location.href = `${base}/`;
		}
	}

	onMount(async () => {
		canGoBack = window.history.length > 1;
		try {
			const items = await loadMushrooms();
			mushroom = bySlug(items, slug);
			if (!mushroom) error = 'Champignon introuvable';
		} catch (e) {
			error = String(e);
		} finally {
			loading = false;
		}
	});

	$: chapeauCouleurs = mushroom ? presentKeysWithPrefix(mushroom, 'chapeau_couleur_') : [];
	$: chapeauTextures = mushroom ? presentKeysWithPrefix(mushroom, 'chapeau_texture_') : [];

	$: lamesCouleurs = mushroom ? presentKeysWithPrefix(mushroom, 'lames_couleur_') : [];
	$: lamesAttaches = mushroom ? presentKeysWithPrefix(mushroom, 'lames_attache_') : [];

	$: poresCouleurs = mushroom ? presentKeysWithPrefix(mushroom, 'pores_couleur_') : [];
	$: poresAttaches = mushroom ? presentKeysWithPrefix(mushroom, 'pores_attache_') : [];

	$: piedCouleurs = mushroom ? presentKeysWithPrefix(mushroom, 'pied_couleur_') : [];
	$: piedTextures = mushroom ? presentKeysWithPrefix(mushroom, 'pied_texture_') : [];
	$: piedMorpho = mushroom ? presentKeysWithPrefix(mushroom, 'pied_morpho_') : [];

	$: chairCouleurs = mushroom ? presentKeysWithPrefix(mushroom, 'chair_couleur_') : [];
	$: chairConsistance = mushroom ? presentKeysWithPrefix(mushroom, 'chair_consistance_') : [];

	$: odeurs = mushroom ? presentKeysWithPrefix(mushroom, 'odeur_type_') : [];
	$: saveurs = mushroom ? presentKeysWithPrefix(mushroom, 'saveur_type_') : [];

	$: habitats = mushroom ? presentKeysWithPrefix(mushroom, 'habitat_type_') : [];
	$: mois = mushroom ? activeMois(mushroom) : [];
</script>

<svelte:head>
	<title>{mushroom?.nom ?? 'Champignon'} — Le Panier-Sûr</title>
</svelte:head>

<section class="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:py-10">
	<button type="button" on:click={goBack} class="btn-ghost mb-4 text-sm">
		← Retour à la galerie
	</button>

	{#if loading}
		<p class="text-forest-600">Chargement…</p>
	{:else if error || !mushroom}
		<div class="card p-8 text-center text-forest-700">
			{error || 'Introuvable'}
		</div>
	{:else}
		<header class="card mb-6 flex flex-col gap-6 overflow-hidden p-0 sm:flex-row">
			<div class="relative w-full shrink-0 bg-forest-100 sm:max-w-md">
				{#if mushroom.image}
					<img
						src="{base}{mushroom.image}"
						alt={mushroom.nom}
						class="h-full max-h-[420px] w-full object-cover"
					/>
				{:else}
					<div class="flex h-72 w-full items-center justify-center text-6xl text-forest-300">
						🍄
					</div>
				{/if}
			</div>
			<div class="flex flex-1 flex-col gap-4 p-6 sm:p-8">
				<h1 class="font-display text-3xl font-bold text-forest-950 sm:text-4xl">
					{mushroom.nom}
				</h1>
				<div>
					<StatusBadge statut={mushroom.statut} size="lg" />
				</div>

				<dl class="grid grid-cols-2 gap-4 text-sm">
					{#if mushroom.chapeau_taille_min_cm != null}
						<div>
							<dt class="section-title">Chapeau</dt>
							<dd class="font-display text-lg text-forest-900">
								{mushroom.chapeau_taille_min_cm}–{mushroom.chapeau_taille_max_cm} cm
							</dd>
						</div>
					{/if}
					{#if mushroom.pied_taille_min_cm != null}
						<div>
							<dt class="section-title">Pied</dt>
							<dd class="font-display text-lg text-forest-900">
								{mushroom.pied_taille_min_cm}–{mushroom.pied_taille_max_cm} cm
							</dd>
						</div>
					{/if}
				</dl>

				<a href="{base}/predict?ref={mushroom.slug}" class="btn-primary mt-auto w-fit text-sm">
					Identifier un champignon similaire →
				</a>
			</div>
		</header>

		<div class="grid gap-4 lg:grid-cols-2">
			<InfoSection
				titre="Chapeau"
				icon="🍄"
				absent={mushroom.a_un_chapeau ? null : 'Pas de chapeau'}
				subgroups={[
					{ label: 'Couleurs', items: chapeauCouleurs, colorMode: true },
					{ label: 'Texture', items: chapeauTextures }
				]}
			/>

			<InfoSection
				titre="Lames"
				icon="🌿"
				absent={mushroom.a_des_lames ? null : 'Pas de lames'}
				subgroups={[
					{ label: 'Couleurs', items: lamesCouleurs, colorMode: true },
					{ label: 'Attaches', items: lamesAttaches }
				]}
			/>

			<InfoSection
				titre="Pores"
				icon="•"
				absent={mushroom.a_des_pores ? null : 'Pas de pores'}
				subgroups={[
					{ label: 'Couleurs', items: poresCouleurs, colorMode: true },
					{ label: 'Attaches', items: poresAttaches }
				]}
			/>

			<InfoSection
				titre="Pied"
				icon="🌱"
				absent={mushroom.a_un_pied ? null : 'Pas de pied'}
				subgroups={[
					{ label: 'Couleur', items: piedCouleurs, colorMode: true },
					{ label: 'Texture', items: piedTextures },
					{ label: 'Morphologie', items: piedMorpho }
				]}
			/>

			<InfoSection
				titre="Chair"
				icon="🥩"
				absent={mushroom.a_de_la_chair ? null : 'Pas de chair'}
				subgroups={[
					{ label: 'Couleur', items: chairCouleurs, colorMode: true },
					{ label: 'Consistance', items: chairConsistance }
				]}
			/>

			<InfoSection
				titre="Odeur & saveur"
				icon="👃"
				subgroups={[
					{ label: 'Odeur', items: odeurs },
					{ label: 'Saveur', items: saveurs }
				]}
			/>

			<InfoSection titre="Habitat" icon="🌳" subgroups={[{ label: 'Milieux', items: habitats }]} />

			<SaisonStrip active={mois} />
		</div>
	{/if}
</section>
