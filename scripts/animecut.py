"""Cut an anime character out of its background with isnetis (anime-segmentation)."""
import sys
import numpy as np
import onnxruntime as ort
from PIL import Image

SIZE = 1024
SESSION = ort.InferenceSession("models/isnetis.onnx", providers=["CPUExecutionProvider"])


def cut(src, dst, pad=0):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    canvas = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    scale = SIZE / max(w, h)
    small = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    canvas.paste(small, ((SIZE - small.width) // 2, (SIZE - small.height) // 2))
    x = np.asarray(canvas, dtype=np.float32) / 255.0
    x = (x - 0.5) / 0.5
    x = np.transpose(x, (2, 0, 1))[None, ...]
    mask = SESSION.run(None, {"img": x})[0][0, 0]
    mask = (mask - mask.min()) / max(1e-6, mask.max() - mask.min())
    full = Image.fromarray((mask * 255).astype(np.uint8))
    ox, oy = (SIZE - small.width) // 2, (SIZE - small.height) // 2
    full = full.crop((ox, oy, ox + small.width, oy + small.height)).resize((w, h), Image.LANCZOS)
    out = im.convert("RGBA")
    out = im.convert("RGBA")
    out.putalpha(full)
    bb = out.getbbox()
    out.crop(bb).save(dst)
    return out.crop(bb).size


if __name__ == "__main__":
    print(sys.argv[1], "->", cut(sys.argv[1], sys.argv[2]))
