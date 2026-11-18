"""Render the private Ocean Drive comparison. Inputs and credits are in editorial/OCEAN_DRIVE.md."""

import argparse
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import resample_poly
from math import gcd

WIDTH, HEIGHT, FPS = 1080, 1920, 30
DURATION, SAMPLE_RATE = 13.2, 48000
FONT_DIR = Path("/usr/share/fonts/truetype/open-sans")
HEAD = ImageFont.truetype(str(FONT_DIR / "OpenSans-CondBold.ttf"), 89)
NAME = ImageFont.truetype(str(FONT_DIR / "OpenSans-CondBold.ttf"), 82)
LABEL = ImageFont.truetype(str(FONT_DIR / "OpenSans-Bold.ttf"), 31)
CREDIT = ImageFont.truetype(str(FONT_DIR / "OpenSans-Semibold.ttf"), 25)
WHITE, GOLD, BLUE = "#fffaf0", "#ffd98c", "#abf5ff"
PHOTO_CREDIT = "Photo recadrée · Dan Lundberg · CC BY-SA 2.0"
SOURCE_NOTE = (
    "GTA VI © Rockstar Games, Trailer 1 (00:32.57) et rubrique Musique. "
    "Photo « 20111001 1498 South Beach Hotel Victor dusk (2) » © Dan Lundberg, "
    "https://flickr.com/photos/9508280@N07/6931673712/ ; recadrages de la photo "
    "sous https://creativecommons.org/licenses/by-sa/2.0/. Montage et musique originaux. "
    "Voix française de synthèse SIWIS / Piper."
)


def crop(image, height, cx, cy, fraction):
    """Fill a panel around a focal point. Coordinates are fractions of the source."""
    w, h = image.size
    box_h = min(h, w * height / WIDTH) * fraction
    box_w = box_h * WIDTH / height
    left = min(max(w * cx - box_w / 2, 0), w - box_w)
    top = min(max(h * cy - box_h / 2, 0), h - box_h)
    return image.resize((WIDTH, height), Image.Resampling.BICUBIC,
                        (left, top, left + box_w, top + box_h))


def label(draw, y, text, accent):
    x = 62
    right = x + 53 + int(draw.textlength(text, font=LABEL))
    draw.rounded_rectangle((x, y, right, y + 56), radius=7, fill="#111820")
    draw.rectangle((x + 13, y + 14, x + 18, y + 42), fill=accent)
    draw.text((x + 32, y + 5), text, font=LABEL, fill=WHITE)


def shade(frame, first, last, top=0, bottom=183):
    mask = Image.linear_gradient("L").resize((1, last - first)).point(
        lambda value: round(top + value / 255 * (bottom - top))
    ).resize((WIDTH, last - first))
    frame.paste((9, 15, 22), (0, first, WIDTH, last), mask)


def lines(frame, y, words, accent=WHITE, font=HEAD):
    draw = ImageDraw.Draw(frame)
    for index, line in enumerate(words):
        draw.text((67, y + 88 * index), line, font=font,
                  fill=accent if index == len(words) - 1 else WHITE,
                  stroke_width=2, stroke_fill="#152028")


def split(game, real, progress):
    frame = Image.new("RGB", (WIDTH, HEIGHT))
    frame.paste(crop(game, 938, .724, .195, .43 - .03 * progress), (0, 0))
    frame.paste(crop(real, 976, .653, .365, .65 - .045 * progress), (0, 944))
    frame.paste("#ffdfae", (0, 938, WIDTH, 944))
    draw = ImageDraw.Draw(frame)
    label(draw, 148, "VICE CITY", BLUE)
    label(draw, 973, "MIAMI BEACH", GOLD)
    return frame


def compose(t, game, real, opening):
    if t < 1.5:
        frame = opening
        label(ImageDraw.Draw(frame), 154, "GTA VI  /  OCEAN DRIVE", BLUE)
        shade(frame, 970, HEIGHT)
        lines(frame, 1170, ["Pourquoi cet hôtel", "a changé de nom ?"], GOLD)
    elif t < 2.55:
        frame = split(game, real, (t - 1.5) / 1.05)
    elif t < 6.35:
        p = (t - 2.55) / 3.8
        frame = crop(real, HEIGHT, .64 + .014 * p, .51 - .115 * p, .94 - .25 * p)
        label(ImageDraw.Draw(frame), 154, "MIAMI BEACH  /  OCEAN DRIVE", GOLD)
        shade(frame, 990, HEIGHT)
        words = ["Sur Ocean Drive,", "à Miami Beach."] if t < 4.4 else ["Le vrai hôtel", "s’appelle Victor."]
        lines(frame, 1170, words, GOLD)
    elif t < 9.7:
        p = min(1, max(0, (t - 7.25) / 1.15))
        ease = p * p * (3 - 2 * p)
        frame = crop(game, HEIGHT, .66 + .069 * ease, .47 - .25 * ease, .98 - .46 * ease)
        label(ImageDraw.Draw(frame), 154, "GTA VI  /  VICE CITY", BLUE)
        shade(frame, 1030, HEIGHT)
        words = ["Regarde", "le néon bleu."] if t < 8.55 else ["Hôtel Dixon."]
        lines(frame, 1200, words, BLUE)
    else:
        frame = split(game, real, (t - 9.7) / (DURATION - 9.7))
        shade(frame, 535, 938, 0, 222)
        lines(frame, 671, ["Lawrence Murray Dixon"], GOLD, NAME)
        ImageDraw.Draw(frame).text((70, 794), "L’architecte de l’hôtel Victor.", font=LABEL,
                                    fill=WHITE, stroke_width=1, stroke_fill="#162128")
    if 1.5 <= t < 6.35 or t >= 9.7:
        draw = ImageDraw.Draw(frame)
        draw.text((66, 1570), PHOTO_CREDIT, font=CREDIT, fill=WHITE,
                  stroke_width=2, stroke_fill="#102027")
    return frame


