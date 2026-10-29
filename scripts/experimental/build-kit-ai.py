# -*- coding: utf-8 -*-
"""Build a dsh-tui companion kit from pixel sprites, animating at sprite scale.

Inputs are the low-resolution sprites written by comfy_pixelize.py
(art_<who>_src.small.png / art_<who>_sleep.small.png + .small.json with the
integer upscale factor k). Everything is composed at that low resolution and
only then upscaled with NEAREST, so a 1px bob is a real 1px bob instead of a
3px jump, which is what made the earlier kits look choppy.
"""
import json, math, os, shutil
from collections import deque
import numpy as np
from PIL import Image

CANVAS_W, CANVAS_H = 301, 288
GRID_W, GRID_H = 42, 30
COLOR_BUDGET = 30
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

GLYPHS = {
    "note": ["..#", "..#", ".##", "###", "##."],
    "heart": [".#.#.", "#####", "#####", ".###.", "..#.."],
    "zzz": ["###", "..#", ".#.", "#..", "###"],
    "excl": ["#", "#", "#", ".", "#"],
    "sweat": [".#", "##", "#.", ".."],
    "star": ["..#..", ".###.", "#####", ".###.", "..#.."],
    "dots": ["...", "...", "###"],
}

TITLES = {
    "idle": "待机眨眼", "idle-look": "东张西望", "idle-spout": "开心哼歌", "thinking": "思考",
    "typing": "打字", "music": "听歌", "conducting": "指挥", "building": "干活",
    "error": "出错", "happy": "开心", "notification": "提示", "compacting": "压缩上下文",
    "carrying": "搬东西", "sleeping": "睡觉", "waking": "醒来", "poke-left": "戳一下",
    "poke-right": "戳一下", "tickle": "挠痒", "drag": "被拖走", "swim": "游泳",
    "smile-hearts": "心动", "thumbs-up": "点赞",
}


def blink_from_sleep(awake, sleep, y0, y1):
    """Steal the closed-eye band from the sleeping sprite (same character, same scale)."""
    a = np.array(awake.copy())
    s = np.array(sleep)
    sx = (a.shape[1] - s.shape[1]) // 2
    for y in range(y0, min(y1, s.shape[0], a.shape[0])):
        for x in range(s.shape[1]):
            tx = x + sx
            if not (0 <= tx < a.shape[1]):
                continue
            if s[y, x, 3] > 0:
                a[y, tx] = s[y, x]
            else:
                a[y, tx, 3] = 0
    return Image.fromarray(a, "RGBA")


