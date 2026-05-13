import { writable } from 'svelte/store';
import type { Prediction } from '$lib/ml/predictor';

export type Porteur = 'lames' | 'pores' | 'aucun';

export type PredictForm = {
	a_un_chapeau: boolean;
	a_un_pied: boolean;
	a_de_la_chair: boolean;
	porteur: Porteur;
	chapeau_taille_cm: number;
	pied_taille_cm: number;
	chapeauCouleurs: string[];
	piedCouleurs: string[];
	lamesCouleurs: string[];
	poresCouleurs: string[];
	chairCouleurs: string[];
	chapeauTextures: string[];
	piedTextures: string[];
	piedMorpho: string[];
	lamesAttaches: string[];
	poresAttaches: string[];
	chairConsistance: string[];
	odeur: string[];
	saveur: string[];
	habitats: string[];
	mois: number[];
};

export const initialPredictForm: PredictForm = {
	a_un_chapeau: true,
	a_un_pied: true,
	a_de_la_chair: true,
	porteur: 'lames',
	chapeau_taille_cm: 8,
	pied_taille_cm: 6,
	chapeauCouleurs: [],
	piedCouleurs: [],
	lamesCouleurs: [],
	poresCouleurs: [],
	chairCouleurs: [],
	chapeauTextures: [],
	piedTextures: [],
	piedMorpho: [],
	lamesAttaches: [],
	poresAttaches: [],
	chairConsistance: [],
	odeur: [],
	saveur: [],
	habitats: [],
	mois: []
};

export const predictForm = writable<PredictForm>({ ...initialPredictForm });
export const predictResults = writable<Prediction[] | null>(null);

export function resetPredictForm() {
	predictForm.set({ ...initialPredictForm });
	predictResults.set(null);
}
