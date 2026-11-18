# GTA VI — automatisation éditoriale

Produire des vidéos verticales francophones sur GTA VI avec des sources vérifiables, une identité indépendante et des visuels utilisables. Cibles : TikTok, Instagram Reels, YouTube Shorts.

## Reprendre le projet

Commencer par [AGENTS.md](AGENTS.md), puis suivre le [plan d'exécution](docs/PLAN.md) et le [guide éditorial](editorial/PLAYBOOK.md). Le [point de reprise](docs/ETAT.md) indique le dernier résultat observé. Le [lot initial](editorial/seed.json) contient les sources, les scènes et les textes par plateforme.

Depuis la racine, avec Python 3.10+, FFmpeg et FFprobe, le filtre `ass` et la police DejaVu Sans :

```bash
python3 tools/render_seeds.py
```

Les trois répertoires produits sous `output/seeds/` contiennent un MP4, les sous-titres, les textes par plateforme, les sources et les résultats de contrôle. Ces aperçus servent à qualifier le montage. Le plan décrit la revalidation éditoriale avant diffusion et la suite du moteur.

Le dépôt public conserve le code, les sources publiques, les décisions et les preuves expurgées. La chaîne de publication et ses accès distants sont à qualifier.

## Exécuter la veille et régénérer le kit

```bash
python3 tools/pipeline.py run
python3 -m unittest discover -s tests -v
python3 tools/metrics.py output/pipeline/metriques-vierge.csv
```

`run` lit les pages publiques, contrôle les affirmations du catalogue et exporte les packs, les couvertures et une file de sept jours sous `output/pipeline/`. Les créneaux expirés ou les sources trop anciennes pour le créneau restent à traiter. Une nouvelle URL Newswire devient une piste à rédiger. `refresh` ne fait que la collecte et `plan` relit le dernier instantané sans accès réseau. Une relance réutilise les rendus dont l'empreinte ancre la révision. Conserver la base locale pour les relances dans le même environnement.

Le compte TikTok observé dans Studio est `@gtavieditfr`. La première vidéo P02 est importée et légendée dans l'onglet ouvert. Le formulaire web de cette session affiche les actions de publication et d'abandon, sans reçu de brouillon durable. Se reporter à [l'état de reprise](docs/ETAT.md) avant toute nouvelle mise en file de P02.

L'adaptateur [Buffer](https://developers.buffer.com/guides/getting-started.html) exige une clé fournie au runtime et le canal dédié. `python3 tools/buffer_draft.py channels` interroge les canaux en lecture seule. Le sous-ordre `draft --help` précise les paramètres pour un brouillon autorisé, dont le handle exact et l'URL HTTPS directe d'un MP4 identique au rendu. En l'absence d'hébergement compatible, utiliser l'import natif. Avant d'activer une programmation réelle, qualifier la route de diffusion, la visibilité et les métriques avec un ID natif.
