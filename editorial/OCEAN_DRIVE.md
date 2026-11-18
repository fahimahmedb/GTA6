# Ocean Drive, pourquoi l’hôtel a changé de nom

**Pilote monté pour visionnage privé.** Un détail en treize secondes. Sur la vraie Ocean Drive, la tour porte le nom Victor. Dans GTA VI elle porte le nom Dixon. Lawrence Murray Dixon a conçu le véritable hôtel. La comparaison entre les deux façades est documentée par le responsable de la Miami Design Preservation League interrogé par Axios et par un reportage de l’Associated Press. [Axios Miami](https://www.axios.com/local/miami/2023/12/05/gta-6-trailer-vice-city-landmarks) · [Associated Press](https://apnews.com/article/grand-theft-auto-vi-miami-vice-city-1441b5de7d3f458ad08626193d645a46)

## Montage livré

| Temps | Ce que voit le spectateur | Voix et son |
| --- | --- | --- |
| 0–1,5 s | La rue en mouvement, un cabriolet turquoise et les néons de la bande-annonce. Question sur la façade. | « Pourquoi cet hôtel a changé de nom dans le jeu ? » |
| 1,5–2,55 s | Les deux tours l’une au-dessus de l’autre, avec leurs lieux indiqués. | La question se termine sur le premier raccord. |
| 2,55–6,35 s | La vraie façade en lumière du soir. Le rapprochement rend VICTOR lisible. | « À Miami Beach, sur Ocean Drive, c’est l’hôtel Victor. » |
| 6,35–9,70 s | Retour à Vice City sous la pluie, déplacement du cadre jusqu’aux lettres bleues HOTEL DIXON. | « Dans Vice City, lis le néon bleu. Dixon. » |
| 9,70–13,20 s | Les enseignes restent visibles, le nom complet de l’architecte apparaît entre les deux plans. | « C’est le nom de l’architecte du vrai bâtiment. » Courte retombée du motif musical. |

Le MP4 remis en privé porte le SHA-256 `c11573b95da1fd89a249868a404a85dc7b90cafa166c76856f1b13c03d0ce4dc`. Rendu contrôlé à 1080 × 1920, 396 images, 30 i/s, H.264 et AAC 48 kHz. Sur le fichier décodé, le mix atteint −16,7 LUFS intégrés et −1,5 dBTP. Le fichier livré mesure 5 532 540 octets. Les recadrages et textes ont été vérifiés à huit instants du MP4.

## Sources de production

| Entrée | Source et traitement |
| --- | --- |
| Rue en mouvement | Rockstar Games, *Grand Theft Auto VI Trailer 1*, 32,57 à 34,07 s. Reprendre la version de l’espace média. La piste originale est coupée. [Bande-annonce](https://www.rockstargames.com/VI/trailer-1) · [MP4 officiel](https://media-rockstargames-com.akamaized.net/VI/downloads/videos/GTAVI_Trailer_1/GTAVI_Trailer_1.mp4) |
| Enseigne Dixon | Rockstar Games, image de fond officielle de la rubrique Musique, 3840 × 2160. Empreinte `b926af3c0bec3ec7f830a0ae3584da579b465dd676bac3e7498caa924116edc3`. [Rubrique](https://www.rockstargames.com/VI/music) · [Image utilisée](https://www.rockstargames.com/VI/_next/static/media/album-background-desktop.0sxn7hogv.8xn.jpg) |
| Enseigne Victor | Dan Lundberg, *20111001 1498 South Beach Hotel Victor dusk (2)*, photographie originale du 1er octobre 2011, 3648 × 2736. Recadrages animés, crédit dans les plans et dans les métadonnées. Les adaptations de cette photo sont proposées sous CC BY-SA 2.0. Empreinte `52b8834793e738271df2522fbfc5a487948366bb2718d3d5ff1c0cd59c76972e`. [Photo et notice](https://commons.wikimedia.org/wiki/File:20111001_1498_South_Beach_Hotel_Victor_dusk_(2).jpg) · [Licence](https://creativecommons.org/licenses/by-sa/2.0/) |
| Son | Percussions, basse et synthétiseur composés pour ce montage. Voix française de synthèse Piper SIWIS. Données vocales SIWIS sous CC BY 4.0 selon la fiche du modèle. Modèle utilisé `b1d946fd68d0347155fa59bce0a018924abbef3c1561181db45ca463d83963ef`. [Fiche](https://huggingface.co/rhasspy/piper-voices/blob/main/fr/fr_FR/siwis/medium/MODEL_CARD) |

Pour une diffusion sociale, établir la portée de réutilisation des deux médias Rockstar pour la destination et l’usage envisagés et conserver l’attribution photographique dans la légende même si les métadonnées sont effacées. Rockstar met à disposition des éléments à télécharger et à partager. Sa politique sur les vidéos de fans précise la portée de ses permissions. Le dépôt public contient les références et la recette. Le pilote reste hors de la file de diffusion. [Médiathèque Rockstar](https://www.rockstargames.com/VI/media) · [Politique Rockstar](https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material)

## Reproduire le montage

Placer dans `media/ocean-drive/` la bande-annonce complète sous `trailer.mp4`, l’image de Rockstar sous `dixon.jpg`, la photo originale sous `victor.jpg` et quatre voix mono PCM 16 bits sous `voice/line0.wav` à `voice/line3.wav`. Les textes exacts figurent dans le tableau. Les quatre répliques peuvent être enregistrées au micro. Pour retrouver la variante de synthèse, utiliser Piper 1.8 avec le modèle SIWIS medium, `length_scale=1.04`, `noise_scale=0.53` et `noise_w_scale=0.64`. Une nouvelle prise de voix produit une nouvelle empreinte.

Avec FFmpeg, Python, Pillow, NumPy, SciPy et Open Sans installés, exécuter depuis la racine du dépôt.

```bash
python3 tools/render_ocean_drive.py \
  --trailer media/ocean-drive/trailer.mp4 \
  --game-photo media/ocean-drive/dixon.jpg \
  --real-photo media/ocean-drive/victor.jpg \
  --voice-dir media/ocean-drive/voice \
  --output output/review/GTA_VI_Ocean_Drive.mp4
```

## Textes du pilote

- **TikTok.** « À Miami Beach, il s’appelle Victor. Regarde le nom que Rockstar lui a donné dans GTA VI. #GTA6 #ViceCity #MiamiBeach »
- **Reels.** « Même tour sur Ocean Drive. À Miami, l’enseigne dit Victor. À Vice City, Dixon. C’était le nom de l’architecte de l’hôtel. #GTA6 #ViceCity #ArtDeco »
- **Shorts.** Titre « Pourquoi cet hôtel de Miami change de nom dans GTA VI ». Description « Compare les deux façades sur Ocean Drive. Lawrence Murray Dixon a conçu le véritable hôtel Victor. »
- **Crédit à joindre à chaque variante.** « Images du jeu © Rockstar Games. Photo Victor, “20111001 1498 South Beach Hotel Victor dusk (2)”, Dan Lundberg, recadrée, CC BY-SA 2.0. Sources historiques, Axios Miami et Associated Press. » Ajouter la référence de la photo et le lien de licence dans le champ de description ou de crédits disponible sur le réseau.
