<script lang="ts">
	export let observed: boolean;
</script>

<span
	class="chip text-[0.65rem] font-semibold uppercase tracking-wide"
	class:bg-forest-600={observed}
	class:text-white={observed}
	class:bg-forest-100={!observed}
	class:text-forest-600={!observed}
	title={observed
		? 'Au moins une sélection : les autres options seront marquées absentes.'
		: 'Aucune sélection : la section est ignorée par le modèle.'}
>
	{observed ? 'Observé' : 'Inconnu'}
</span>
