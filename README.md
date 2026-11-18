# GTA VI — automatisation éditoriale

Produire des vidéos verticales francophones sur GTA VI avec des sources vérifiables, une identité indépendante et des visuels utilisables. Cibles : TikTok, Instagram Reels, YouTube Shorts.

## Reprendre le projet

Commencer par le [point de reprise](docs/ETAT.md), les [exemples GTA étudiés](editorial/REFERENCES.md) et la [fiche du pilote Ocean Drive](editorial/OCEAN_DRIVE.md), avec ses sources et sa commande de montage. Le [mandat](AGENTS.md), le [plan d’exécution](docs/PLAN.md) et le [guide éditorial](editorial/PLAYBOOK.md) décrivent la suite.

Depuis la racine, avec Python 3.10+, FFmpeg et FFprobe, le filtre `ass` et la police DejaVu Sans :

```bash
python3 tools/render_seeds.py
```

Les trois répertoires produits sous `output/seeds/` contiennent un MP4, les sous-titres, les textes par plateforme, les sources et les résultats de contrôle. Ces aperçus servent à qualifier le montage. Le plan décrit la revalidation éditoriale avant diffusion et la suite du moteur.

Le dépôt public conserve le code, les sources publiques, les décisions et les preuves expurgées. La chaîne de publication et ses accès distants sont à qualifier.

## Exécuter la veille et contrôler la file

```bash
python3 tools/pipeline.py run
python3 -m unittest discover -s tests -v
python3 tools/metrics.py output/pipeline/metriques-vierge.csv
```

`run` contrôle les sources, produit les aperçus et actualise le planning dans `output/pipeline/`. Les sept maquettes sont marquées `PREVIEW_ONLY`, sans créneau ni export vers un kit de lancement ou Buffer. Les accès natifs suivent la même décision éditoriale. Une URL Newswire nouvelle devient une piste à rédiger. `refresh` collecte et `plan` relit le dernier instantané sans accès réseau. Conserver la base locale pour les relances.

Le premier TikTok P02 est [public sur @gtavieditfr](https://www.tiktok.com/@gtavieditfr/video/7709565918271114518). Le nouveau montage Ocean Drive a été remis en vidéo privée à visionner.

L'adaptateur [Buffer](https://developers.buffer.com/guides/getting-started.html) exige une clé fournie au runtime et le canal dédié. `python3 tools/buffer_draft.py channels` interroge les canaux en lecture seule. Le sous-ordre `draft --help` précise les paramètres pour un brouillon autorisé, dont le handle exact et l'URL HTTPS directe d'un MP4 identique au rendu. En l'absence d'hébergement compatible, utiliser l'import natif. Avant d'activer une programmation réelle, qualifier la route de diffusion, la visibilité et les métriques avec un ID natif.
