"""Package the locally verified assets for native upload from a phone or computer."""

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pipeline import OUTPUT, load_json, parse_time, utcnow
from render_seeds import PLATFORMS

INTRO = """GTA VI EDIT FR
Kit de lancement

Commence par p02-vice-city-leonida, la vidéo qui présente la différence entre Vice City et Leonida.
Pour chaque réseau, utilise video.mp4 et le texte du fichier tiktok.txt, instagram.txt ou youtube.txt.
Chaque dossier contient aussi cover.jpg, subtitles.srt et un manifeste avec les sources.

Le planning est une proposition en heure de Paris. RECHECK demande de relire les sources.
La vidéo p01-heure-france concerne une annonce pré-lancement. Vérifie son échéance dans le manifeste.
Le dossier de sortie P04 reste en attente d'une confirmation régionale.

TikTok : compte @gtavieditfr.
YouTube et Instagram : utilise le compte dédié que tu viens de créer.
Pour éviter un doublon, vérifie la file de publication du canal avant chaque envoi.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", type=Path)
    parser.add_argument("--input", type=Path, default=OUTPUT)
    args = parser.parse_args()
    queue = load_json(args.input / "queue.json")
    args.kit.parent.mkdir(parents=True, exist_ok=True)
    now = utcnow()
    with ZipFile(args.kit, "w", compression=ZIP_DEFLATED) as kit:
        kit.writestr("A_LIRE.txt", INTRO)
        for name in ("planning.csv", "metriques-vierge.csv", "sources.json"):
            kit.write(args.input / name, name)
        for post_id, entry in queue["posts"].items():
            if entry["state"] != "READY_LOCAL":
                continue
            if entry["expires_at"] and parse_time(entry["expires_at"]) <= now:
                continue
            directory = args.input / entry["pack"]
            video = directory / "video.mp4"
            if hashlib.sha256(video.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"{post_id}: unexpected video digest")
            names = ("video.mp4", "cover.jpg", "subtitles.srt", "manifest.json", *(f"{p}.txt" for p in PLATFORMS))
            for name in names:
                kit.write(directory / name, f"{post_id}/{name}")


if __name__ == "__main__":
    main()
