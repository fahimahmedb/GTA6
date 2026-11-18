"""Package the locally verified assets for native upload from a phone or computer."""

import argparse
import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from pipeline import OUTPUT, load_json, parse_time, reviewed_master, utcnow
from render_seeds import PLATFORMS

INTRO = """GTA VI EDIT FR
Kit de lancement

Pour chaque réseau, utilise video.mp4 et le texte du fichier tiktok.txt, instagram.txt ou youtube.txt.
Chaque dossier contient aussi cover.jpg, subtitles.srt et un manifeste avec les sources.

Le planning est une proposition en heure de Paris. RECHECK demande de relire les sources.
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
    now = utcnow()
    approved = {}
    for post_id, entry in queue["posts"].items():
        if entry["state"] != "READY_LOCAL":
            continue
        if not entry.get("source_until") or parse_time(entry["source_until"]) <= now:
            continue
        if entry.get("expires_at") and parse_time(entry["expires_at"]) <= now:
            continue
        directory = args.input / entry["pack"]
        manifest = load_json(directory / "manifest.json")
        if not reviewed_master(manifest):
            continue
        digest = hashlib.sha256((directory / "video.mp4").read_bytes()).hexdigest()
        if digest != entry["sha256"] or digest != manifest["sha256"]:
            raise ValueError(f"{post_id}: unexpected video digest")
        approved[post_id] = directory
    if not approved:
        parser.exit(1, "PREVIEW_ONLY: aucun montage validé à exporter.\n")

    args.kit.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=args.kit.parent, delete=False) as temporary:
        temp_path = Path(temporary.name)
    try:
        with ZipFile(temp_path, "w", compression=ZIP_DEFLATED) as kit:
            kit.writestr("A_LIRE.txt", INTRO)
            for name in ("planning.csv", "metriques-vierge.csv", "sources.json"):
                kit.write(args.input / name, name)
            names = ("video.mp4", "cover.jpg", "subtitles.srt", "manifest.json", *(f"{p}.txt" for p in PLATFORMS))
            for post_id, directory in approved.items():
                for name in names:
                    kit.write(directory / name, f"{post_id}/{name}")
        temp_path.replace(args.kit)
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
