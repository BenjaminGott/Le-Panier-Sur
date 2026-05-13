<script lang="ts">
	import type { Mushroom } from '$lib/data/types';
	import { HABITATS } from '$lib/data/types';
	import { dangerLevel } from '$lib/data/insights';
	import ChartCanvas from './ChartCanvas.svelte';
	import type { ChartConfiguration } from 'chart.js';

	export let mushrooms: Mushroom[] = [];

	function colorForPct(pct: number): string {
		if (pct >= 60) return '#7a0e1a';
		if (pct >= 40) return '#c1333d';
		if (pct >= 25) return '#e07c2a';
		if (pct >= 10) return '#f1c757';
		return '#4d8559';
	}

	$: rows = HABITATS.map((h) => {
		const subset = mushrooms.filter((m) => m[`habitat_type_${h}`] === true);
		const n = subset.length;
		if (n === 0) return null;
		let danger = 0;
		for (const m of subset) {
			const d = dangerLevel(m.statut);
			if (d !== 'safe') danger++;
		}
		const pct = (danger / n) * 100;
		return {
			label: h.replace(/_/g, ' '),
			pct,
			n
		};
	})
		.filter((r): r is { label: string; pct: number; n: number } => r !== null && r.n >= 5)
		.sort((a, b) => a.pct - b.pct);

	$: config = {
		type: 'bar',
		data: {
			labels: rows.map((r) => `${r.label} (n=${r.n})`),
			datasets: [
				{
					label: '% espèces dangereuses',
					data: rows.map((r) => +r.pct.toFixed(1)),
					backgroundColor: rows.map((r) => colorForPct(r.pct)),
					borderRadius: 6
				}
			]
		},
		options: {
			indexAxis: 'y' as const,
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: { display: false },
				tooltip: {
					callbacks: {
						label: (ctx) => `${(ctx.parsed.x as number).toFixed(1)} % dangereuses`
					}
				}
			},
			scales: {
				x: {
					beginAtZero: true,
					max: 100,
					ticks: { color: '#305538', callback: (v) => `${v}%` },
					title: {
						display: true,
						text: '% espèces dangereuses (toxiques + à rejeter + mortelles)',
						color: '#305538',
						font: { size: 11 }
					}
				},
				y: { ticks: { color: '#305538', font: { size: 11 } } }
			}
		}
	} satisfies ChartConfiguration;
</script>

{#key rows.map((r) => `${r.label}:${r.n}:${r.pct.toFixed(1)}`).join('|')}
	<ChartCanvas {config} />
{/key}
