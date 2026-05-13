<script lang="ts">
	import ChartCanvas from './ChartCanvas.svelte';
	import type { ChartConfiguration } from 'chart.js';
	import type { Bucket } from '$lib/data/insights';

	export let buckets: Bucket[];

	$: config = {
		type: 'bar',
		data: {
			labels: buckets.map((b) => `${b.label} (n=${b.total})`),
			datasets: [
				{
					label: 'Comestibles',
					data: buckets.map((b) => +b.pctSafe.toFixed(1)),
					backgroundColor: '#4d8559',
					stack: 'stack',
					borderRadius: 4
				},
				{
					label: 'À rejeter / Toxiques',
					data: buckets.map((b) => +b.pctRisky.toFixed(1)),
					backgroundColor: '#e07c2a',
					stack: 'stack',
					borderRadius: 4
				},
				{
					label: 'Mortels',
					data: buckets.map((b) => +b.pctDeadly.toFixed(1)),
					backgroundColor: '#7a0e1a',
					stack: 'stack',
					borderRadius: 4
				}
			]
		},
		options: {
			indexAxis: 'y' as const,
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
				tooltip: {
					callbacks: {
						label: (ctx) => {
							const v = ctx.parsed.x as number;
							return `${ctx.dataset.label} : ${v.toFixed(1)} %`;
						}
					}
				}
			},
			scales: {
				x: {
					stacked: true,
					beginAtZero: true,
					max: 100,
					ticks: { color: '#305538', callback: (v) => `${v}%` }
				},
				y: { stacked: true, ticks: { color: '#305538' } }
			}
		}
	} satisfies ChartConfiguration;
</script>

{#key buckets.map((b) => `${b.label}:${b.total}:${b.deadly}:${b.risky}:${b.safe}`).join('|')}
	<ChartCanvas {config} />
{/key}
