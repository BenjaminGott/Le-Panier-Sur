# Scraping des données — Le Panier-Sûr

Documentation du pipeline d'extraction des données de champignons depuis le site source.

- **Source** : `https://www.guidedeschampignons.com`
- **Notebook** : `etl/scraping/scrap.ipynb`
- **Sorties** :
  - `data/raw/champignons_data.csv` — données textuelles (219 lignes × 17 colonnes)
  - `data/raw/champignons_images.csv` — images encodées en base64 (219 lignes × 3 colonnes)

---

## 1. Vue d'ensemble du pipeline

```
https://www.guidedeschampignons.com
    │
    ├─ 1. Listing des champignons (3 pages d'index)
    │      → liste d'URLs vers les fiches produit
    │
    ├─ 2. Scraping fiche par fiche
    │      → requête HTTP + parsing HTML (BeautifulSoup)
    │      → extraction : nom, image, nom scientifique, synonyme,
    │        statut, 10 caractéristiques descriptives, catégories
    │      → téléchargement + encodage base64 de l'image principale
    │
    └─ 3. Export double CSV
           ├─ champignons_data.csv   (texte, sans image_base64)
           └─ champignons_images.csv (nom + image_url + image_base64)
```

Librairies utilisées : `requests`, `beautifulsoup4`, `pandas`, `base64`.

---

## 2. Étape 1 — Listing des fiches

Le site liste tous les champignons paginés sur `/tous-les-champignons/page/{N}`. Sur chaque page, les liens vers les fiches individuelles sont contenus dans des éléments de classe `h5`.

```python
page_tabe = [1, 2, 3]
class_ = "h5"
```

**Logique** :
1. Requête `GET` sur chaque page d'index.
2. Parsing du HTML avec BeautifulSoup.
3. Recherche de tous les éléments de classe `h5`.
4. Pour chaque élément : extraction des balises `<a>` internes (nom + lien).

**Sortie** : liste `data` de dicts `{"text": <nom>, "href": <url_fiche>}`, une entrée par champignon à scraper.

> Si le site ajoute des pages, étendre `page_tabe = [1, 2, 3, 4, …]`.

---

## 3. Étape 2 — Scraping d'une fiche

Deux fonctions principales :

### `get_image_base64(url)`

Télécharge l'image depuis son URL, récupère son `Content-Type`, encode les octets en base64 et renvoie une data URI :

```
data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/...
```

Format utilisable directement dans une balise `<img>` HTML ou pour un stockage portable. Timeout de 10 secondes.

### `scrape_champignon(url)`

Fonction principale : parcourt une fiche produit et extrait toutes les informations. Retourne un dict prêt à être converti en ligne de DataFrame.

Structure de la page ciblée (site WooCommerce) :

| Élément HTML | Donnée extraite |
|---|---|
| `<h1 class="product_title">` | `nom` |
| `<div class="woocommerce-product-gallery__image-first">` → `<a href>` | `image_url` + `image_base64` |
| `<div class="woocommerce-product-details__short-description">` | bloc principal de description |
| `<span class="posted_in">` | `categories` |

### Parsing du bloc `short-description`

Ce bloc contient plusieurs `<p>`. Chacun suit un format régulier :

```
<p><strong>CHAPEAU :</strong> 5 à 25 cm, couvert de mèches brun-roux…</p>
```

