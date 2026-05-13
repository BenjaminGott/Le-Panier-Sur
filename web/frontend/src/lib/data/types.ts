export type Statut =
	| 'Les excellents champignons'
	| 'Les bons champignons'
	| 'Les champignons mediocres'
	| 'Champignon à rejeter'
	| 'Les champignons toxiques'
	| 'Les champignons mortel'
	| string;

export type Mushroom = {
	nom: string;
	slug: string;
	image: string;
	statut: string;

	// Tailles (cm)
	chapeau_taille_min_cm: number | null;
	chapeau_taille_max_cm: number | null;
	pied_taille_min_cm: number | null;
	pied_taille_max_cm: number | null;

	// Présence des organes (booléens 0/1)
	a_un_chapeau: boolean;
	a_des_pores: boolean;
	a_des_lames: boolean;
	a_un_pied: boolean;
	a_de_la_chair: boolean;

	// Toutes les autres colonnes booléennes du CSV
	[key: string]: boolean | number | string | null;
};

export type FeatureGroup = {
	titre: string;
	icon: string;
	prefix: string;
	items: { key: string; label: string }[];
};

export const COULEURS = [
	'blanc',
	'brun',
	'jaune',
	'rouge',
	'orange',
	'rose',
	'gris',
	'noir',
	'vert',
	'bleu',
	'violet',
	'ocre',
	'roux'
] as const;

export const COULEUR_HEX: Record<(typeof COULEURS)[number], string> = {
	blanc: '#f5f5f0',
	brun: '#8b5a2b',
	jaune: '#f1c757',
	rouge: '#c1333d',
	orange: '#e07c2a',
	rose: '#e8a4b3',
	gris: '#9ca3af',
	noir: '#1f2937',
	vert: '#4d8559',
	bleu: '#3a6ea8',
	violet: '#7e57c2',
	ocre: '#bd7012',
	roux: '#a8693e'
};

export const MOIS = [
	'Jan',
	'Fév',
	'Mar',
	'Avr',
	'Mai',
	'Juin',
	'Juil',
	'Août',
	'Sep',
	'Oct',
	'Nov',
	'Déc'
];

export const HABITATS = [
	'feuillus',
	'coniferes',
	'foret',
	'prairies',
	'clairieres',
	'lisieres',
	'jardins',
	'bois',
	'chenes',
	'hetres',
	'pins',
	'bouleaux',
	'chataigniers',
	'charmes',
	'melezes',
	'bois_morts'
] as const;

export const STATUT_VARIANT: Record<string, string> = {
	'Les excellents champignons': 'excellent',
	'Les bons champignons': 'bon',
	'Les champignons mediocres': 'mediocre',
	'Champignon à rejeter': 'rejeter',
	'Les champignons toxiques': 'toxique',
	'Les champignons mortel': 'mortel'
};

export const STATUT_LABEL: Record<string, string> = {
	'Les excellents champignons': 'Excellents',
	'Les bons champignons': 'Bons',
	'Les champignons mediocres': 'Médiocres',
	'Champignon à rejeter': 'À rejeter',
	'Les champignons toxiques': 'Toxiques',
	'Les champignons mortel': 'Mortels'
};

export const STATUT_ORDER = [
	'Les excellents champignons',
	'Les bons champignons',
	'Les champignons mediocres',
	'Champignon à rejeter',
	'Les champignons toxiques',
	'Les champignons mortel'
];
