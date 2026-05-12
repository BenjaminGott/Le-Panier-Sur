import Papa from 'papaparse';
import { base } from '$app/paths';
import type { Mushroom } from './types';

let cache: Promise<Mushroom[]> | null = null;

const BOOL_KEYS_NEVER = new Set([
	'nom',
	'statut',
	'slug',
	'image',
	'chapeau_taille_min_cm',
	'chapeau_taille_max_cm',
	'pied_taille_min_cm',
	'pied_taille_max_cm'
]);

export function loadMushrooms(): Promise<Mushroom[]> {
	if (cache) return cache;
	cache = (async () => {
		const [csvText, metaJson] = await Promise.all([
			fetch(`${base}/data/champignons_clean.csv`).then((r) => r.text()),
			fetch(`${base}/data/champignons_meta.json`).then((r) => r.json())
		]);

		const parsed = Papa.parse<Record<string, unknown>>(csvText, {
			header: true,
			dynamicTyping: true,
			skipEmptyLines: true
		});

		const meta = new Map<string, { slug: string; image: string }>();
		for (const m of metaJson as Array<{ nom: string; slug: string; image: string }>) {
			meta.set(m.nom.toUpperCase(), { slug: m.slug, image: m.image });
		}

		const items: Mushroom[] = [];
		for (const row of parsed.data) {
			if (!row || !row.nom) continue;
			const nom = String(row.nom).trim();
			const m = meta.get(nom.toUpperCase());
			const out: Record<string, unknown> = {
				...row,
				nom,
				slug: m?.slug ?? slugify(nom),
				image: m?.image ?? '',
				statut: String(row.statut ?? '').trim()
			};
			// Coerce binary 0/1 -> boolean for non-numeric / non-special columns
			for (const key of Object.keys(out)) {
				if (BOOL_KEYS_NEVER.has(key)) continue;
				const v = out[key];
				if (v === 0 || v === 1) out[key] = v === 1;
			}
			items.push(out as Mushroom);
		}

		items.sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
		return items;
	})();
	return cache;
}

export function slugify(name: string): string {
	return name
		.normalize('NFKD')
		.replace(/[̀-ͯ]/g, '')
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-+|-+$/g, '');
}

export function bySlug(items: Mushroom[], slug: string): Mushroom | undefined {
	return items.find((m) => m.slug === slug);
}

export function presentKeysWithPrefix(m: Mushroom, prefix: string): string[] {
	const out: string[] = [];
	for (const k of Object.keys(m)) {
		if (k.startsWith(prefix) && m[k] === true) {
			out.push(k.slice(prefix.length));
		}
	}
	return out;
}

export function activeMois(m: Mushroom): number[] {
	const months: number[] = [];
	for (let i = 1; i <= 12; i++) {
		const key = `saison_mois_${i.toString().padStart(2, '0')}`;
		if (m[key] === true) months.push(i);
	}
	return months;
}