def blink_procedural(sprite):
    """Close the eyes by repainting the eye boxes with skin and drawing a lid line."""
    a = np.array(sprite.copy())
    h, w = a.shape[:2]
    rgb = a[..., :3].astype(np.int16)
    al = a[..., 3] > 0
    mx = rgb.max(axis=2).astype(np.float32)
    mn = rgb.min(axis=2).astype(np.float32)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    val = mx / 255.0
    band = np.zeros((h, w), bool)
    band[int(h * 0.20):int(h * 0.40), int(w * 0.15):int(w * 0.85)] = True
    cand = band & al & ((sat > 0.35) | (val < 0.30))
    boxes = []
    seen = np.zeros((h, w), bool)
    for y in range(h):
        for x in range(w):
            if not cand[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)]); seen[y, x] = True; cells = []
            while q:
                cy, cx = q.popleft(); cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and cand[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
            if not (3 <= len(cells) <= 400):
                continue
            ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
            bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            if bh <= h * 0.14 and 2 <= bw <= w * 0.45:
                boxes.append((min(xs), min(ys), max(xs), max(ys)))
    boxes.sort(key=lambda b: -(b[2] - b[0]))
    boxes = sorted(boxes[:2])
    for (x0, y0, x1, y1) in boxes:
        below = rgb[max(y1 + 1, 0):min(y1 + 4, h), x0:x1 + 1]
        sel = below[(below.sum(axis=2) > 300)]
        skin = np.median(sel, axis=0).astype(np.uint8) if len(sel) else np.array([246, 224, 200], np.uint8)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if al[y, x]:
                    a[y, x, :3] = skin
        ymid = (y0 + y1) // 2
        for x in range(x0, x1 + 1):
            a[ymid, x, :3] = (skin * 0.35).astype(np.uint8)
            a[ymid, x, 3] = 255
    return Image.fromarray(a, "RGBA")


def make_blink(sprite):
    """Close the eyes of a small sprite: repaint the eye box with skin + a lid line."""
    im = sprite.copy()
    a = np.array(im)
    h, w = a.shape[:2]
    rgb = a[..., :3].astype(np.int16)
    alpha = a[..., 3] > 0
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    face_top, face_bot = int(h * 0.18), int(h * 0.50)
    region = np.zeros((h, w), bool)
    region[face_top:face_bot, int(w * 0.12):int(w * 0.88)] = True
    band = region & alpha
    if band.sum() < 20:
        return im
    thr = np.median(lum[band]) * 0.72
    core = band & (lum < thr)
    if core.sum() < 4:
        return im
    xs_all = np.nonzero(core)[1]
    mid = int(np.median(xs_all))
    skin = np.median(rgb[band & (lum > np.median(lum[band]))], axis=0).astype(np.uint8)
    lid = (0.35 * skin).astype(np.uint8)

    for lo, hi in ((0, mid), (mid, w)):
        part = core.copy()
        part[:, :lo] = False
        part[:, hi:] = False
        ys2, xs2 = np.nonzero(part)
        if len(ys2) < 2:
            continue
        y0, y1 = ys2.min(), ys2.max()
        x0, x1 = xs2.min(), xs2.max()
        box = np.zeros((h, w), bool)
        box[y0:y1 + 1, x0:x1 + 1] = True
        box &= alpha
        a[box, :3] = skin
        a[box, 3] = 255
        span = max(1, x1 - x0)
        for i in range(span + 1):
            x = x0 + i
            t = i / span
            y = int(round(y0 + (y1 - y0) * 0.5 + math.sin(math.pi * t) * (y1 - y0) * 0.22))
            if 0 <= y < h:
                a[y, x, :3] = lid
                a[y, x, 3] = 255
    return Image.fromarray(a, "RGBA")


def draw_glyph(canvas, name, gx, gy, color):
    for y, row in enumerate(GLYPHS[name]):
        for x, ch in enumerate(row):
            if ch != "#":
                continue
            xx, yy = gx + x, gy + y
            if 0 <= xx < canvas.width and 0 <= yy < canvas.height:
                canvas.putpixel((xx, yy), color)


def compose(arts, key, dx, dy, glyphs, small_size, effect_colors):
    S_W, S_H = small_size
    canvas = Image.new("RGBA", (S_W, S_H), (0, 0, 0, 0))
    art = arts[key]
    x = (S_W - art.width) // 2 + dx
    y = S_H - art.height - 1 + dy
    canvas.paste(art, (x, y), art)
    spots = [(S_W - 8, 1), (2, 3)]
    for i, g in enumerate(glyphs):
        sx, sy = spots[i % len(spots)]
        draw_glyph(canvas, g, sx, sy + (2 if i == 1 else 0), effect_colors[i % len(effect_colors)])
    return canvas


def frames_for(key):
    """[(art_key, dx, dy, glyphs, dur)] with dx/dy in sprite pixels."""
    if key == "idle":
        out = [("N", 0, d, (), 170) for d in (0, -1, -1, -2, -2, -1, -1, 0, 1, 1, 0, 0)]
        out += [("B", 0, 0, (), 90), ("B", 0, 0, (), 70), ("N", 0, 0, (), 150)]
        return out
    if key == "idle-look":
        return [("N", -1, 0, (), 420), ("N", -1, 0, (), 380), ("N", 0, 0, (), 420),
                ("N", 1, 0, (), 380), ("N", 1, 0, (), 420), ("N", 0, 0, (), 400),
                ("B", 0, 0, (), 90), ("N", 0, 0, (), 110)]
    if key == "idle-spout":
        return [("N", 0, -1, ("note",), 200), ("N", 0, 0, ("note",), 200),
                ("N", 0, -1, ("note",), 200), ("N", 0, 0, (), 220)]
    if key == "thinking":
        return [("N", 0, 0, ("sweat",), 300), ("N", 0, -1, ("sweat",), 300),
                ("N", 0, 0, ("sweat",), 340), ("N", 0, 0, (), 300)]
    if key == "typing":
        return [("N", 0, 0, (), 150), ("N", 0, 1, (), 150)] * 3 + [("N", 0, 0, (), 180)]
    if key == "music":
        return [("N", 0, -1, ("note",), 260), ("N", 0, 0, ("note",), 240),
                ("N", 0, -1, ("star",), 260), ("N", 0, 0, (), 240)]
    if key == "conducting":
        return [("N", 1, 0, ("note",), 170), ("N", -1, -1, ("note",), 170),
                ("N", 1, 0, ("note",), 170), ("N", -1, -1, ("note",), 170)]
    if key == "building":
        return [("N", 0, -1, ("star",), 240), ("N", 0, 0, ("star",), 240),
                ("N", 0, -1, ("dots",), 260), ("N", 0, 0, (), 240)]
    if key == "error":
        return [("N", -1, 0, ("excl",), 110), ("N", 1, 0, ("excl",), 110),
                ("N", -1, 0, ("excl",), 110), ("N", 0, 0, (), 240)]
    if key == "happy":
        return [("N", 0, -2, ("heart",), 220), ("N", 0, 0, ("heart",), 220),
                ("N", 0, -1, ("heart",), 240), ("B", 0, 0, (), 100),
                ("N", 0, 0, (), 200)]
    if key == "notification":
        return [("N", 0, -1, ("excl",), 200), ("N", 0, 0, ("excl",), 200),
                ("N", 0, -1, ("excl",), 200), ("N", 0, 0, (), 320)]
    if key == "compacting":
        return [("S", 0, 0, ("zzz",), 420), ("S", 0, 0, ("zzz", "zzz"), 520),
                ("S", 0, 1, ("zzz",), 420)]
    if key == "carrying":
        return [("N", 0, -1, (), 260), ("N", 0, 0, (), 260), ("N", 0, -1, ("dots",), 280)]
    if key == "sleeping":
        return [("S", 0, 0, ("zzz",), 700), ("S", 0, 1, ("zzz",), 700),
                ("S", 0, 0, ("zzz", "zzz"), 700)]
    if key == "waking":
        return [("S", 0, 0, ("zzz",), 260), ("B", 0, 0, (), 180),
                ("N", 0, 0, (), 220), ("N", 0, -1, (), 240)]
    if key == "poke-left":
        return [("N", -2, 1, ("excl",), 90), ("N", 0, 0, (), 160),
                ("B", 0, 0, (), 90), ("N", 0, 0, (), 160)]
    if key == "poke-right":
        return [("N", 2, 1, ("excl",), 90), ("N", 0, 0, (), 160),
                ("B", 0, 0, (), 90), ("N", 0, 0, (), 160)]
    if key == "tickle":
        return [("N", -1, 0, ("heart",), 130), ("N", 1, -1, ("heart",), 130),
                ("B", 0, 0, ("heart",), 130), ("N", -1, 0, ("heart",), 130),
                ("N", 1, -1, (), 130)]
    if key == "drag":
        return [("N", 0, -2, (), 240), ("N", 0, -1, ("excl",), 240), ("N", 0, 0, (), 240)]
    if key == "swim":
        return [("N", 1, 1, (), 220), ("N", 0, 0, (), 220), ("N", -1, -1, (), 220),
                ("N", 0, 0, (), 220)]
    if key == "smile-hearts":
        return [("N", 0, -1, ("heart", "heart"), 260), ("N", 0, 0, ("heart",), 240),
                ("B", 0, 0, ("heart",), 120), ("N", 0, -1, ("heart",), 240)]
    if key == "thumbs-up":
        return [("N", 0, -1, ("star",), 320), ("N", 0, 0, ("star",), 320)]
    return [("N", 0, 0, (), 300)]


def to_grid(canvas, palette):
    small = canvas.resize((GRID_W, GRID_H), Image.LANCZOS)
    px = small.load()
    keys = list(palette.keys())
    cols = np.array([palette[k] for k in keys], dtype=np.int32)
    rows = []
    for y in range(GRID_H):
        row = []
        for x in range(GRID_W):
            r, g, b, al = px[x, y]
            if al < 110:
                row.append(".")
                continue
            d = ((cols - np.array([r, g, b])) ** 2).sum(axis=1)
            row.append(keys[int(d.argmin())])
        rows.append("".join(row))
    return rows


BLINK_CFG = {
    "mizuki": ("band", 13, 25),
    "ena": ("proc",),
}


def build(who, normal_small, sleep_small, outdir, effect_hex, effect_hex2):
    meta = json.load(open(normal_small.replace(".small.png", ".small.json"), encoding="utf-8"))
    k = meta["k"]
    S_W, S_H = math.ceil(CANVAS_W / k), math.ceil(CANVAS_H / k)

    artN = Image.open(normal_small).convert("RGBA")
    artS = Image.open(sleep_small).convert("RGBA")
    cfg = BLINK_CFG.get(who, ("proc",))
    blink = blink_from_sleep(artN, artS, cfg[1], cfg[2]) if cfg[0] == "band" else blink_procedural(artN)
    blink.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"blink_{who}.small.png"))
    arts = {"N": artN, "S": artS, "B": blink}

    ec = tuple(int(effect_hex[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    ec2 = tuple(int(effect_hex2[i:i + 2], 16) for i in (1, 3, 5)) + (255,)

    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(os.path.join(outdir, "img"))

    flat = artN.convert("RGB").quantize(colors=COLOR_BUDGET - 2, method=Image.MEDIANCUT)
    colors = [c for _, c in flat.convert("RGB").getcolors(maxcolors=1 << 20)]
    colors.sort(key=lambda c: -(c[0] * 0.3 + c[1] * 0.6 + c[2] * 0.1))
    palette = {}
    for i, (r, g, b) in enumerate(colors[: COLOR_BUDGET - 2]):
        palette[CHARS[i]] = (int(r), int(g), int(b))
    palette[CHARS[COLOR_BUDGET - 2]] = ec[:3]
    palette[CHARS[COLOR_BUDGET - 1]] = ec2[:3]

    timings, animations = {}, []
    for key in TITLES:
        d = os.path.join(outdir, "img", key)
        os.makedirs(d)
        entries, frames = [], []
        for i, (art_key, dx, dy, glyphs, dur) in enumerate(frames_for(key)):
            small = compose(arts, art_key, dx, dy, glyphs, (S_W, S_H), (ec, ec2))
            canvas = small.resize((S_W * k, S_H * k), Image.NEAREST)
            if canvas.width > CANVAS_W or canvas.height > CANVAS_H:
                canvas = canvas.crop((0, 0, CANVAS_W, CANVAS_H))
            else:
                pad = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
                pad.paste(canvas, (0, 0), canvas)
                canvas = pad
            fname = f"{i:02d}.png"
            canvas.save(os.path.join(d, fname))
            entries.append({"dur": dur, "file": fname})
            frames.append({"dur": dur, "rows": to_grid(canvas, palette)})
        timings[key] = entries
        animations.append({"key": key, "title": TITLES[key], "frames": frames})

    json.dump({"size": [GRID_W, GRID_H],
               "palette": {c: "#%02x%02x%02x" % v for c, v in palette.items()},
               "animations": animations},
              open(os.path.join(outdir, "frames.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    json.dump(timings, open(os.path.join(outdir, "img", "timings.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    total = sum(len(v) for v in timings.values())
    print(f"{who}: {len(animations)} anims, {total} frames (k={k}, sprite {S_W}x{S_H}) -> {outdir}")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    build("mizuki", os.path.join(here, "art_mizuki_src.small.png"), os.path.join(here, "art_mizuki_sleep.small.png"),
          os.path.join(here, "kits", "mizuki"), "#F2A9C4", "#F5CB6E")
    build("ena", os.path.join(here, "art_ena_src.small.png"), os.path.join(here, "art_ena_sleep.small.png"),
          os.path.join(here, "kits", "ena"), "#EFA79E", "#E8B45C")
