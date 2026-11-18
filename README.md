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
