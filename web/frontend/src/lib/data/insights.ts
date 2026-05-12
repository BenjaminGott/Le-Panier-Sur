import type { Mushroom } from './types';
import { STATUT_VARIANT } from './types';

export type DangerLevel = 'safe' | 'risky' | 'deadly';

export function dangerLevel(statut: string): DangerLevel {
	const v = STATUT_VARIANT[statut];
	if (v === 'mortel') return 'deadly';
	if (v === 'toxique' || v === 'rejeter') return 'risky';
	return 'safe';
}

export type Bucket = {
	label: string;
	total: number;
	safe: number;
	risky: number;
	deadly: number;
	pctSafe: number;
	pctRisky: number;
	pctDeadly: number;
};

export function bucketize(mushrooms: Mushroom[], label: string): Bucket {
	const b: Bucket = {
		label,
		total: mushrooms.length,
		safe: 0,
		risky: 0,
		deadly: 0,
		pctSafe: 0,
		pctRisky: 0,
		pctDeadly: 0
	};
	for (const m of mushrooms) {
		const d = dangerLevel(m.statut);
		if (d === 'safe') b.safe++;
		else if (d === 'risky') b.risky++;
		else b.deadly++;
	}
	if (b.total > 0) {
		b.pctSafe = (b.safe / b.total) * 100;
		b.pctRisky = (b.risky / b.total) * 100;
		b.pctDeadly = (b.deadly / b.total) * 100;
	}
	return b;
}

/** Lift = P(danger|feature) / P(danger). >1 = la feature augmente le risque. */
export function lift(buckets: { with: Bucket; without: Bucket }, level: 'risky' | 'deadly') {
	const baseline =
		(buckets.with[level] + buckets.without[level]) /
		Math.max(1, buckets.with.total + buckets.without.total);
	if (baseline === 0) return 0;
	const pWith = buckets.with[level] / Math.max(1, buckets.with.total);
	return pWith / baseline;
}

export type FeaturePredicate = {
	id: string;
	label: string;
	test: (m: Mushroom) => boolean;
};

export function splitBy(mushrooms: Mushroom[], pred: FeaturePredicate) {
	const wi: Mushroom[] = [];
	const wo: Mushroom[] = [];
	for (const m of mushrooms) (pred.test(m) ? wi : wo).push(m);
	return {
		with: bucketize(wi, `Avec ${pred.label}`),
		without: bucketize(wo, `Sans ${pred.label}`)
	};
}

