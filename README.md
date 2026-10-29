# dsh-tui · Project SEKAI theme pack

Two things for [dsh-tui](https://www.npmjs.com/package/@deepseek-harness-tui/dsh-tui),
built around 暁山瑞希 (Akiyama Mizuki) and 東雲絵名 (Shinonome Ena) from
*Project SEKAI COLORFUL STAGE!*:

1. **Two custom themes** — 81 colour keys each, single-hue ramps, official image
   colours as the accent (`#DDAACC` for Mizuki, `#CCAA88` for Ena).
2. **Pixel mascots** — 32×32 official chibi cursors turned into splash / portrait
   art, plus a settings row that lets you pick which character shows up.

| mizuki | ena |
| :--: | :--: |
| ![mizuki theme](docs/images/mizuki.png) | ![ena theme](docs/images/ena.png) |

```
themes/mizuki.json      81 keys, base dark, accent #DDAACC
themes/ena.json         81 keys, base dark, accent #CCAA88
scripts/                everything that puts them on screen
docs/PIPELINE.md        how the mascot art is produced, step by step
docs/NOTES.md           dead ends worth not repeating
```

## Quick start

```bash
# 1. themes
node scripts/install-themes.mjs mizuki     # or: ena

# 2. splash / sidebar mascot (optional, needs Python + Pillow)
python scripts/fetch-cursors.py Mizuki Ena
python scripts/cursor_head.py cursors/frames/Mizuki/Person/00.png assets/maid-mizuki/normal.png
python scripts/cursor_head.py cursors/frames/Ena/Person/00.png    assets/maid-ena/normal.png
node scripts/install-mascot.mjs mizuki   --normal assets/maid-mizuki/normal.png   --happy  assets/maid-mizuki/happy.png

# 3. two small patches so hex themes and the character picker actually work
node scripts/patch-theme-colors.mjs
node scripts/patch-portrait-options.mjs
```

Restart dsh-tui afterwards (`terminalImages` and the patches are read at boot).

## Why the patches exist

`dsh-tui` ships themes whose colours are written `rgb(r,g,b)`. Custom themes tend
to be written `#rrggbb`, and `parseRGB()` in
`lib/types/components/Spinner/spinnerUtils.js` silently returns `null` for hex —
so the splash wordmark fell back to the DeepSeek brand blue while every other
surface picked up the accent. `patch-theme-colors.mjs` teaches `parseRGB` about
hex and rebuilds the big title as a single-hue ramp off `theme.accent`
(`#DDAACC → #E8C5DC → #F2DFEC`) instead of mixing in `activity`/`FLASH`/`PALE`.

The settings panel builds its rows from an explicit field list in
`lib/types/dsh-adapter/plugin.js`, with metadata from
`lib/types/settings/definitions.js`. Neither knows about a "which portrait art"
option, so `patch-portrait-options.mjs` adds one:

```
开屏与吉祥物 → 立绘形象:  内置女仆娘 / 暁山瑞希 / 東雲絵名
```

Both scripts are idempotent and must be re-run after upgrading `dsh-tui`
(they patch files inside `~/.dsh/profiles/dsh-tui/node_modules/...`).

## Splash art is a three-way choice

From `lib/types/components/splashArtRows.js`:

```js
if (brand === 'deepseek' && (mascotSkin === 'deepy' || mascotSkin === 'whaleGirl')) return 'mascot';
if (input.whaleGirl || brand !== 'deepseek') return 'portrait';
return 'whale';
```

`mascot` wins whenever the pet skin is a sticker pet, so the portrait slot only
shows up with `companion.skin: whale` + `whaleGirl: true`:

```yaml
# ~/.dsh/profiles/dsh-tui/cordis.patch.yml
terminalImages: true
whaleGirl: true
maidPortraitSkin: mizuki    # added by patch-portrait-options.mjs
companion:
  skin: whale
```

`portrait` renders a real image through kitty/sixel, which needs a terminal that
answers the graphics query. Windows Terminal works once
`terminalImages` is on; in a terminal that cannot, dsh-tui falls back to the
30×30 letter grid (`whaleGirlSprite.js`) — that path is why the same art looks
blocky in some sessions.

## Credits / licence

Code: MIT. Art derived from *Project SEKAI COLORFUL STAGE!* belongs to
SEGA / Colorful Palette; this repo does not redistribute it — the scripts fetch
or generate it locally. See [NOTICE.md](NOTICE.md).
