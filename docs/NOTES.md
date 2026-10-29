# Dead ends (so the next person skips them)

> 中文摘要：任何「大图降采样到 42×30」都会糊（整幅只有 1260 格，脸要占 200 格）；手绘 42×30 形状干净但不像本人；`Normal` 光标里箭头压在左鬓上，按颜色、按其它状态搬像素、按 bbox 对齐投票三种补法都失败 —— 正确做法是换用 `Person` 状态。另外 `parseRGB()` 只认 `rgb()` 不认 `#hex`，是「主题整体生效但开屏大字还是品牌蓝」的根因。

Getting a *recognisable* character out of a 32-pixel-wide budget took a lot of
wrong turns. These are the ones that looked promising and were not.

## Downscaling real artwork

Every "draw it bigger, then shrink" route fails the same way: at 42×30 the whole
character gets 1260 pixels, and a face needs roughly 200 of them. Tried and
failed:

- official stamp PNG (296×256, transparent, has Japanese text baked in) →
  downscale loses the eyes entirely;
- character-select illustration (376×840) → decoration removal is fine, the
  42×30 grid is not;
- `gpt-image-2` pixel-art prompts (looked great at 1024²) → the source is ~70
  pixels of detail, so the 42-pixel version is mush;
- ComfyUI img2img (denoise 0.5 / 0.72 / 0.82) → recoloured the dress to teal and
  rebuilt the pose; same seed + edited prompt also changes the pose, so it is
  not a reliable "blink variant" generator.

Conclusion: pick a source that **is** already ~32 px, or draw it by hand at that
size. The official cursors are the former.

## Hand-drawing 42×30

`draw_bust.py` / `draw_bust2.py` build a bust out of ellipses and row spans.
It produces something clean and unmistakably *a* pink-haired chibi, but not
distinguishably *Mizuki*. Complaints it collected: "太不像了" (too unlike), then
"头部形状" (the head is a ball — no jaw taper). Row-span silhouettes fix the
shape; they do not fix likeness.

## Recovering the occluded left edge

`Normal` cursors draw the pointer over the upper-left hair. Tried:

1. key by UI palette (`#FBC5FF`, `#884499`, `#421C70`, `#CD95BE`) → anti-aliased
   edge pixels survive and look like a colour-shifted patch;
2. move pixels in from `Person` / `Working` / `Link` at fixed coordinates →
   those states **shift the head 2–4 px**, so the seam never lines up;
3. per-pixel majority vote across states aligned by bbox → the bboxes disagree
   by more than the arrow moves, so the vote is polluted.

The fix was to not need recovery: use `Person`, whose icon never touches the
face, and repaint the few outline pixels the icon covered (see `PIPELINE.md`).

## Theme wordmark colour

`parseRGB()` matched `rgb(...)` only. A hex accent therefore parsed to `null`
and the splash wordmark silently used the DeepSeek brand blue — while the rest
of the UI (which uses Ink's own colour handling) was correctly themed. If a
"theme mostly works but the big title is blue" issue shows up again, start here.

Second-order trap: after making `parseRGB` understand hex, using `activity` as
the middle stop of the title gradient gives *two* hues — Ena's tan accent plus
Mizuki's pink activity makes a muddy "brown → pink → cream" ramp. Single-hue
(accent lightened 32% / 62%) is the safe formula.

## Odds and ends

- `rembg` cannot fetch its ONNX models here (GitHub release connections are
  dropped). `skytnt/anime-seg` via `hf-mirror.com` works.
- `animecut.py` must resize the mask **after** cropping to 1024, not before —
  the wrong order yields a 62×585 bbox.
- `dsh-tui` on Windows is a delegating launcher at
  `%APPDATA%\npm\node_modules\@deepseek-harness-tui\dsh-tui\bin\dsh-tui.js` that
  forwards to the profile copy. Patch the profile copy only.
