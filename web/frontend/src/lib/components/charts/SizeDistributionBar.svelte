<script lang="ts">
	import type { Mushroom } from '$lib/data/types';
	import { dangerLevel } from '$lib/data/insights';
	import ChartCanvas from './ChartCanvas.svelte';
	import type { ChartConfiguration } from 'chart.js';

	export let mushrooms: Mushroom[] = [];

	const BUCKETS: Array<{ label: string; min: number; max: number }> = [
		{ label: '0–3 cm', min: 0, max: 3 },
		{ label: '3–6 cm', min: 3, max: 6 },
		{ label: '6–10 cm', min: 6, max: 10 },
		{ label: '10–15 cm', min: 10, max: 15 },
		{ label: '15–20 cm', min: 15, max: 20 },
		{ label: '20+ cm', min: 20, max: Infinity }
	];

	function avgSize(m: Mushroom): number | null {
		const min = m.chapeau_taille_min_cm;
		const max = m.chapeau_taille_max_cm;
		if (typeof min !== 'number' || typeof max !== 'number' || min === 0 || max === 0) return null;
		return (min + max) / 2;
	}

	$: counts = (() => {
		const safe = BUCKETS.map(() => 0);
		const risky = BUCKETS.map(() => 0);
		const deadly = BUCKETS.map(() => 0);
		for (const m of mushrooms) {
			const s = avgSize(m);
			if (s == null) continue;
			const idx = BUCKETS.findIndex((b) => s >= b.min && s < b.max);
			if (idx === -1) continue;
			const d = dangerLevel(m.statut);
			if (d === 'safe') safe[idx]++;
			else if (d === 'risky') risky[idx]++;
			else deadly[idx]++;
		}
		return { safe, risky, deadly };
	})();

	$: config = {
		type: 'bar',
		data: {
			labels: BUCKETS.map((b) => b.label),
			datasets: [
				{
					label: 'Comestibles',
					data: counts.safe,
					backgroundColor: '#4d8559',
					stack: 'stack',
					borderRadius: 4
				},
				{
					label: 'À rejeter / Toxiques',
					data: counts.risky,
					backgroundColor: '#e07c2a',
					stack: 'stack',
					borderRadius: 4
				},
				{
					label: 'Mortels',
					data: counts.deadly,
					backgroundColor: '#7a0e1a',
					stack: 'stack',
					borderRadius: 4
				}
			]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
				tooltip: {
					callbacks: {
						label: (ctx) => `${ctx.dataset.label} : ${ctx.parsed.y} espèces`
					}
				}
			},
			scales: {
				x: {
					stacked: true,
					ticks: { color: '#305538' },
					title: {
						display: true,
						text: 'Taille moyenne du chapeau',
						color: '#305538',
						font: { size: 11 }
					}
				},
				y: {
					stacked: true,
					beginAtZero: true,
					ticks: { precision: 0, color: '#305538' },
					title: {
						display: true,
						text: "Nombre d'espèces",
						color: '#305538',
						font: { size: 11 }
					}
				}
			}
		}
	} satisfies ChartConfiguration;
</script>

{#key counts.safe.concat(counts.risky, counts.deadly).join(',')}
	<ChartCanvas {config} />
{/key}
