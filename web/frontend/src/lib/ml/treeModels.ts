import { base } from '$app/paths';
import { buildFeatureVector, type Prediction } from '$lib/ml/predictor';

export type TreeModelKey = 'tree' | 'forest';

type Leaf = { leaf: [number, number][] };
type Split = { f: number; t: number; l: number; r: number; m: number };
type Node = Leaf | Split;

type TreeModel = {
	kind: TreeModelKey;
	labels: string[];
	features: string[];
	abstain_threshold: number;
	nodes?: Node[];
	trees?: Node[][];
};

export type TreeResult = {
	predictions: Prediction[];
	abstain: boolean;
};

const FILES: Record<TreeModelKey, string> = {
	tree: 'tree_champignons.json',
	forest: 'forest_champignons.json'
};

const cache: Partial<Record<TreeModelKey, Promise<TreeModel>>> = {};

async function loadModel(key: TreeModelKey): Promise<TreeModel> {
	if (!cache[key]) {
		cache[key] = fetch(`${base}/models/${FILES[key]}`).then((r) => {
			if (!r.ok) throw new Error(`fetch ${FILES[key]} -> ${r.status}`);
			return r.json();
		});
	}
	return cache[key]!;
}

export async function checkTreeAvailability(
	key: TreeModelKey
): Promise<{ available: boolean; reason?: string }> {
	try {
		const r = await fetch(`${base}/models/${FILES[key]}`, { method: 'HEAD' });
		if (!r.ok)
			return {
				available: false,
				reason: 'Modèle absent. Lance : python model/train_robust_models.py'
			};
		return { available: true };
	} catch (e) {
		return { available: false, reason: String(e) };
	}
}

function runTree(nodes: Node[], x: Float32Array, out: Float64Array): void {
	let i = 0;
	while (true) {
		const n = nodes[i];
		if ('leaf' in n) {
			for (const [cls, p] of n.leaf) out[cls] += p;
			return;
		}
		const v = x[n.f];
		if (Number.isNaN(v)) i = n.m ? n.l : n.r;
		else i = v <= n.t ? n.l : n.r;
	}
}

export async function predictTree(
	key: TreeModelKey,
	values: Record<string, number>,
	topK = 5
): Promise<TreeResult> {
	const model = await loadModel(key);
	const x = buildFeatureVector(values, model.features);
	const proba = new Float64Array(model.labels.length);

	if (model.kind === 'forest' && model.trees) {
		for (const tree of model.trees) runTree(tree, x, proba);
		for (let i = 0; i < proba.length; i++) proba[i] /= model.trees.length;
	} else if (model.nodes) {
		runTree(model.nodes, x, proba);
	}

	const total = proba.reduce((a, b) => a + b, 0) || 1;
	const idx = Array.from(proba.keys()).sort((a, b) => proba[b] - proba[a]);
	const predictions = idx.slice(0, topK).map((i) => ({
		espece: model.labels[i] ?? `class_${i}`,
		confiance: proba[i] / total
	}));

	const abstain = predictions.length === 0 || predictions[0].confiance < model.abstain_threshold;
	return { predictions, abstain };
}
