# -*- coding: utf-8 -*-
"""Render a preview card for the dsh-TUI 'mizuki' theme."""
import json
from PIL import Image, ImageDraw, ImageFont

THEME = json.load(open(r"C:\Users\Floze\.dsh-tui\themes\mizuki.json", encoding="utf-8"))
C = THEME["colors"]

W, H = 1040, 1170
BG = "#0E0B13"
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

CJK = r"C:\Windows\Fonts\msyh.ttc"
CJK_B = r"C:\Windows\Fonts\msyhbd.ttc"
MONO = r"C:\Windows\Fonts\consola.ttf"
MONO_B = r"C:\Windows\Fonts\consolab.ttf"


def f(path, size):
    return ImageFont.truetype(path, size)


def hexc(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def blend(fg, bg, a):
    fc, bc = hexc(fg), hexc(bg)
    return tuple(int(fc[i] * a + bc[i] * (1 - a)) for i in range(3))


# ── header ────────────────────────────────────────────────────────────────
d.text((44, 34), "暁山瑞希 · Amia", font=f(CJK_B, 38), fill=hexc(C["accent"]))
d.text((46, 86), "dsh-TUI custom theme  ·  mizuki.json  ·  base: dark  ·  image color #DDAACC",
       font=f(MONO, 15), fill=hexc(C["subtle"]))
d.line([(44, 118), (W - 44, 118)], fill=hexc(C["promptBorder"]), width=1)

# ── terminal mock ─────────────────────────────────────────────────────────
TX, TY, TW, TH = 44, 136, W - 88, 396
d.rounded_rectangle([TX, TY, TX + TW, TY + TH], 12, fill=hexc(C["background"]),
                    outline=hexc(C["promptBorder"]), width=1)

x, y = TX + 22, TY + 20
# user prompt line
d.text((x, y), "❯", font=f(MONO_B, 18), fill=hexc(C["accent"]))
d.text((x + 22, y), "把 accent 调成瑞希的印象色", font=f(CJK, 18), fill=hexc(C["text"]))
y += 34

# assistant body with syntax-ish coloring
seg = [("我把 ", C["text"]), ("accent", C["syntaxKeyword"]), (" 换成了 ", C["text"]),
       ("#DDAACC", C["syntaxString"]), ("（官方 image color），", C["text"]),
       ("shimmer", C["syntaxFunction"]), (" 提亮一档到 ", C["text"]),
       ("#F0D7E8", C["syntaxString"]), ("。", C["text"])]
cx = x
for text, col in seg:
    d.text((cx, y), text, font=f(CJK, 18), fill=hexc(col))
    cx += d.textlength(text, font=f(CJK, 18))
y += 34

# tool card
CY = y
CH = 96
d.rounded_rectangle([x, CY, x + TW - 44, CY + CH], 8, fill=hexc(C["toolCardBackground"]),
                    outline=blend(C["promptBorder"], C["toolCardBackground"], 0.55), width=1)
d.ellipse([x + 14, CY + 16, x + 24, CY + 26], fill=hexc(C["toolDotExec"]))
d.text((x + 32, CY + 11), "bash", font=f(MONO_B, 16), fill=hexc(C["toolNameExec"]))
d.text((x + 84, CY + 13), "完成", font=f(CJK, 14), fill=hexc(C["success"]))
d.text((x + 14, CY + 44), "pnpm add dsh-meme@0.1.70 --save-exact", font=f(MONO, 15),
       fill=hexc(C["inactive"]))
d.text((x + 14, CY + 68), "+ dsh-meme 0.1.70", font=f(MONO, 15), fill=hexc(C["success"]))
y = CY + CH + 22

# diff
for sign, body, fg, bgk in (("-", '  accent: "#FF9EC7"', C["diffRemoved"], C["diffRemovedDimmed"]),
                            ("+", '  accent: "#DDAACC"', C["diffAdded"], C["diffAddedDimmed"])):
    d.rectangle([x, y, x + TW - 44, y + 26], fill=blend(bgk, C["background"], 0.35))
    d.text((x + 10, y + 4), sign, font=f(MONO_B, 15), fill=hexc(fg))
    d.text((x + 28, y + 4), body, font=f(MONO, 15), fill=hexc(fg))
    y += 28

# context bar
y += 14
barX, barW, barH = x, TW - 44, 10
total = 34 + 22 + 26 + 12 + 6
segs = [("contextBarSystem", 34), ("contextBarPrompt", 22), ("contextBarAssistant", 26),
        ("contextBarThinking", 12), ("contextBarTools", 6)]
off = 0
for key, n in segs:
    w = barW * n / total
    d.rectangle([barX + off, y, barX + off + w - 2, y + barH], fill=hexc(C[key]))
    off += w
d.text((barX, y + 18), "context ・ 38%", font=f(MONO, 13), fill=hexc(C["subtle"]))
y += 46

# status bar
d.line([(x, y), (x + TW - 44, y)], fill=blend(C["promptBorder"], C["background"], 0.35), width=1)
y += 10
st = [("deepseek-v4", C["accent"]), ("  ·  max  ·  ~/.dsh-tui  ·  ", C["inactive"]),
      ("● mizuki", C["toolDotRead"]), ("  ·  12.4k tok", C["subtle"])]
cx = x
for text, col in st:
    d.text((cx, y), text, font=f(MONO, 14), fill=hexc(col))
    cx += d.textlength(text, font=f(MONO, 14))

# ── palette ───────────────────────────────────────────────────────────────
PY = 606
d.text((44, PY - 34), "配色", font=f(CJK_B, 20), fill=hexc(C["text"]))
d.text((104, PY - 30), "81 个颜色键全部覆盖", font=f(CJK, 14), fill=hexc(C["subtle"]))

GROUPS = [
    ("焦点 / 强调", ["accent", "accentShimmer", "activity", "activityShimmer", "suggestion", "remember"]),
    ("正文", ["text", "inactive", "subtle", "inverseText", "background"]),
    ("面板 / 边框", ["permission", "promptBorder", "bashBorder", "planMode", "ide"]),
    ("工具与状态点", ["toolCardBackground", "toolDotExec", "toolDotRead", "toolDotWrite", "toolDotWeb"]),
    ("状态 / diff", ["success", "error", "warning", "diffAdded", "diffRemoved", "merged"]),
    ("语法高亮", ["syntaxKeyword", "syntaxString", "syntaxComment", "syntaxNumber", "syntaxFunction", "syntaxType"]),
    ("上下文条", ["contextBarSystem", "contextBarPrompt", "contextBarAssistant", "contextBarThinking", "contextBarTools"]),
    ("其他", ["mascotBody", "cursor", "ignition", "selectionBg", "userMessageBackground", "rate_limit_fill"]),
]

col_w = (W - 88) / 2
row_h = 30
for gi, (gname, keys) in enumerate(GROUPS):
    col = gi % 2
    row = gi // 2
    gx = 44 + col * col_w
    gy = PY + row * (row_h * 3 + 34)
    d.text((gx, gy), gname, font=f(CJK, 14), fill=hexc(C["subtle"]))
    for i, k in enumerate(keys):
        r, c = i // 2, i % 2
        ix = gx + c * (col_w / 2 - 6)
        iy = gy + 24 + r * row_h
        d.rectangle([ix, iy, ix + 18, iy + 18], fill=hexc(C[k]),
                    outline=blend(C["promptBorder"], BG, 0.4))
        d.text((ix + 26, iy + 2), k, font=f(MONO, 12), fill=hexc(C["text"]))
        d.text((ix + 26 + d.textlength(k, font=f(MONO, 12)) + 8, iy + 2), C[k],
               font=f(MONO, 12), fill=hexc(C["subtle"]))

out = r"C:\Users\Floze\mizuki-theme-preview.png"
img.save(out)
print("saved", out, img.size)
