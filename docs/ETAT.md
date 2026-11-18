# État de reprise

## Exécution du 18 novembre 2026

- Dépôt canonique public `fahimahmedb/GTA6`, ID `1463085173`. Branche `feature/automation-mvp`. Parent de cette exécution `d2f0a12c43e956ed8fcbd936bcafe701c277bd53`. Utiliser le HEAD distant pour le SHA du lot courant.
- `python3 tools/pipeline.py run` exécuté avec accès HTTP réel. Cinq pages primaires en HTTP 200, sept faits vérifiés par expressions et empreintes d'extraits, trois liens Newswire découverts. La sortie annoncée en France était le 19 novembre à minuit. L'annonce expire à `2026-11-18T23:00:00Z`. P04 disponibilité France est bloqué jusqu'à une preuve sur un store France.
- Sept clips 9:16, 1080×1920, H.264 yuv420p, 30 ips, audio AAC silencieux et durées 13–15 s. Le nom éditorial a été aligné sur le compte observé. P02 SHA-256 `b6baf06020881b6dac097fa131f6730bd7ba6af0e59209a14fd287d2442e152d` dans le runtime vérifié. Relance réelle sans nouveau rendu sur les sept révisions. La file locale contient 24 lignes, dont 21 destinées aux sept packs et trois bloquées pour P04. Les créneaux lointains marqués `RECHECK` appellent une nouvelle collecte. Voir [la commande de reprise](../README.md).
- `python3 -m unittest discover -s tests -v` a réussi 11 tests, dont rejet d'une date contradictoire, relance de la file, canal différent et réponse perdue après création simulée. `python3 tools/metrics.py output/pipeline/metriques-vierge.csv` a retourné zéro observation native. Les médianes ne sont calculées qu'à partir de valeurs observées sur une même plateforme et fenêtre. Veille et exports sont exécutables à la demande. Aucun déclencheur récurrent activé.

## Accès et preuve

| Canal | Statut observé | Suite |
| --- | --- | --- |
| TikTok `@gtavieditfr` | Session vérifiée dans Studio. P02 importé en 1080p, prévisualisé à 15 s et légendé dans le formulaire. Aucun clic de publication, aucun reçu de brouillon persistant, pas d'ID natif. | Reprendre l'onglet déjà préparé. Si le formulaire a expiré, réimporter le MP4 P02 et la légende associée. Éviter une création parallèle pendant que ce formulaire est ouvert. |
| YouTube Shorts | Création du compte déclarée. Sept exports locaux. Canal authentifié, brouillon, publication et lecture métrique UNKNOWN. | Vérifier le canal créé, réutiliser le MP4 P02 avec le titre et la description YouTube. |
| Instagram Reels | Création du compte déclarée. Sept exports locaux. Canal authentifié, brouillon, publication et lecture métrique UNKNOWN. | Vérifier le compte et le mode de dépôt, puis utiliser la variante Instagram. |
| Buffer | API non authentifiée. `buffer_draft.py channels` a remonté l'absence de `BUFFER_API_KEY`. Métadonnées et déduplication qualifiées localement. | Tester la lecture réelle du compte si une connexion dédiée est disponible. Le mode natif ne requiert pas de clé Buffer. |

Dans le bilan, regrouper uniquement les identités/connexions qui manquent et la décision de diffusion si elle reste requise. En cas de confirmation, rechercher d'abord une preuve native du post, puis lire les métriques aux fenêtres H+12, H+24 et H+72.
