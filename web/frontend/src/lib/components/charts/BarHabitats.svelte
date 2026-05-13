<script lang="ts">
	import type { Mushroom } from '$lib/data/types';
	import { HABITATS } from '$lib/data/types';
	import ChartCanvas from './ChartCanvas.svelte';
	import type { ChartConfiguration } from 'chart.js';

	export let mushrooms: Mushroom[] = [];

	$: pairs = HABITATS.map((h) => ({
		label: h.replace(/_/g, ' '),
		count: mushrooms.filter((m) => m[`habitat_type_${h}`] === true).length
	}))
		.filter((p) => p.count > 0)
		.sort((a, b) => b.count - a.count)
		.slice(0, 10);

	$: config = {
		type: 'bar',
		data: {
			labels: pairs.map((p) => p.label),
			datasets: [
				{
					label: 'Espèces',
					data: pairs.map((p) => p.count),
					backgroundColor: '#a8693e',
					borderRadius: 6
				}
			]
		},
		options: {
			indexAxis: 'y' as const,
			responsive: true,
			maintainAspectRatio: false,
			plugins: { legend: { display: false } },
			scales: {
				x: { beginAtZero: true, ticks: { precision: 0, color: '#305538' } },
				y: { ticks: { color: '#305538' } }
			}
		}
	} satisfies ChartConfiguration;
</script>

{#key pairs.map((p) => p.count).join(',')}
	<ChartCanvas {config} />
{/key}
