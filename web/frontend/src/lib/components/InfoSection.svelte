<script lang="ts">
	import { COULEUR_HEX } from '$lib/data/types';

	type SubGroup = {
		label: string;
		items: string[];
		colorMode?: boolean;
	};

	export let titre: string;
	export let icon = '';
	/** If set, the whole organ is absent — show only this message. */
	export let absent: string | null = null;
	export let subgroups: SubGroup[] = [];

	function isCouleur(s: string): s is keyof typeof COULEUR_HEX {
		return s in COULEUR_HEX;
	}

	$: present = subgroups.filter((s) => s.items.length > 0);
	$: missing = subgroups.filter((s) => s.items.length === 0).map((s) => s.label);
</script>

<section class="card flex flex-col p-5">
	<header class="mb-3 flex items-center gap-2">
		{#if icon}<span class="text-lg" aria-hidden="true">{icon}</span>{/if}
		<h3 class="font-display text-lg font-semibold text-forest-900">{titre}</h3>
	</header>

	{#if absent}
		<p class="rounded-lg bg-forest-100/60 px-3 py-2 text-sm italic text-forest-600">
			{absent}
		</p>
	{:else}
		<div class="flex flex-col gap-3">
			{#each present as sg}
				<div>
					<p class="section-title mb-1.5">{sg.label}</p>
					<ul class="flex flex-wrap gap-1.5">
						{#each sg.items as it}
							{@const niceLabel = it.replace(/_/g, ' ')}
							{#if sg.colorMode && isCouleur(it)}
								<li class="chip border border-forest-200 bg-white text-xs text-forest-800">
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
				</div>
			{/each}
		</div>

		{#if missing.length > 0}
			<footer
				class="mt-4 flex flex-wrap items-center gap-1.5 border-t border-dashed border-forest-200 pt-3 text-xs text-forest-500"
			>
				<span class="font-semibold">Info manquante&nbsp;:</span>
				{#each missing as label, i}
					<span>{label}{i < missing.length - 1 ? ',' : ''}</span>
				{/each}
			</footer>
		{/if}

		{#if present.length === 0 && missing.length === 0}
			<p class="text-sm italic text-forest-500">Aucune donnée renseignée.</p>
		{/if}
	{/if}
</section>
