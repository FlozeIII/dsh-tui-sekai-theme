"""Extract the 32x32 cursor chibi head.

Source frames are the `Person` cursor state: the character is drawn untouched and the
only extra artwork is the small grey glyph in the top-left corner. That glyph is a
separate 4-connected blob, so it can be dropped by shape alone - no colour keying,
which is what left the pale seam behind on earlier attempts.
"""
import sys
from collections import deque

import numpy as np
from PIL import Image

OUT = (301, 288)
N = 32
GLYPH_BOX = (0, 0, 11, 13)      # where the Person glyph lives (x0, y0, x1, y1)


def blobs(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            out.append(cells)
    return out


GAP_WINDOW = (0, 0, 14, 12)     # where the glyph used to sit and eat the outline


def outline_colour(a, keep):
    """The art's own silhouette colour: the most common colour on the silhouette."""
    from collections import Counter
    cnt = Counter()
    h, w = keep.shape
    for y in range(h):
        for x in range(w):
            if not keep[y, x]:
                continue
            if any(
                not (0 <= y + dy < h and 0 <= x + dx < w) or not keep[y + dy, x + dx]
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                cnt[tuple(int(v) for v in a[y, x])] += 1
    if not cnt:
        return (0x80, 0x46, 0x51)
    return cnt.most_common(1)[0][0]


def close_gap(out, keep):
    """The Person glyph was composited over the art, which ate the outline along the
    upper-left silhouette. Put that one-cell border back inside the same window."""
    col = outline_colour(out[..., :3].astype(np.int16), keep)
    x0, y0, x1, y1 = GAP_WINDOW
    snap = out.copy()
    for y in range(y0, min(y1, N)):
        for x in range(x0, min(x1, N)):
            if not keep[y, x] or tuple(snap[y, x, :3]) == col:
                continue
            edge = any(
                not (0 <= y + dy < N and 0 <= x + dx < N) or not keep[y + dy, x + dx]
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if edge:
                out[y, x, :3] = col


def head_image(path):
    a = np.array(Image.open(path).convert("RGB")).astype(np.int16)
    if a.shape[:2] != (N, N):
        canvas = np.zeros((N, N, 3), np.int16)
        h, w = min(N, a.shape[0]), min(N, a.shape[1])
        canvas[:h, :w] = a[:h, :w]
        a = canvas
    opaque = a.sum(2) > 40

    keep = np.zeros((N, N), bool)
    x0, y0, x1, y1 = GLYPH_BOX
    for cells in blobs(opaque):
        cy = sum(c[0] for c in cells) / len(cells)
        cx = sum(c[1] for c in cells) / len(cells)
        if len(cells) < 100 and x0 <= cx <= x1 and y0 <= cy <= y1:
            continue
        for y, x in cells:
            keep[y, x] = True

    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = a.astype(np.uint8)
    out[..., 3] = np.where(keep, 255, 0)
    close_gap(out, keep)
    im = Image.fromarray(out)
    return im.crop(im.getbbox())


def build(src, dst):
    im = head_image(src)
    scale = max(1, min(OUT[1] // im.height, OUT[0] // im.width))
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    canvas = Image.new("RGBA", OUT, (0, 0, 0, 0))
    canvas.paste(big, ((OUT[0] - big.width) // 2, 0), big)
    canvas.save(dst)
    print(f"{dst}: head {im.size} x{scale} -> {canvas.size}")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
