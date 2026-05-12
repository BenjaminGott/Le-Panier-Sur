import type { Mushroom } from './types';
import type { FeaturePredicate } from './insights';

export type GuideChartType = 'stacked' | 'habitat' | 'size';

export type GuideStep = {
	id: string;
	numero: number;
	icon: string;
	titre: string;
	sousTitre: string;
	intro: string;
	predicates: FeaturePredicate[];
	chart: GuideChartType;
	especes: string[];
	aFaire: string[];
	aEviter: string[];
	conclusion: string;
};

export const GUIDE_STEPS: GuideStep[] = [
	{
		id: 'preparer-sortie',
		numero: 1,
		icon: '🗺️',
		titre: 'Préparer la sortie',
		sousTitre: 'Où et quand ramasser ?',
		intro:
			"Avant même de toucher un champignon, ton choix d'habitat et de saison oriente déjà fortement la probabilité de tomber sur des espèces dangereuses. Les feuillus (chênes, hêtres) hébergent la majorité des Amanites mortelles, alors que les prairies et clairières contiennent surtout des espèces non-mortelles — le risque change radicalement selon le décor.",
		predicates: [],
		chart: 'habitat',
		especes: ['AMANITE PHALLOÏDE', 'CÈPE DE BORDEAUX', 'GIROLLE'],
		aFaire: [
			"Note systématiquement les arbres voisins (chêne, hêtre, pin, bouleau…)",
			"Privilégie les sorties après quelques jours de pluie suivis d'une accalmie",
			"Cible les habitats que tu connais bien avant d'explorer de nouveaux milieux"
		],
		aEviter: [
			"Cueillir « au hasard » sans repérer le type de forêt",
			"Sortir hors saison — la majorité des espèces apparaissent de septembre à novembre",
			"Mélanger des champignons issus d'habitats différents dans le même panier"
		],
		conclusion:
			"L'habitat est le premier filtre : sous chênes et hêtres, redouble de prudence. En prairie, la palette d'espèces dangereuses est plus restreinte mais existe (Clitocybes blancs, Inocybes…)."
	},
	{
		id: 'observation-distance',
		numero: 2,
		icon: '👀',
		titre: 'Première observation à distance',
		sousTitre: 'Forme et taille avant tout',
		intro:
			"Avant de cueillir, regarde la silhouette générale. Les très grandes espèces (chapeau ≥ 15 cm) sont majoritairement des Bolets, Lépiotes ou Polypores — un profil différent des petites espèces où se cachent beaucoup d'Inocybes et Clitocybes risqués. La taille seule ne décide rien, mais elle oriente la famille.",
		predicates: [
			{
				id: 'grand-chapeau',
				label: 'grand chapeau (≥ 15 cm)',
				test: (m: Mushroom) => {
					const v = m.chapeau_taille_max_cm;
					return typeof v === 'number' && v >= 15;
				}
			},
			{
				id: 'petit-chapeau',
				label: 'petit chapeau (≤ 5 cm)',
				test: (m: Mushroom) => {
					const v = m.chapeau_taille_max_cm;
					return typeof v === 'number' && v > 0 && v <= 5;
				}
			}
		],
		chart: 'size',
		especes: ['POLYPORE SOUFRÉ', 'CÈPE DE BORDEAUX', 'RUSSULE ÉMÉTIQUE'],
		aFaire: [
			"Mémoriser la silhouette globale : trapue, élancée, en parasol, en éponge",
			"Mesurer mentalement le chapeau (paume = ~10 cm pour repère)",
			"Photographier l'environnement avant de cueillir, pour garder le contexte"
		],
		aEviter: [
			"Conclure « gros = bon » : certains Bolets satans atteignent 30 cm",
			"Ignorer les très petites espèces — beaucoup d'Inocybes mortels font 2-4 cm",
			"Cueillir sans avoir vu la silhouette entière (chapeau + pied)"
		],
		conclusion:
			"La taille n'est qu'un premier indice. Note-la mentalement, puis passe à l'inspection détaillée du pied et du dessous du chapeau."
	},
	{
		id: 'inspecter-pied',
		numero: 3,
		icon: '🚩',
		titre: 'Inspecter le pied',
		sousTitre: "Volve et anneau : les drapeaux rouges",
		intro:
			"Le critère le plus discriminant du dataset. Les Amanites — qui regroupent les espèces les plus mortelles d'Europe (Phalloïde, Vireuse, Printanière) — partagent une signature : un pied avec **volve** (sac à la base, parfois enterré) et souvent un **anneau**. Cette particularité fait basculer la statistique vers le mortel de manière spectaculaire.",
		predicates: [
			{
				id: 'volve',
				label: 'volve à la base',
				test: (m: Mushroom) => m.pied_morpho_volve === true
			},
			{
				id: 'anneau',
				label: 'anneau sur le pied',
				test: (m: Mushroom) => m.pied_morpho_anneau === true
			},
			{
				id: 'volve-ou-anneau',
				label: 'volve OU anneau',
				test: (m: Mushroom) => m.pied_morpho_volve === true || m.pied_morpho_anneau === true
			}
		],
		chart: 'stacked',
		especes: ['AMANITE PHALLOÏDE', 'AMANITE VIREUSE', 'LÉPIOTE ÉLEVÉE'],
		aFaire: [
			"Toujours déterrer le pied entier — la volve peut être cachée sous la mousse",
			"Couper proprement à la base avec un couteau, sans arracher",
			"Examiner l'anneau : libre/coulissant, fixe, double, denté ?"
		],
		aEviter: [
			"Couper le pied au ras du sol — tu perds le critère le plus important",
			"Ignorer un petit renflement à la base : c'est peut-être une volve naissante",
			"Confondre une simple gaine (Cortinaires) avec une vraie volve"
		],
		conclusion:
			"Une volve = passe ton chemin tant que tu n'as pas formellement identifié l'espèce. C'est la règle qui sauve le plus de vies chez les cueilleurs débutants."
	},
	{
		id: 'sous-chapeau',
		numero: 4,
		icon: '🦠',
		titre: 'Sous le chapeau',
		sousTitre: 'Pores ou lames ? Et de quelle couleur ?',
		intro:
			"Retourne le champignon. Sous le chapeau : soit des **lames** (Agarics, Amanites, Russules…), soit des **pores** (Bolets, comme une éponge). Statistiquement, les espèces à pores ont une part de comestibles plus élevée (cèpes !), mais comportent des pièges. Et surtout : des pores **rouges ou orangés vifs** sont rares chez les espèces sûres.",
		predicates: [
			{
				id: 'pores',
				label: 'pores (Bolets)',
				test: (m: Mushroom) => m.a_des_pores === true
			},
			{
				id: 'lames',
				label: 'lames',
				test: (m: Mushroom) => m.a_des_lames === true
			},
			{
				id: 'pores-rouges',
				label: 'pores rouges/orange',
				test: (m: Mushroom) =>
					m.pores_couleur_rouge === true || m.pores_couleur_orange === true
			}
		],
		chart: 'stacked',
		especes: ['CÈPE DE BORDEAUX', 'BOLET SATAN', 'GIROLLE'],
		aFaire: [
			"Toujours retourner le champignon avant de décider",
			"Pour les Bolets : observer si la chair bleuit à la coupe",
			"Apprendre à distinguer cèpes (pores blancs/jaunes) des bolets dangereux (pores rouges)"
		],
		aEviter: [
			"Cueillir un Bolet aux pores rouges « au cas où »",
			"Ignorer la couleur des lames : les lames blanches d'Amanite peuvent être traîtres",
			"Mélanger un Bolet et un Agaric dans le même sac (les confusions de cuisine sont vite arrivées)"
		],
		conclusion:
			"Pour les Bolets : pores rouges + chair qui bleuit fort + chapeau sombre → on laisse sur place. Pour les lames : croise toujours avec la couleur du pied et la présence d'anneau."
	},
	{
		id: 'couleur-chapeau',
		numero: 5,
		icon: '🎨',
		titre: 'Couleurs du chapeau',
		sousTitre: 'Un indice trompeur',
		intro:
			"Beaucoup pensent qu'un chapeau rouge = poison. La data nuance ce mythe : le rouge est sur-représenté chez les espèces toxiques, mais beaucoup de **mortels (Phalloïde, Vireuse) sont blancs ou verdâtres**. À l'inverse, certains chapeaux jaunes ou bruns abritent autant d'excellents que de toxiques. La couleur seule ne décide rien.",
		predicates: [
			{
				id: 'chapeau-rouge',
				label: 'chapeau rouge',
				test: (m: Mushroom) => m.chapeau_couleur_rouge === true
			},
			{
				id: 'chapeau-blanc',
				label: 'chapeau blanc',
				test: (m: Mushroom) => m.chapeau_couleur_blanc === true
			},
			{
				id: 'chapeau-jaune',
				label: 'chapeau jaune',
				test: (m: Mushroom) => m.chapeau_couleur_jaune === true
			}
		],
		chart: 'stacked',
		especes: ['AMANITE TUE-MOUCHES', 'AMANITE PHALLOÏDE', 'AGARIC DES JACHÈRES'],
		aFaire: [
			"Croiser systématiquement la couleur avec : forme du pied, anneau/volve, odeur",
			"Photographier la couleur en lumière naturelle (la lumière LED fausse les teintes)",
			"Vérifier si la couleur change avec la pluie ou la maturité"
		],
		aEviter: [
			"Conclure « blanc = pur, sain » — l'Amanite phalloïde est blanchâtre à verdâtre",
			"Conclure « rouge = poison » — l'Amanite tue-mouches est rouge mais pas mortelle",
			"S'arrêter à la couleur dominante : observe aussi les nuances et les marges"
		],
		conclusion:
			"La couleur n'est qu'un indice parmi d'autres. C'est la combinaison de critères (couleur + pied + lames + odeur) qui permet une identification fiable."
	},
	{
		id: 'odeur-saveur',
		numero: 6,
		icon: '👃',
		titre: 'Sentir et goûter',
		sousTitre: 'Tests sensoriels avec précaution',
		intro:
			"Deux sens à entraîner. **L'odeur** : les champignons à odeur désagréable (phénol, iode, terre) sont plus risqués en moyenne ; anisé/amande tend vers la comestibilité. **La saveur** : poser la chair sur la pointe de la langue puis recracher — amère, piquante ou poivrée = test fiable de toxicité (à condition de bien recracher).",
		predicates: [
			{
				id: 'odeur-desagreable',
				label: 'odeur phénol/iode/désagréable',
				test: (m: Mushroom) =>
					m.odeur_type_phenol === true ||
					m.odeur_type_iode === true ||
					m.odeur_type_desagreable === true
			},
			{
				id: 'odeur-anise',
				label: 'odeur anisée/amande',
				test: (m: Mushroom) => m.odeur_type_anise === true || m.odeur_type_amande === true
			},
			{
				id: 'saveur-amere',
				label: 'saveur amère/piquante/poivrée',
				test: (m: Mushroom) =>
					m.saveur_type_amere === true ||
					m.saveur_type_piquante === true ||
					m.saveur_type_poivree === true
			}
		],
		chart: 'stacked',
		especes: ['AGARIC DES JACHÈRES', 'RUSSULE ÉMÉTIQUE', 'AMANITE PHALLOÏDE'],
		aFaire: [
			"Frotter légèrement la chair pour libérer les arômes",
			"Pour le test de saveur : poser sur la langue 5 secondes, puis cracher et rincer",
			"Noter les odeurs « chimiques » comme un signal fort"
		],
		aEviter: [
			"Avaler le test de saveur — jamais, même chez un comestible présumé",
			"Conclure « bonne odeur = comestible » : la Phalloïde a une odeur agréable",
			"Tester la saveur d'un champignon dont la silhouette ressemble à une Amanite"
		],
		conclusion:
			"Une odeur chimique ou une saveur amère/piquante = on laisse. Une odeur agréable et une saveur douce ne suffisent **pas** à valider la comestibilité — il faut combiner avec les étapes précédentes."
	},
	{
		id: 'recapitulatif',
		numero: 7,
		icon: '✅',
		titre: 'Récapitulatif',
		sousTitre: 'La check-list décisionnelle',
		intro:
			"Synthèse des signaux les plus forts du dataset. Les trois premiers critères (volve/anneau, pores rouges, saveur amère) sont les plus discriminants : si l'un d'eux est positif, la probabilité de toxicité ou de mortalité est nettement supérieure à la moyenne. À l'inverse, l'odeur anisée/amande est associée à des espèces plus souvent comestibles.",
		predicates: [
			{
				id: 'recap-rouge',
				label: 'volve OU anneau',
				test: (m: Mushroom) => m.pied_morpho_volve === true || m.pied_morpho_anneau === true
			},
			{
				id: 'recap-pores',
				label: 'pores rouges/orange',
				test: (m: Mushroom) =>
					m.pores_couleur_rouge === true || m.pores_couleur_orange === true
			},
			{
				id: 'recap-saveur',
				label: 'saveur amère/piquante',
				test: (m: Mushroom) =>
					m.saveur_type_amere === true ||
					m.saveur_type_piquante === true ||
					m.saveur_type_poivree === true
			},
			{
				id: 'recap-odeur-bonne',
				label: 'odeur anisée/amande',
				test: (m: Mushroom) => m.odeur_type_anise === true || m.odeur_type_amande === true
			}
		],
		chart: 'stacked',
		especes: ['AMANITE PHALLOÏDE', 'CÈPE DE BORDEAUX', 'BOLET SATAN'],
		aFaire: [
			"Suivre les étapes 1→6 dans l'ordre, sans en sauter",
			"Au moindre doute après l'étape 3 (volve/anneau) : abandonner cette espèce",
			"Faire vérifier sa cueillette par un pharmacien mycologue avant consommation"
		],
		aEviter: [
			"Se fier à un seul critère, même très discriminant",
			"Cueillir des espèces fermées (boutons) : trop jeunes pour être identifiées",
			"Garder une espèce « pour vérifier plus tard » dans le panier des comestibles"
		],
		conclusion:
			"Aucun critère pris isolément ne suffit. Le guide t'apprend à **combiner les indices** : c'est la convergence de plusieurs signaux qui permet de cueillir en sécurité."
	}
];
