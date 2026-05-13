<script lang="ts">
	import type { Mushroom } from '$lib/data/types';
	import { STATUT_ORDER, STATUT_LABEL, STATUT_VARIANT } from '$lib/data/types';
	import ChartCanvas from './ChartCanvas.svelte';
	import type { ChartConfiguration } from 'chart.js';

	export let mushrooms: Mushroom[] = [];

	const VARIANT_COLOR: Record<string, string> = {
		excellent: '#2e7d32',
		bon: '#66a44e',
		mediocre: '#cda434',
		rejeter: '#e07c2a',
		toxique: '#c1333d',
		mortel: '#7a0e1a'
	};

	$: counts = (() => {
		const c: Record<string, number> = {};
		for (const m of mushrooms) c[m.statut] = (c[m.statut] ?? 0) + 1;
		return c;
	})();

	$: orderedKeys = STATUT_ORDER.filter((s) => counts[s]);
	$: labels = orderedKeys.map((s) => STATUT_LABEL[s] ?? s);
	$: data = orderedKeys.map((s) => counts[s]);
	$: colors = orderedKeys.map((s) => VARIANT_COLOR[STATUT_VARIANT[s] ?? 'mediocre']);

	$: config = {
		type: 'pie',
		data: {
			labels,
			datasets: [
				{
					data,
					backgroundColor: colors,
					borderColor: '#ffffff',
					borderWidth: 2
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
			}
		}
	} satisfies ChartConfiguration;
</script>

{#key data.join(',')}
	<ChartCanvas {config} />
{/key}