**Algorithme** :
1. `paragraphs = desc.find_all("p")` — récupère tous les paragraphes.
2. **Premier paragraphe** :
   - Le premier `<strong>` contient le `nom_scientifique`.
   - Le texte après le `<br>` contient le `synonyme` (détecté par la présence de "ynon" — pour "synonyme"/"Synonyme"/"SYNONYME").
   - Certains champignons ont le badge `statut` dans une `<img>` au premier paragraphe (lu via l'attribut `alt`).
3. **Deuxième paragraphe** : badge statut (image `alt`) OU texte libre si ce n'est pas un champ descriptif.
4. **Paragraphes suivants** : pour chaque `<p>`, on cherche dans les balises `<strong>` **et** `<b>` (variations HTML du site) une clé parmi `CHAMPS = [CHAPEAU, PORES, LAMES, PIED, CHAIR, ODEUR, SAVEUR, HABITAT, SAISON, CONFUSION]`. La valeur est le texte du paragraphe moins la clé.
5. Cas spécial `CONFUSION` : on extrait les noms des espèces liées (balises `<a>`) plutôt que le texte brut.

### Gestion des erreurs

Chaque fiche est encapsulée dans un `try / except` : si une fiche échoue (404, timeout, structure HTML anormale), l'erreur est loggée et la boucle continue. Les fiches réussies sont ajoutées à `records`.

### Politesse

`time.sleep(0.5)` entre chaque fiche pour limiter la charge sur le serveur source (≈ 2 requêtes/seconde).

---

## 4. Étape 3 — Export

Deux fichiers sont produits pour séparer les responsabilités :

### `champignons_data.csv` (17 colonnes)

Données textuelles uniquement (les images sont exclues car trop volumineuses pour un CSV exploitable).

| Colonne | Contenu |
|---|---|
| `url` | URL de la fiche source |
| `nom` | Nom commun (ex. `AGARIC AUGUSTE`) |
| `image_url` | URL de l'image (référence) |
| `nom_scientifique` | Ex. `Agaricus augustus` |
| `synonyme` | Autres noms (ex. `agaric impérial`) |
| `statut` | Libellé de dangerosité / comestibilité |
| `chapeau` | Description textuelle |
| `pores` | Description textuelle |
| `lames` | Description textuelle |
| `pied` | Description textuelle |
| `chair` | Description textuelle |
| `odeur` | Description textuelle |
| `saveur` | Description textuelle |
| `habitat` | Description textuelle |
| `saison` | Format `"Mois > Mois"` |
| `confusion` | Liste de champignons similaires (sert d'alerte, pas d'input modèle) |
| `categories` | Tags source (liste séparée par virgules) |

### `champignons_images.csv` (3 colonnes)

- `nom`
- `image_url`
- `image_base64` — data URI complète (`data:image/jpeg;base64,…`)

Ce fichier sera consommé indépendamment par un pipeline image (CNN) quand il sera en place.

---

## 5. Dépendances et configuration

```python
import requests
import base64
import time
import os
from bs4 import BeautifulSoup
import pandas as pd
```

Packages à installer (voir `requirements.txt` du projet) :
- `requests`
- `beautifulsoup4`
- `pandas`

**Timeouts** : 10 secondes par requête image, pas de timeout explicite sur les fiches (défaut `requests`).

---

## 6. Points d'attention / limitations

- **Structure HTML figée** : le parseur dépend fortement des classes CSS et de l'ordre des `<p>`. Si le site évolue, les sélecteurs doivent être mis à jour (voir les `find(…)` / `find_all(…)` dans `scrape_champignon`).
- **Variantes `<strong>` vs `<b>`** : déjà gérées, mais si d'autres balises apparaissent (`<em>`, `<span class>`), il faudra enrichir la liste.
- **Synonyme** : détecté via la sous-chaîne `"ynon"` pour être case-insensitive et tolérer "synonyme"/"Synonyme"/"SYNONYMES". Fragile si le site change le libellé.
- **Doublons** : le listing de pages ne dédoublonne pas — si le même champignon apparaît sur plusieurs pages, il sera scrapé plusieurs fois. À surveiller.
- **Images manquantes** : `get_image_base64` renvoie `None` si l'URL est vide ; en cas d'erreur HTTP elle lève une exception qui remonte au `try/except` externe (toute la fiche est perdue). Possible amélioration : `try/except` autour de l'image seule pour conserver le reste.
- **Rate limiting** : 0.5 s de délai volontaire. À augmenter si le site rate-limite.

---

## 7. Relancer le scraping

```bash
# Depuis etl/scraping/
jupyter nbconvert --to notebook --execute scrap.ipynb
# ou ouvrir scrap.ipynb dans VS Code et exécuter toutes les cellules
```

Les deux CSV sont écrits dans `data/raw/` — les fichiers existants sont écrasés.

---

## 8. Architecture des fichiers

```
Le-Panier-Sur/
├── data/
│   └── raw/
│       ├── champignons_data.csv     ← sortie principale
│       └── champignons_images.csv   ← sortie images (base64)
├── etl/
│   └── scraping/
│       └── scrap.ipynb              ← le notebook
└── docs/
    ├── scraping.md                  ← ce document
    └── transformation.md            ← pipeline aval (nettoyage)
```
