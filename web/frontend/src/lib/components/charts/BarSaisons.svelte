<script lang="ts">
	import type { Mushroom } from '$lib/data/types';
	import { MOIS } from '$lib/data/types';
	import ChartCanvas from './ChartCanvas.svelte';
	import type { ChartConfiguration } from 'chart.js';

	export let mushrooms: Mushroom[] = [];

	$: counts = MOIS.map((_, i) => {
		const k = `saison_mois_${(i + 1).toString().padStart(2, '0')}`;
		return mushrooms.filter((m) => m[k] === true).length;
	});

	$: config = {
		type: 'bar',
		data: {
			labels: MOIS,
			datasets: [
				{
					label: 'Espèces actives',
					data: counts,
					backgroundColor: '#4d8559',
					borderRadius: 6
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: { legend: { display: false } },
			scales: {
				y: { beginAtZero: true, ticks: { precision: 0, color: '#305538' } },
				x: { ticks: { color: '#305538' } }
			}
		}
	} satisfies ChartConfiguration;
</script>

{#key counts.join(',')}
	<ChartCanvas {config} />
{/key}
