# Le Panier-Sûr — Application Web & Desktop

> SvelteKit + Tauri · Galerie & identification de champignons

<!-- CAPTURE : screenshot de l'application desktop -->
> _Capture d'écran à ajouter — fenêtre desktop_

---

## Stack technique

| Couche | Technologie |
|--------|------------|
| Framework | SvelteKit 2 / Svelte 5 |
| Desktop | Tauri 2 (Rust) |
| Style | Tailwind CSS 3 |
| Charts | Chart.js 4 |
| ML Runtime | ONNX Runtime Web |
| Parsing CSV | PapaParse |
| Build | Vite 5 |

---

## Prérequis

- [Node.js](https://nodejs.org/) ≥ 22
- [Rust + Cargo](https://rustup.rs/) ≥ 1.95 *(build desktop uniquement)*
- MSVC Build Tools 2022 *(Windows, build desktop uniquement)*

---

## Installation

```powershell
cd web\frontend
npm install
```

---

## Commandes

| Commande | Description |
|----------|-------------|
| `npm run dev` | Serveur de développement web (localhost:5173) |
| `npm run build` | Build de production web statique |
| `npm run preview` | Prévisualiser le build de production |
| `npm run tauri dev` | Application desktop avec hot-reload |
| `npm run tauri build` | Build `.exe` + installeurs Windows |
| `npm run check` | Vérification TypeScript / Svelte |

---

## Pages

| Route | Description |
|-------|-------------|
| `/` | Galerie des champignons avec recherche et filtres |
| `/champignon/[slug]` | Fiche détaillée d'une espèce |
| `/predict` | Identification par caractéristiques (modèle XGBoost / ONNX) |
| `/stats` | Statistiques & visualisations (habitats, saisons, dangerosité) |
| `/astuces` | Guide de cueillette avec quiz interactif |

### Galerie

<!-- CAPTURE : page d'accueil — galerie avec filtres -->
> _Capture à ajouter_

### Fiche espèce

<!-- CAPTURE : page /champignon/[slug] -->
> _Capture à ajouter_

### Prédiction

<!-- CAPTURE : page /predict avec résultats -->
> _Capture à ajouter_

### Statistiques

<!-- CAPTURE : page /stats -->
> _Capture à ajouter_

---

## Build Desktop (.exe)

```powershell
npm run tauri build
```

Artefacts générés dans `src-tauri/target/release/` :

| Fichier | Description |
|---------|-------------|
| `le-panier-sur.exe` | Exécutable brut |
| `bundle/msi/Le Panier-Sûr_0.1.0_x64_en-US.msi` | Installeur MSI |
| `bundle/nsis/Le Panier-Sûr_0.1.0_x64-setup.exe` | Installeur NSIS |

### Mettre à jour l'icône

1. Modifier `src-tauri/icons/source.png` (PNG 1024×1024)
2. Régénérer toutes les tailles :
   ```powershell
   npx @tauri-apps/cli icon src-tauri\icons\source.png
   ```
3. Relancer `npm run tauri build`

---

## Structure des fichiers

```
web/frontend/
├── src/
│   ├── lib/
│   │   ├── components/         # Composants Svelte réutilisables
│   │   │   ├── SearchBar.svelte
│   │   │   ├── FilterSidebar.svelte
│   │   │   ├── MushroomCard.svelte
│   │   │   ├── charts/         # Chart.js wrappers
│   │   │   └── ...
│   │   └── stores/             # Svelte stores (filtres, état global)
│   └── routes/                 # Pages SvelteKit
│       ├── +page.svelte        # Galerie (/)
│       ├── champignon/[slug]/  # Fiche espèce
│       ├── predict/            # Prédiction ML
│       ├── stats/              # Statistiques
│       └── astuces/            # Guide & quiz
├── static/
│   ├── data/                   # CSVs (champignons_clean.csv, meta JSON)
│   ├── img/                    # Photos des espèces
│   └── models/                 # Modèle ONNX + features/labels JSON
├── src-tauri/                  # Configuration Tauri (Rust)
│   ├── tauri.conf.json
│   ├── icons/                  # Icônes de l'application
│   └── src/                    # Code Rust (minimal)
├── package.json
├── svelte.config.js
├── vite.config.ts
└── tailwind.config.js
```

---

## Données

Les fichiers de données ne sont pas versionnés (voir `.gitignore`). Pour les régénérer :

```powershell
# Depuis la racine du projet
conda activate le_panier_sur
jupyter notebook  # Lancer etl/scraping → transform → augment
```

Puis copier les fichiers générés dans `static/data/` et `static/models/`.
