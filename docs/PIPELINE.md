# Mascot pipeline

> 中文摘要：先用 `fetch-cursors.py` 下载官方 32×32 动画光标并抽帧；用 `Person` 状态（图标在左上、不压脸），按连通块大小丢掉那枚图标，再补回被它盖住的 1–2 px 头发描边；最近邻放大到 301×288 后用 `install-mascot.mjs` 装进 `assets/maid-<角色>/`。立绘也可以从 `Charsel-*.png` 走 `animecut.py`（isnetis.onnx）+ `polish_bust.py`（alpha 二值化、去投影、缩放进画布）。

Goal: a character-accurate face at 32×32 (splash grid) and at 301×288 (portrait
slot), without redrawing anything by hand.

## 1. Source: official cursors

`https://colorfulstage.com/media/download/` ships `<Character> Animated
Cursor.zip`. Each state is a Windows `.ani`, which is RIFF/ACON:

```
RIFF <size> ACON
  LIST <size> INFO  ... (author, name)
  LIST <size> fram
    icon <size> <full .ico bytes>   ← 12 frames, in order
    icon <size> ...
```

`scripts/fetch-cursors.py` walks the RIFF tree, pulls each `icon` chunk and
opens it with Pillow. Seven states exist per character: `Normal`, `Alternate`,
`Busy`, `Diagonal1/2`, `Person`, `Working`, `Link`.

**Use `Person`.** `Normal` draws the pointer arrow over the left side of the
hair, and every earlier attempt to key that arrow out (by colour, by hue, by
majority vote over states) left either a hole or a fringe. `Person` parks a
small grey icon at the top-left corner where it never touches the face; the icon
is a separate connected component, so removing it is exact.

## 2. Head extraction

```
python scripts/cursor_head.py cursors/frames/Mizuki/Person/00.png assets/maid-mizuki/normal.png
```

- 4-connected components; drop the small one (<100 px) whose centroid sits in
  `GLYPH_BOX = (0, 0, 11, 13)`. Size + position, not colour: the icon has
  anti-aliased edge pixels (`#F2F3F6`, `#C8CDD6`, ...) that a colour test misses.
- The icon also **covers** a few pixels of the hair outline, so `close_gap()`
  repaints pixels inside `GAP_WINDOW = (0, 0, 14, 12)` that touch transparency
  and are not already the outline colour. Outline colour is the modal colour
  along the silhouette (`#804651` for both characters here).
- Nearest-neighbour upscale ×11 with padding to 301×288 (the size
  `loadMaidPortraits()` expects).

## 3. Portrait from the full illustration (alternative)

`Charsel-<name>.png` from the wiki (`static.wikitide.net/projectsekaiwiki/...`,
376×840) contains the character plus decorations: a name banner, vertical text,
colour blocks and a soft wall shadow.

```
python scripts/animecut.py   cropped.png matted.png     # isnetis.onnx matte
python scripts/polish_bust.py matted.png ready.png      # alpha + haze + fit
```

- `animecut.py` runs `skytnt/anime-seg` (`isnetis.onnx`, 168 MB, mirror:
  `https://hf-mirror.com/skytnt/anime-seg/resolve/main/isnetis.onnx`) at
  1024×1024 with input normalised `(x-0.5)/0.5`.
- `polish_bust.py` binarises alpha at 200 (110 keeps the wall shadow, 235 eats
  the outline), removes grey regions (low saturation, 130≤v≤232) that touch the
  frame — that is the cast shadow — trims, then fits height into 301×288.
- Crop boxes used: Mizuki `(52, 18, 246, 470)`, Ena `(44, 52, 300, 440)`.

## 4. Install

```
node scripts/install-mascot.mjs mizuki   --normal assets/maid-mizuki/normal.png   --happy  assets/maid-mizuki/happy.png
```

`install-mascot.mjs` copies the PNGs to
`assets/maid-<variant>/{normal,happy}.png`, which is what `maidPortrait.js` reads
for the portrait slot. Enable the row that selects it with
`patch-portrait-options.mjs`, then pick it under 开屏与吉祥物 → 立绘形象.

Terminals without kitty/sixel support never see these PNGs: dsh-tui falls back
to the 30×30 letter grid in `lib/types/components/whaleGirlSprite.js`. Swapping
that module (see `experimental/mascot.mjs`) is the only way to theme that path.

## 5. Theme preview cards

```
python scripts/render-theme.py themes/mizuki.json out.png
```

Renders a 1040×1170 card: terminal mock (user line, syntax-coloured reply, tool
card, diff, five-segment context bar, status bar) above an 8-group swatch grid.
Requires Pillow and the Windows fonts `msyh*.ttc` / `consola*.ttf`.
