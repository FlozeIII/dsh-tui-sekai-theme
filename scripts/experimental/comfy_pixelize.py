# -*- coding: utf-8 -*-
"""Chroma-key a ComfyUI render (flat background) and turn it into a pixel sprite.

The background colour is sampled from the image border and removed with a
border-connected flood fill, so stray same-coloured pixels inside the
character survive. The sprite is then normalised by height, downscaled to a
small virtual resolution, palette-quantised and upscaled with NEAREST.
"""
import json
import sys
from collections import deque
import numpy as np
from PIL import Image

CANVAS_W, CANVAS_H = 301, 288
VIRTUAL_H = 70          # logical pixels kept vertically
COLORS = 24
TOL = 46
SAT = 1.45
OUTLINE = None


def border_rgb(a):
    h, w, _ = a.shape
    patches = [a[0:6, 0:6], a[0:6, w - 6:w], a[h - 6:h, 0:6], a[h - 6:h, w - 6:w]]
    px = np.concatenate([p.reshape(-1, 3) for p in patches])
    return np.median(px, axis=0)


def key_background(im):
    a = np.array(im.convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    bg = border_rgb(a)
    dist = np.sqrt(((a - bg) ** 2).sum(axis=2))
    close = dist < TOL
    # flood fill from the border through background-coloured pixels
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if close[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if close[y, x] and not seen[y, x]:
                seen[y, x] = True; q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and close[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    # enclosed background pockets (e.g. between the legs) are not reachable from
    # the border, so a stricter global colour test mops them up
    enclosed = (dist < TOL * 0.8) & ~seen
    seen = seen | enclosed
    # neither character uses green: any surviving greenish pixel is a key artefact
    rgb = a.astype(np.float32)
    mx = rgb.max(axis=2); mn = rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    greenish = (rgb[..., 1] > rgb[..., 0] * 1.06) & (rgb[..., 1] > rgb[..., 2] * 1.06) & (sat > 0.12)
    seen = seen | greenish
    alpha = np.where(seen, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")


def keep_largest(im):
    a = np.array(im)
    mask = a[..., 3] > 0
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    best, best_area = None, 0
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)]); seen[y, x] = True; cells = []
            while q:
                cy, cx = q.popleft(); cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx))
            if len(cells) > best_area:
                best_area, best = len(cells), cells
    clean = np.zeros((h, w), np.uint8)
    for cy, cx in best or []:
        clean[cy, cx] = 255
    a[..., 3] = clean
    return Image.fromarray(a, "RGBA")


def add_outline(small, color):
    a = np.array(small)
    mask = a[..., 3] > 0
    grow = np.zeros_like(mask)
    grow[1:, :] |= mask[:-1, :]
    grow[:-1, :] |= mask[1:, :]
    grow[:, 1:] |= mask[:, :-1]
    grow[:, :-1] |= mask[:, 1:]
    ring = grow & ~mask
    a[ring] = (color[0], color[1], color[2], 255)
    return Image.fromarray(a, "RGBA")


def to_sprite(im, virtual_h=VIRTUAL_H):
    im = im.crop(im.getbbox())
    scale = virtual_h / im.height
    small_h = virtual_h
    small_w = max(1, round(im.width * scale))
    small = im.resize((small_w, small_h), Image.LANCZOS)
    alpha = small.getchannel("A").point(lambda v: 255 if v >= 110 else 0)
    # a touch more contrast/saturation so the palette keeps the character colours
    from PIL import ImageEnhance
    rgb = ImageEnhance.Color(small.convert("RGB")).enhance(SAT)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
    small = rgb.quantize(colors=COLORS, method=Image.MEDIANCUT).convert("RGBA")
    small.putalpha(alpha)
    if OUTLINE is not None:
        small = add_outline(small, OUTLINE)
    k = CANVAS_H * 0.86 // small_h
    k = max(1, int(k))
    big = small.resize((small.width * k, small.height * k), Image.NEAREST)
    out = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    out.paste(big, ((CANVAS_W - big.width) // 2, CANVAS_H - big.height - 4), big)
    return out, small, k


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 3:
        OUTLINE = tuple(int(sys.argv[3][i:i + 2], 16) for i in (1, 3, 5))
    if len(sys.argv) > 4:
        SAT = float(sys.argv[4])
    if len(sys.argv) > 5:
        COLORS = int(sys.argv[5])
    im = keep_largest(key_background(Image.open(src)))
    out, small, k = to_sprite(im)
    out.save(dst)
    stem = dst[:-4]
    small.save(stem + ".small.png")
    with open(stem + ".small.json", "w", encoding="utf-8") as f:
        json.dump({"k": k, "w": small.width, "h": small.height}, f)
    print(f"{dst}  virtual={small.size}  k={k}")