def soundtrack(voice_dir, path):
    rng = np.random.default_rng(140)
    rate = SAMPLE_RATE
    size = round(DURATION * rate)
    timeline = np.arange(size) / rate
    music, voice = np.zeros(size), np.zeros(size)

    def add(track, start, samples):
        pos = round(start * rate)
        n = min(len(samples), size - pos)
        track[pos:pos + n] += samples[:n]

    # Original bass, percussion and plucked synth. No audio from the trailer.
    beat = .625
    chord = (146.832, 174.614, 220.0, 261.626)
    for n in range(21):
        start = n * beat
        tick = np.arange(round(.38 * rate)) / rate
        if n % 4 in (0, 2):
            kick = np.sin(2 * np.pi * (47 * tick + 2.5 * (1 - np.exp(-22 * tick))))
            add(music, start, .12 * kick * np.exp(-13 * tick))
        if n % 4 in (1, 3):
            noise = rng.standard_normal(len(tick))
            add(music, start, .029 * np.diff(noise, prepend=0) * np.exp(-37 * tick))
        hat = rng.standard_normal(len(tick))
        add(music, start + beat / 2, .017 * np.diff(hat, prepend=0) * np.exp(-75 * tick))
        if n % 2 == 0:
            sustain = np.arange(round(1.18 * rate)) / rate
            freq = chord[(n // 2) % 4]
            bell = np.sin(2 * np.pi * freq * 2 * sustain + .65 * np.sin(2 * np.pi * freq * sustain))
            add(music, start, .071 * bell * np.minimum(1, 90 * sustain) * np.exp(-3.6 * sustain))
    for i, start in enumerate((.03, 2.55, 6.38, 9.78)):
        with wave.open(str(voice_dir / f"line{i}.wav")) as file:
            if file.getnchannels() != 1 or file.getsampwidth() != 2:
                raise ValueError("La voix doit être mono PCM 16 bits.")
            sr = file.getframerate()
            data = np.frombuffer(file.readframes(file.getnframes()), dtype="<i2") / 32768.
        active = np.flatnonzero(np.abs(data) > .014)
        data = data[max(0, active[0] - int(.045 * sr)):active[-1] + int(.11 * sr)]
        if len(data) / sr > (2.51, 3.73, 3.32, 3.4)[i]:
            raise ValueError(f"La réplique {i} dépasse son plan.")
        divisor = gcd(sr, rate)
        add(voice, start, resample_poly(data, rate // divisor, sr // divisor) * .72)
    fade = np.minimum(1, (DURATION - timeline) / .26)
    mix = (music + voice) * fade
    with wave.open(str(path), "wb") as file:
        file.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        file.writeframes((np.clip(mix, -.95, .95) * 32767).astype("<i2").tobytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("trailer", "game-photo", "real-photo", "voice-dir", "output"):
        parser.add_argument("--" + arg, required=True, type=Path)
    parser.add_argument("--source-start", type=float, default=32.57,
                        help="Time of the Ocean Drive shot. Subtract the source offset for a trimmed input.")
    args = parser.parse_args()
    game, real = (Image.open(p).convert("RGB") for p in (args.game_photo, args.real_photo))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output.parent) as temp:
        folder = Path(temp)
        sound = folder / "mix.wav"
        soundtrack(args.voice_dir, sound)
        subprocess.run([
            "ffmpeg", "-loglevel", "error", "-y", "-ss", str(args.source_start), "-i", str(args.trailer),
            "-an", "-vf", "fps=30,crop=ih*9/16:ih:(iw-ow)*0.31:0,scale=1080:1920",
            "-frames:v", "45", "-q:v", "2", str(folder / "open-%02d.jpg"),
        ], check=True)
        output = folder / "review.mp4"
        command = [
            "ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", "1080x1920", "-r", "30", "-i", "-", "-i", str(sound), "-c:v", "libx264",
            "-threads", "4", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=8", "-ar", "48000", "-c:a", "aac", "-b:a", "160k",
            "-metadata", "title=Pourquoi cet hôtel a changé de nom dans GTA VI ?",
            "-metadata", "comment=" + SOURCE_NOTE, "-movflags", "+faststart", str(output),
        ]
        with subprocess.Popen(command, stdin=subprocess.PIPE) as encode:
            try:
                for i in range(round(DURATION * FPS)):
                    opening = None
                    if i < 45:
                        with Image.open(folder / f"open-{i + 1:02d}.jpg") as shot:
                            opening = shot.convert("RGB")
                    frame = compose(i / FPS, game, real, opening)
                    encode.stdin.write(frame.tobytes())
            finally:
                encode.stdin.close()
            if encode.wait():
                raise RuntimeError("L’encodage a échoué.")
        output.replace(args.output)


if __name__ == "__main__":
    main()
