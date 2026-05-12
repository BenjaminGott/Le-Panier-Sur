import { writable, derived, type Readable } from 'svelte/store';
import type { Mushroom } from '$lib/data/types';

export type Filters = {
	search: string;
	statuts: string[];
	habitats: string[];
	mois: number[];
	couleursChapeau: string[];
};

export const initialFilters: Filters = {
	search: '',
	statuts: [],
	habitats: [],
	mois: [],
	couleursChapeau: []
};

export const filters = writable<Filters>({ ...initialFilters });

export function resetFilters() {
	filters.set({ ...initialFilters });
}

export function activeFilterCount(f: Filters): number {
	return (
		(f.search ? 1 : 0) +
		f.statuts.length +
		f.habitats.length +
		f.mois.length +
		f.couleursChapeau.length
	);
}

export function makeFiltered(mushrooms: Readable<Mushroom[]>) {
	return derived([mushrooms, filters], ([$m, $f]) => {
		const q = $f.search.trim().toLowerCase();
		return $m.filter((mush) => {
			if (q) {
				const hay = mush.nom.toLowerCase();
				if (!hay.includes(q)) return false;
			}
			if ($f.statuts.length && !$f.statuts.includes(mush.statut)) return false;
			if ($f.habitats.length) {
				const ok = $f.habitats.some((h) => mush[`habitat_type_${h}`] === true);
				if (!ok) return false;
			}
			if ($f.mois.length) {
				const ok = $f.mois.some(
					(mo) => mush[`saison_mois_${mo.toString().padStart(2, '0')}`] === true
				);
				if (!ok) return false;
			}
			if ($f.couleursChapeau.length) {
				const ok = $f.couleursChapeau.some((c) => mush[`chapeau_couleur_${c}`] === true);
				if (!ok) return false;
			}
			return true;
		});
	});
}
