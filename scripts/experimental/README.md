# Experimental / machine-specific

Kept for reference; these need extra setup and are not part of the supported path.

- `mascot.mjs` — installs a **102-frame** 42×30 kit produced by `build-kit-ai.py`
  (plus the 30×30 splash module) into the dsh-tui package. Expects
  `~/.dsh-tui/mascot/kits/<name>/frames.json`. The supported path for portrait
  art is `../install-mascot.mjs`.
- `comfy_pixelize.py` / `build-kit-ai.py` — ComfyUI-based sprite generation:
  chibi from Illustrious-XL + character LoRA on a chroma-green background, then
  border-colour keying, 70 px virtual height, quantise, nearest ×3, assemble
  42×30 letter grids. Works, but the 42×30 result is not recognisable enough to
  be worth the pipeline; see `../../docs/NOTES.md`.
- `splash_sprite.py` — hand-drawn 30×30 bust (ellipses + row spans). Clean, but
  generic. Kept as the fallback when a terminal has no image support.
- `render-preview.py` — earlier variant of `../render-theme.py`.
