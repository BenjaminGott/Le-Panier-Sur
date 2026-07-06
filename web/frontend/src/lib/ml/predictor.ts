import * as ort from 'onnxruntime-web';
import { base } from '$app/paths';

// Singletons — le modèle et les métadonnées ne sont chargés qu'une seule fois
let sessionPromise: Promise<ort.InferenceSession> | null = null;
let featuresPromise: Promise<string[]> | null = null;
let labelsPromise: Promise<string[]> | null = null;

export type Prediction = { espece: string; confiance: number };

export type PredictionAvailability = {
	available: boolean;
	reason?: string;
};

async function loadJson<T>(url: string): Promise<T> {
	const r = await fetch(url);
	if (!r.ok) throw new Error(`fetch ${url} -> ${r.status}`);
	return r.json();
}

// Vérifie que le fichier .onnx est bien présent avant d'afficher l'UI de prédiction
export async function checkAvailability(): Promise<PredictionAvailability> {
	try {
		const r = await fetch(`${base}/models/xgb_champignons.onnx`, { method: 'HEAD' });
		if (!r.ok) {
			return {
				available: false,
				reason:
					"Le modèle ONNX n'est pas généré. Lance : python scripts/export_onnx.py (depuis web/frontend)"
			};
		}
		return { available: true };
	} catch (e) {
		return { available: false, reason: String(e) };
	}
}

// Liste des 163 features attendues par le modèle (ordre strict)
export async function getFeatures(): Promise<string[]> {
	if (!featuresPromise) {
		featuresPromise = loadJson<string[]>(`${base}/models/xgb_features.json`);
	}
	return featuresPromise;
}

// Noms des 219 espèces de champignons (index = classe XGBoost)
export async function getLabels(): Promise<string[]> {
	if (!labelsPromise) {
		labelsPromise = loadJson<string[]>(`${base}/models/xgb_labels.json`);
	}
	return labelsPromise;
}

// Charge le modèle ONNX dans le navigateur via WebAssembly (pas de serveur requis)
async function getSession(): Promise<ort.InferenceSession> {
	if (!sessionPromise) {
		sessionPromise = ort.InferenceSession.create(`${base}/models/xgb_champignons.onnx`, {
			executionProviders: ['wasm']
		});
	}
	return sessionPromise;
}

/**
 * Aligne les valeurs du formulaire sur l'ordre exact des features du modèle.
 * Les features non renseignées → NaN (XGBoost les gère nativement).
 */
export function buildFeatureVector(
	values: Record<string, number>,
	features: string[]
): Float32Array {
	const arr = new Float32Array(features.length);
	for (let i = 0; i < features.length; i++) {
		const v = values[features[i]];
		arr[i] = v == null ? NaN : v; // champ absent = donnée manquante
	}
	return arr;
}

/**
 * Lance l'inférence ONNX et retourne les top-K espèces
 * les plus probables avec leur score de confiance.
 */
export async function predict(values: Record<string, number>, topK = 5): Promise<Prediction[]> {
	// Chargement parallèle du modèle et des métadonnées
	const [session, features, labels] = await Promise.all([
		getSession(),
		getFeatures(),
		getLabels()
	]);

	// Construction du tenseur d'entrée [1 × nb_features]
	const vec = buildFeatureVector(values, features);
	const tensor = new ort.Tensor('float32', vec, [1, features.length]);

	const inputName = session.inputNames[0];
	const outputs = await session.run({ [inputName]: tensor });

	// Récupération de la sortie de probabilités [1 × 219]
	let proba: number[] | null = null;
	for (const name of session.outputNames) {
		const t = outputs[name];
		if (!t || t.type !== 'float32') continue;
		const dims = t.dims;
		if (dims.length === 2 && dims[0] === 1 && Number(dims[1]) === labels.length) {
			proba = Array.from(t.data as Float32Array);
			break;
		}
	}
	// Fallback si le nom du tenseur de sortie est inattendu
	if (!proba) {
		for (const name of session.outputNames) {
			const t = outputs[name];
			if (t && t.type === 'float32') {
				proba = Array.from(t.data as Float32Array);
				break;
			}
		}
	}
	if (!proba) throw new Error('No usable output tensor from ONNX model');

	// Tri décroissant par probabilité → top-K résultats
	const idx = proba.map((_, i) => i);
	idx.sort((a, b) => proba![b] - proba![a]);
	return idx.slice(0, topK).map((i) => ({
		espece: labels[i] ?? `class_${i}`,
		confiance: proba![i]
	}));
}
