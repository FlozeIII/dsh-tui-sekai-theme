# 像素小人生成流程

目标：在 32×32（开屏字符网格）和 301×288（立绘槽）两个尺寸上，都拿到**认得出是谁**的脸，
而且不靠手画。

## 1. 素材来源：官方光标

`https://colorfulstage.com/media/download/` 提供 `<角色> Animated Cursor.zip`。
每个状态是一个 Windows `.ani`，本质是 RIFF/ACON：

```
RIFF <size> ACON
  LIST <size> INFO  ...（作者、名称）
  LIST <size> fram
    icon <size> <完整的 .ico 字节>   ← 12 帧，按顺序
    icon <size> ...
```

`scripts/fetch-cursors.py` 遍历 RIFF 树，把每个 `icon` chunk 取出来交给 Pillow 解析。
每个角色有 7 个状态：`Normal`、`Alternate`、`Busy`、`Diagonal1/2`、`Person`、
`Working`、`Link`。

**用 `Person`。** `Normal` 会把鼠标箭头画在头发左半边上面，而我试过的所有抠箭头办法
（按颜色、按色相、跨状态多数投票）要么留下洞、要么留下毛边。`Person` 把一枚小灰色图标
停在左上角，跟脸不接触，而且那枚图标是一个独立的连通块——删掉它是精确的。

## 2. 抠头

```
python scripts/cursor_head.py cursors/frames/Mizuki/Person/00.png assets/maid-mizuki/normal.png
```

- 4-连通分块，只丢掉「面积 < 100 px 且质心落在 `GLYPH_BOX = (0, 0, 11, 13)`」的那一块。
  判据是**大小 + 位置**，不是颜色：图标的边缘有抗锯齿过渡色（`#F2F3F6`、`#C8CDD6` 等），
  用颜色判一定会漏，漏掉的那半圈像素看起来就是"这块颜色不对"。
- 图标还**压住**了头发描边的几个像素，所以 `close_gap()` 会把
  `GAP_WINDOW = (0, 0, 14, 12)` 里"紧贴透明、且本身不是描边色"的像素改回描边色。
  描边色取剪影上出现最多的颜色（这两个角色都是 `#804651`）。
- 最近邻放大 ×11，补齐到 301×288（`loadMaidPortraits()` 期望的画布）。

## 3. 另一条路：从完整立绘裁半身

wiki 上的 `Charsel-<角色>.png`（`static.wikitide.net/projectsekaiwiki/...`，376×840）
是角色选择立绘，除了角色本人还有一堆装饰：人名横幅、右侧竖排字、色块、以及墙上的柔和投影。

```
python scripts/animecut.py   cropped.png matted.png     # isnetis.onnx 抠图
python scripts/polish_bust.py matted.png ready.png      # alpha + 去投影 + 缩放
```

- `animecut.py` 跑 `skytnt/anime-seg`（`isnetis.onnx`，168 MB，镜像：
  `https://hf-mirror.com/skytnt/anime-seg/resolve/main/isnetis.onnx`），输入 1024×1024，
  预处理 `(x-0.5)/0.5`。
- `polish_bust.py` 把 alpha 按 200 二值化（110 会把墙上投影留下，235 会啃掉描边），
  然后去掉"低饱和、130≤v≤232、且贴着画布边缘"的连通块——那就是投影——再裁边、
  按高度缩放塞进 301×288。
- 用到的裁剪框：瑞希 `(52, 18, 246, 470)`，絵名 `(44, 52, 300, 440)`。

## 4. 装上

```
node scripts/install-mascot.mjs mizuki \
  --normal assets/maid-mizuki/normal.png \
  --happy  assets/maid-mizuki/normal.png
```

`install-mascot.mjs` 把图拷到 `assets/maid-<变体>/{normal,happy}.png`，也就是
`maidPortrait.js` 给立绘槽读的位置。用 `patch-portrait-options.mjs` 打开设置页那一行，
再到「开屏与吉祥物 → 立绘形象」里选中即可。

不支持 kitty/sixel 的终端根本看不到这些 PNG：dsh-tui 会退回
`lib/types/components/whaleGirlSprite.js` 里的 30×30 字符网格。要给那条路换图，
只能替换那个模块（见 `experimental/mascot.mjs`）。

## 5. 主题预览卡

```
python scripts/render-theme.py themes/mizuki.json out.png
```

输出 1040×1170 的卡片：上半是终端 mock（用户行、带语法色的回复、工具卡、diff、
五段上下文条、状态栏），下半是 8 组色块网格。需要 Pillow 和 Windows 字体
`msyh*.ttc` / `consola*.ttf`。
