#!/usr/bin/env python3
"""Download the official Project SEKAI animated cursors and unpack their frames.

The official site ships a 32x32 pixel chibi of every character as a Windows
cursor set (one `.ani` per cursor state). Each `.ani` is a RIFF/ACON file whose
`LIST fram` chunk is a sequence of complete `.ico` payloads, so we can pull the
frames out with `struct` + Pillow and never touch the cursor-specific code.

    python fetch-cursors.py Mizuki Ena
    python fetch-cursors.py Mizuki Ena --out ../cursors

Frames land in `<out>/frames/<Character>/<State>/NN.png`.
"""
from __future__ import annotations

import argparse
import io
import struct
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

BASE = "https://colorfulstage.com/upload_images/media/Download/"

# state -> file name inside the zip
STATES = [
    "Normal",
    "Alternate",
    "Busy",
    "Diagonal1",
    "Diagonal2",
    "Person",
    "Working",
    "Link",
]


def riff_children(data: bytes, start: int, end: int):
    """Yield (chunk_id, payload_offset, payload_size) for one RIFF level."""
    pos = start
    while pos + 8 <= end:
        chunk_id = data[pos : pos + 4]
        size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        yield chunk_id, pos + 8, size
        pos += 8 + size + (size & 1)


def icon_payloads(data: bytes) -> list[bytes]:
    """Every `icon` chunk inside the file, depth-first (they live in `LIST fram`)."""
    found: list[bytes] = []

    def walk(start: int, end: int) -> None:
        for chunk_id, body, size in riff_children(data, start, end):
            if chunk_id == b"icon":
                found.append(data[body : body + size])
            elif chunk_id == b"LIST":
                walk(body + 4, body + size)

    walk(12, len(data))
    return found


def unpack_ani(path: Path, out_dir: Path) -> int:
    frames = icon_payloads(path.read_bytes())
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for index, payload in enumerate(frames):
        try:
            image = Image.open(io.BytesIO(payload)).convert("RGBA")
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"  ! {path.name} frame {index}: {exc}", file=sys.stderr)
            continue
        if image.size != (32, 32):
            canvas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            canvas.paste(image, (0, 0))
            image = canvas
        image.save(out_dir / f"{index:02d}.png")
        written += 1
    return written


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    print(f"  download {url}")
    with urllib.request.urlopen(url, timeout=60) as response:
        dest.write_bytes(response.read())
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("characters", nargs="+", help="Mizuki, Ena, ...")
    parser.add_argument("--out", default="cursors", help="output directory")
    parser.add_argument(
        "--static", action="store_true", help="also fetch the static (.cur) set"
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for character in args.characters:
        print(f"{character}")
        zips = [f"{character} Animated Cursor.zip"]
        if args.static:
            zips.append(f"{character} Static Cursor.zip")

        for zip_name in zips:
            url = BASE + urllib.parse.quote(zip_name)
            archive = download(url, out / "downloads" / zip_name)
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(out / "raw" / character / Path(zip_name).stem)

        root = out / "raw" / character
        for ani in sorted(root.rglob("*.ani")):
            state = ani.stem
            if state not in STATES:
                continue
            count = unpack_ani(ani, out / "frames" / character / state)
            print(f"  {state:<10} {count} frames")

        for cur in sorted(root.rglob("*.cur")):
            frame = Image.open(cur).convert("RGBA")
            if frame.size != (32, 32):
                canvas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
                canvas.paste(frame, (0, 0))
                frame = canvas
            dest = out / "static" / character
            dest.mkdir(parents=True, exist_ok=True)
            frame.save(dest / f"{cur.stem}.png")

    print(f"done -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
