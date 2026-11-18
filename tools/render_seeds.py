"""Render sourced editorial previews locally, with no network or publishing access."""

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTES = {
    "coral": ("FF896C", "1C1824"),
    "mint": ("9DF4CD", "121D25"),
    "lilac": ("CDB4FF", "1B182E"),
}
PLATFORMS = ("tiktok", "instagram", "youtube")
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,DejaVu Sans,48,&H00F8F7FF,&H00F8F7FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def timecode(seconds, srt=False):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if srt:
        return f"{hours:02}:{minutes:02}:{seconds:02},000"
    return f"{hours}:{minutes:02}:{seconds:02}.00"


def save_subtitles(post, path):
    accent, _ = PALETTES[post["palette"]]
    color = f"&H{accent[4:6]}{accent[2:4]}{accent[:2]}&"
    end = sum(scene["seconds"] for scene in post["scenes"])
    ass = [ASS_HEADER.rstrip()]
    srt = []

    def write_line(start, stop, x, y, size, text, style=""):
        if any(character in text for character in "{}\\\n\r"):
            raise ValueError(f"Invalid subtitle text: {text!r}")
        tags = rf"{{\pos({x},{y})\fs{size}{style}}}"
        ass.append(f"Dialogue: 0,{timecode(start)},{timecode(stop)},Main,,0,0,0,,{tags}{text}")

    write_line(0, end, 96, 320, 30, "DOSSIER  /  LEONIDA", rf"\b1\1c{color}\fsp4")
    write_line(0, end, 96, 1392, 28, "GTA VI  /  PAGE DE FANS INDÉPENDANTE", r"\1c&HDDCFC9&")

    start = 0
    for index, scene in enumerate(post["scenes"], 1):
        stop = start + scene["seconds"]
        write_line(start, stop, 96, 526, 32, post["pillar"], rf"\b1\1c{color}\fsp3")
        write_line(start, stop, 708, 526, 30, f"{index:02d} / {len(post['scenes']):02d}", rf"\1c{color}")
        for row, headline in enumerate(scene["headline"]):
            size = 98 if len(headline) <= 11 else 74
            write_line(start, stop, 96, 660 + 126 * row, size, headline, r"\b1")
        detail = scene["detail"].replace("GTA VI", "GTA\u00a0VI")
        detail = re.sub(r" (?=[?!:;])", "\u202f", detail)
        detail_lines = textwrap.wrap(detail, width=27, break_long_words=False)
        if len(detail_lines) > 5:
            raise ValueError(f"{post['id']}: scene {index} exceeds the caption safe area")
        for row, detail in enumerate(detail_lines):
            write_line(start, stop, 96, 986 + 60 * row, 47, detail)
        subtitle = "\n".join([" ".join(scene["headline"]), scene["detail"]])
        srt.append(f"{index}\n{timecode(start, True)} --> {timecode(stop, True)}\n{subtitle}")
        start = stop

    (path / "scene.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")
    (path / "subtitles.srt").write_text("\n\n".join(srt) + "\n", encoding="utf-8")


def render(post, path, duration):
    accent, background = PALETTES[post["palette"]]
    progress = "drawbox=x=96:y=1300:w=720:h=3:color=white@0.14:t=fill"
    filters = [
        "drawbox=x=48:y=277:w=824:h=1177:color=white@0.05:t=2",
        f"drawbox=x=96:y=427:w=102:h=5:color=0x{accent}:t=fill",
        progress,
    ]
    start = 0
    for index, scene in enumerate(post["scenes"], 1):
        stop = start + scene["seconds"]
        width = 720 * index // len(post["scenes"])
        filters.append(
            f"drawbox=x=96:y=1300:w={width}:h=3:color=0x{accent}:t=fill:"
            f"enable='gte(t,{start})*lt(t,{stop})'"
        )
        start = stop
    filters.append("ass=scene.ass")
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"color=c=0x{background}:size=1080x1920:rate=30:duration={duration}",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", str(duration), "-vf", ",".join(filters),
        "-c:v", "libx264", "-threads", "2", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
        "video.mp4",
    ], cwd=path, check=True)


def inspect_video(path, duration):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ], check=True, capture_output=True, text=True)
    probe = json.loads(result.stdout)
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
    actual = {
        key: video[key]
        for key in ("width", "height", "pix_fmt", "avg_frame_rate")
    }
    actual.update(video_codec=video["codec_name"], audio_codec=audio["codec_name"])
    expected = {
        "width": 1080, "height": 1920, "pix_fmt": "yuv420p", "avg_frame_rate": "30/1",
        "video_codec": "h264", "audio_codec": "aac",
    }
    seconds = float(probe["format"]["duration"])
    if actual != expected or abs(seconds - duration) > 0.12:
        raise ValueError(f"Unexpected stream or duration: {actual}, {seconds}s")
    return {**actual, "duration_seconds": seconds, "audio_content": "silence"}


def build_pack(post, facts, output):
    post_id = post["id"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", post_id):
        raise ValueError(f"Invalid content ID: {post_id}")
    post_facts = {fact_id: facts[fact_id] for fact_id in post["fact_ids"]}
    duration = sum(scene["seconds"] for scene in post["scenes"])
    if not post_facts or not 7 <= duration <= 30:
        raise ValueError(f"{post_id}: facts required and duration must be 7–30s")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        path = Path(temporary)
        save_subtitles(post, path)
        render(post, path, duration)
        video = path / "video.mp4"
        manifest = {
            "content_id": post_id,
            "state": "PREVIEW_ONLY",
            "cover": post["cover"],
            "valid_until": post["valid_until"],
            "facts": post_facts,
            "assets": [{"name": "video.mp4", "provenance": "original typography, graphics and silent audio"}],
            "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
            "technical_qc": inspect_video(video, duration),
        }
        for platform in PLATFORMS:
            caption = post["captions"][platform]
            (path / f"{platform}.txt").write_text(
                f"{caption['title']}\n\n{caption['body']}\n", encoding="utf-8"
            )
        (path / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        destination = output / post_id
        destination.mkdir(exist_ok=True)
        for name in ("video.mp4", "scene.ass", "subtitles.srt", *(f"{p}.txt" for p in PLATFORMS), "manifest.json"):
            (path / name).replace(destination / name)
    print(f"{post_id}: {duration}s, sha256={manifest['sha256']}, {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--post", help="Render only this content ID")
    parser.add_argument("--seed", type=Path, default=ROOT / "editorial" / "seed.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "seeds")
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    posts = [post for post in seed["posts"] if args.post is None or post["id"] == args.post]
    if not posts:
        parser.error("No matching seed post")
    if len({post["id"] for post in posts}) != len(posts):
        parser.error("Duplicate content ID in the seed")
    for post in posts:
        build_pack(post, seed["facts"], args.output.resolve())


if __name__ == "__main__":
    main()
