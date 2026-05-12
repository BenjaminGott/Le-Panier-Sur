<script lang="ts">
	import { STATUT_VARIANT } from '$lib/data/types';

	export let statut: string;
	export let size: 'sm' | 'md' | 'lg' = 'sm';

	const VARIANT_STYLE: Record<string, string> = {
		excellent: 'bg-status-excellent text-white',
		bon: 'bg-status-bon text-white',
		mediocre: 'bg-status-mediocre text-forest-950',
		rejeter: 'bg-status-rejeter text-white',
		toxique: 'bg-status-toxique text-white',
		mortel: 'bg-status-mortel text-white'
	};

	const VARIANT_ICON: Record<string, string> = {
		excellent: '★',
		bon: '✓',
		mediocre: '~',
		rejeter: '✗',
		toxique: '☠',
		mortel: '⚠'
	};

	$: variant = STATUT_VARIANT[statut] ?? 'mediocre';
	$: classes = VARIANT_STYLE[variant] ?? VARIANT_STYLE.mediocre;
	$: icon = VARIANT_ICON[variant] ?? '';

	$: sizeCls =
		size === 'lg'
			? 'px-3 py-1.5 text-sm'
			: size === 'md'
				? 'px-2.5 py-1 text-xs'
				: 'px-2 py-0.5 text-[0.7rem]';
</script>

<span class="chip {classes} {sizeCls} font-semibold tracking-wide shadow-sm">
	<span aria-hidden="true">{icon}</span>
	<span>{statut}</span>
</span>
