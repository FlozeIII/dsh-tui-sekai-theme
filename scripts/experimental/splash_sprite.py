# -*- coding: utf-8 -*-
"""Draw the 30x30 splash portrait with primitives.

dsh-tui paints this grid as half-block cells when the terminal has no image
protocol, so it has to read at 30x30; downscaling our 301x288 art turns to mush,
hence the hand-built geometry here.
"""
import sys
from pathlib import Path

from PIL import Image

HOME = Path.home()
MASCOT = HOME / ".dsh-tui" / "mascot"
OUT_DIR = MASCOT / "splash"
N = 30

PALETTES = {
    "mizuki": dict(hair="#F4D2E1", hair_l="#FBE6EF", hair_d="#DDAACC", hair_s="#B3809B",
                   skin="#FDEFE6", skin_s="#EFD2C4", eye="#3E1F2C", iris="#D0719B",
                   dark="#2A1B24", shirt="#FCF8FB", shirt_s="#DED4DC",
                   skirt="#332839", accent="#E86FA3"),
    "ena": dict(hair="#93786B", hair_l="#B29283", hair_d="#6F5850", hair_s="#584540",
                skin="#FDEFE6", skin_s="#EFD2C4", eye="#3A2218", iris="#C9903F",
                dark="#241A1C", shirt="#FBEEEA", shirt_s="#DCCFC3",
                skirt="#2B2530", accent="#E0A24C"),
}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def canvas():
    return [[None] * N for _ in range(N)]


def put(g, x, y, c):
    if c is not None and 0 <= x < N and 0 <= y < N:
        g[y][x] = c


def ellipse(g, cx, cy, rx, ry, c):
    for y in range(N):
        for x in range(N):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                g[y][x] = c


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(g, x, y, c)


def draw(who):
    g = canvas()
    P = PALETTES[who]

    # back hair mass (big bob) + side ponytail hanging on the right
    ellipse(g, 14.5, 13.5, 10.5, 11.5, P["hair"])
    ellipse(g, 25.0, 13.0, 2.6, 3.6, P["hair_d"])
    ellipse(g, 25.5, 19.0, 2.8, 4.6, P["hair_d"])
    ellipse(g, 24.5, 23.0, 2.2, 2.6, P["hair_d"])

    # face sits low in the bob
    ellipse(g, 14.5, 14.5, 5.6, 6.2, P["skin"])

    # shoulders / shirt
    ellipse(g, 14.5, 28.0, 9.5, 6.0, P["shirt"])
    rect(g, 5, 26, 24, 26, P["shirt"])
    # collar V + small dark bowtie at the neck
    for i in range(3):
        put(g, 13 + i, 22 + i, P["shirt_s"])
        put(g, 16 - i, 22 + i, P["shirt_s"])
    rect(g, 14, 24, 15, 24, P["dark"])
    put(g, 13, 25, P["dark"])
    put(g, 16, 25, P["dark"])

    # fringe: solid arc over the forehead, dipping to the brows
    ellipse(g, 14.5, 8.5, 7.4, 4.2, P["hair"])
    for x in range(8, 22):
        put(g, x, 10 + (1 if x in (9, 14, 19) else 0), P["hair"])
    rect(g, 11, 4, 12, 5, P["hair_l"])
    rect(g, 17, 5, 18, 5, P["hair_l"])

    # eyes: lid row + iris row, 2 cells each
    for x0 in (11, 16):
        rect(g, x0, 13, x0 + 1, 13, P["eye"])
        rect(g, x0, 14, x0 + 1, 14, P["iris"])
        put(g, x0, 14, P["eye"])
    # mouth
    put(g, 14, 17, P["accent"])

    # hair tie
    rect(g, 22, 9, 23, 11, P["hair_s"])
    # ribbon bow on the ponytail (top right, clear of the face)
    rect(g, 21, 3, 24, 5, P["dark"])
    put(g, 20, 4, P["dark"])
    put(g, 25, 4, P["dark"])
    rect(g, 22, 6, 23, 6, P["dark"])

    # skirt hem
    rect(g, 5, 27, 24, 29, P["skirt"])
    rect(g, 6, 27, 23, 27, P["shirt"])

    # outline: hair pixels touching transparency drop to the shadow tone
    out = [row[:] for row in g]
    for y in range(N):
        for x in range(N):
            if g[y][x] not in (P["hair"], P["hair_d"]):
                continue
            if any(not (0 <= x + dx < N and 0 <= y + dy < N) or g[y + dy][x + dx] is None
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = P["hair_s"]
    return out


def to_module(grid, pal, who):
    rows = "".join(
        "    [" + ", ".join("null" if c is None else "[%d, %d, %d]" % hex2rgb(c) for c in row) + "],\n"
        for row in grid
    )
    return f"""/**
 * Splash portrait sprite (30 cols x 30 rows, half-block rendered -> 15 text rows).
 *
 * Hand-built by ~/.dsh-tui/mascot/splash_sprite.py for the `{who}` theme: 30x30
 * leaves no room for a downscaled render, so the shapes are drawn directly.
 * Contract: 30 cells per row, `null` = transparent, each cell is [r, g, b].
 * Rendering: lib/types/components/WhaleGirl.js.
 */
/** Sprite columns. */
export const WHALE_GIRL_COLS = 30;
/** Sprite rows (rendered as `WHALE_GIRL_SPRITE_ROWS / 2` text rows). */
export const WHALE_GIRL_SPRITE_ROWS = 30;
/** Sprite: [row][col] = null (transparent) or [r, g, b]. */
export const WHALE_GIRL_SPRITE = [
{rows}];
"""


def render(grid, pal, out, scale=14):
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c:
                px[x, y] = hex2rgb(c) + (255,)
    img.resize((N * scale, N * scale), Image.NEAREST).save(out)


def main():
    who = (sys.argv[1] if len(sys.argv) > 1 else "mizuki").lower()
    grid = draw(who)
    pal = PALETTES[who]
    render(grid, pal, str(MASCOT / f"_splash_{who}.png"))
    if "--write" in sys.argv:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{who}.js").write_text(to_module(grid, pal, who), encoding="utf-8")
        print(f"wrote splash/{who}.js")
    else:
        print(f"preview _splash_{who}.png")


if __name__ == "__main__":
    main()
