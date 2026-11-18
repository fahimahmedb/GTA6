# État de reprise au 18 novembre 2026

Dépôt `fahimahmedb/GTA6`, ID `1463085173`, branche `feature/automation-mvp`. Le parent de la correction éditoriale est le commit [4aef176](https://github.com/fahimahmedb/GTA6/commit/4aef176a08182f2cb9159273b8042a6fcdefc3e1). Il conserve les résultats du premier rendu et de la veille.

## Ce qui est effectivement en ligne

| Canal | Preuve | Reprise |
| --- | --- | --- |
| TikTok `@gtavieditfr` | P02 « Vice City ou Leonida ? » a reçu l’ID natif `7709565918271114518`. La page vidéo s’ouvrait, puis Studio indiquait « Everyone » après vérification. Les vues, mentions J’aime et commentaires affichaient zéro au constat initial. [Post public](https://www.tiktok.com/@gtavieditfr/video/7709565918271114518) | Conserver cet ID pour les métriques. Aucune réimportation ou diffusion d’une seconde copie. Ce constat initial ne permet pas d’évaluer sa réception. |
| YouTube Shorts et Instagram Reels | Comptes créés selon le propriétaire. Aucune diffusion de ce lot observée sur ces réseaux. | Garder les sept anciens exports hors des deux canaux. |
| Buffer | Aucun accès authentifié établi lors du lot initial. Un test local du sous-ordre de brouillon a vérifié le rejet d’une maquette avant l’appel de création. | Le test local couvre le code. Un accès réel reste à qualifier si cette route est choisie. |

## Décision éditoriale et travail livré

- P02 avait trois écrans fixes de 4, 5 et 6 secondes. Son MP4 portait le SHA-256 `b6baf06020881b6dac097fa131f6730bd7ba6af0e59209a14fd287d2442e152d`. La détection de silence à −65 dB couvrait toute la piste. Le propriétaire a rejeté ce traitement.
- Les sept rendus du premier ZIP sont des maquettes techniques. Cette ancienne archive est périmée pour tout usage de diffusion. Lors de la relance sur la base existante, cinq sources ont répondu HTTP 200, sept faits ont passé les vérifications et la file comptait **21 lignes PREVIEW_ONLY**, **3 BLOCK** pour P04 et **zéro créneau proposé**. La commande d’export a refusé de créer un ZIP.
- Le [benchmark](../editorial/REFERENCES.md) renvoie aux posts originaux, décrit les plans réellement vérifiés et les limites des compteurs. Le [pilote Ocean Drive](../editorial/OCEAN_DRIVE.md) met en pratique le rapprochement visuel. Son MP4 a été remis au propriétaire en privé avec voix française, son original et crédit photo. SHA-256 `c11573b95da1fd89a249868a404a85dc7b90cafa166c76856f1b13c03d0ce4dc`. Il reste hors des trois files publiques.
- La file, la constitution du kit et le brouillon Buffer contrôlent désormais la revue éditoriale du média. Pour un montage réellement qualifié, le manifeste porte `state=APPROVED` et une `editorial_review` avec le SHA-256 de la vidéo, `visual_evidence` et `rights_reference`. Cette référence documente les destinations couvertes. Le kit commun aux trois plateformes exige que les médias soient utilisables sur chacune. Les formulaires natifs restent sous contrôle de l’opérateur. Un changement de libellé sur une maquette ne constitue pas une revue.

## Prochaine action

Les seize tests unitaires sont passés. Ils incluent la relance sur une ancienne file, la non-création d’un brouillon Buffer à partir d’une maquette, le refus de l’ancien kit et un export nominal sur un montage témoin qualifié.

Pour une nouvelle demande de montage, reprendre les images et le conducteur de l’épisode, ou tourner l’essai radio à pied décrit dans les références. Pour une éventuelle demande de publication, identifier le clip demandé, sa révision et le canal, vérifier la portée des droits pour cet usage, puis relire l’état natif du bon compte après envoi. Le mandat de publication donné pour P02 a déjà été exécuté. Aucun déclencheur récurrent activé.

Commandes de contrôle depuis la racine.

```bash
python3 -m unittest discover -s tests -v
python3 tools/pipeline.py run
```
