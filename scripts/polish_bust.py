import sys
from collections import deque
import numpy as np
from PIL import Image

CANVAS = (301, 288)


def haze_mask(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(2); mn = rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    return (sat < 0.10) & (mn >= 130) & (mx <= 232)


def drop_border_grey(alpha, rgb):
    m = haze_mask(rgb)
    h, w = m.shape
    lab = np.zeros((h, w), np.int32)
    drop = np.zeros((h, w), bool)
    cur = 0
    for sy in range(h):
        for sx in range(w):
            if not m[sy, sx] or lab[sy, sx]:
                continue
            cur += 1
            lab[sy, sx] = cur
            q = deque([(sy, sx)])
            cells = [(sy, sx)]
            touch = False
            while q:
                cy, cx = q.popleft()
                if cy in (0, h - 1) or cx in (0, w - 1):
                    touch = True
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        q.append((ny, nx))
                        cells.append((ny, nx))
            if touch and len(cells) > 40:
                for cy, cx in cells:
                    drop[cy, cx] = True
    alpha = alpha.copy()
    alpha[drop] = 0
    return alpha


def main(src, dst):
    im = Image.open(src).convert("RGBA")
    a = np.array(im)
    rgb = a[..., :3].astype(np.float32)
    alpha = a[..., 3].copy()
    alpha[alpha < 200] = 0
    alpha = drop_border_grey(alpha, rgb)
    a[..., 3] = alpha
    out = Image.fromarray(a)
    bbox = out.getbbox()
    out = out.crop(bbox)
    scale = (CANVAS[1] - 12) / out.height
    w = int(out.width * scale)
    out = out.resize((w, CANVAS[1] - 12), Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(out, ((CANVAS[0] - w) // 2, 6), out)
    canvas.save(dst)
    print(dst, canvas.size, "opaque", int((np.array(canvas)[..., 3] > 0).sum()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
