# État de reprise

## Dernier lot — préparation du 18 novembre 2026

- Dépôt `fahimahmedb/GTA6`, ID `1463085173`, public. Branche par défaut `Claude` observée à `1674a7a08f57f3c40630ad462112db484a1352a2`. Branche de travail avant ce lot `feature/automation-mvp` à `612b8db6d467f45aa960cbd57670d20bb0a35b98`. Lire le HEAD distant pour l'identité exacte du lot qui contient ce fichier.
- Sources vues : [page GTA VI](https://www.rockstargames.com/VI), [horaires Rockstar](https://support.rockstargames.com/articles/29jV3Cv2cCgvwM1XgtMO5o/grand-theft-auto-vi-regional-pre-load-and-release-times-on-playstation-5-and-xbox-series-x-or-s), [Take-Two du 9 novembre](https://www.take2games.com/ir/news/take-two-interactive-software-inc-reports-results-fiscal-4). Le créneau annoncé pour Paris était `2026-11-18T23:00:00Z`. Disponibilité réelle le jour J à revérifier. P01 expire au créneau annoncé.
- `python3 tools/render_seeds.py` exécuté sur les trois sujets. Sorties dans `output/seeds/`, régénérables. FFprobe a vérifié 1080×1920, 30 fps, H.264 yuv420p, AAC, durées 14/15/15 s. Piste silencieuse, textes incrustés. Chaque pack comprend les sources, un SRT et les trois variantes de légendes. Rendu répété sur P02 avec SHA-256 identique dans le même runtime. Saisie d'une référence factuelle inexistante rejetée sans créer de pack.

| Pack | SHA-256 du MP4 produit |
| --- | --- |
| P01 | `6fc6dca9c34046f8ed8208a1aa6a9e09474774cba1c989a6e5664707c08ab8fa` |
| P02 | `03eeaa120277d2bba2cf0d855cb531f27f884bf7b1526e416377cc544d1a8221` |
| P03 | `831798ddf0811ff02b7180185b1b67ba750437a88d5c537f482c41280b45f288` |

## Accès et niveaux de preuve

| Surface | Observé | Prochaine exécution |
| --- | --- | --- |
| GitHub | Lecture de la branche et accès d'écriture annoncé par le connecteur. Le CLI local était non authentifié pour écrire. | Vérifier HEAD et diff, utiliser les permissions disponibles, pousser par lots vérifiés. |
| YouTube Shorts | Variantes et vidéo locales. Canal GTA VI, brouillon et diffusion distants UNKNOWN. | Lire les canaux autorisés et essayer le parcours le plus avancé applicable. |
| Instagram Reels | Variantes et vidéo locales. Compte pro GTA VI et autopublication distants UNKNOWN. | Vérifier type du compte et mode disponible. |
| TikTok | Variantes et vidéo locales. Compte GTA VI et publication distants UNKNOWN. | Vérifier le canal dédié et son mode. |
| Buffer / Metricool | Documentation Buffer consultée. Aucun compte Buffer validé. La lecture Metricool n'a pas identifié de marque dédiée GTA VI. Aucune action sociale écrite. | Réexaminer les accès, poursuivre localement en parallèle. |
| Veille, file, métriques | Sources consultées pour le lot initial. Collecteur récurrent, file réconciliable et import métriques à construire. | Lots B, C/D, E de [PLAN.md](PLAN.md). |

## Prochaine action

Se placer sur la branche, comparer le HEAD, lancer `python3 tools/render_seeds.py` si nécessaire et démarrer [le plan](PLAN.md). Revalider les faits sensibles avant tout usage externe. Après un obstacle de compte, finir les autres lots. Remplacer cet état avec la preuve atteinte pour chaque canal et intégrer les interventions humaines restantes au seul bilan final.
