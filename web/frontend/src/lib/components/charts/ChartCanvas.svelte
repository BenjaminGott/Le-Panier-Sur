<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import {
		Chart,
		ArcElement,
		BarElement,
		CategoryScale,
		LinearScale,
		Tooltip,
		Legend,
		PieController,
		BarController
	} from 'chart.js';
	import type { ChartConfiguration } from 'chart.js';

	Chart.register(
		ArcElement,
		BarElement,
		CategoryScale,
		LinearScale,
		Tooltip,
		Legend,
		PieController,
		BarController
	);

	export let config: ChartConfiguration;
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;

	onMount(() => {
		chart = new Chart(canvas, config);
	});

	onDestroy(() => {
		chart?.destroy();
	});
</script>

<div class="relative h-[280px] w-full">
	<canvas bind:this={canvas}></canvas>
</div>
