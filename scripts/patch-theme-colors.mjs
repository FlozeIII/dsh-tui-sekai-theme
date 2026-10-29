// Re-apply the custom-theme colour fixes after a dsh-tui upgrade.
//
// `parseRGB()` only understood `rgb(r,g,b)`, so a theme that stores hex (`#DDAACC`)
// parsed to null and the splash wordmark fell back to the DeepSeek brand blue. This
// script (1) teaches parseRGB about hex and (2) makes the big title run a single-hue
// ramp off the theme accent instead of borrowing `activity`/FLASH/PALE.
//
//   node patch-theme-colors.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const PKG = join(
  process.env.USERPROFILE ?? process.env.HOME,
  '.dsh/profiles/dsh-tui/node_modules/@deepseek-harness-tui/dsh-tui',
);

function patch(rel, fn) {
  const file = join(PKG, rel);
  const before = readFileSync(file, 'utf8');
  const after = fn(before);
  if (after === before) {
    console.log(`${rel}: already patched`);
    return;
  }
  writeFileSync(file, after);
  console.log(`${rel}: patched`);
}

patch('lib/types/components/Spinner/spinnerUtils.js', src => {
  if (src.includes('HEX_STRING_PATTERN')) return src;
  let out = src.replace(
    'const RGB_STRING_PATTERN = ',
    'const HEX_STRING_PATTERN = /^#([0-9a-fA-F]{3,8})$/;\nconst RGB_STRING_PATTERN = ',
  );
  const hexFn = [
    'function parseHex(colorStr) {',
    "    const m = typeof colorStr === 'string' ? colorStr.match(HEX_STRING_PATTERN) : null;",
    '    if (!m) return null;',
    '    let hex = m[1];',
    "    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');",
    '    if (hex.length !== 6 && hex.length !== 8) return null;',
    '    return { r: parseInt(hex.slice(0, 2), 16), g: parseInt(hex.slice(2, 4), 16), b: parseInt(hex.slice(4, 6), 16) };',
    '}',
    'export function parseRGB(colorStr) {',
  ].join('\n');
  out = out.replace('export function parseRGB(colorStr) {', hexFn);
  out = out.replace('        }\n        : null;', '        }\n        : parseHex(colorStr);');
  return out;
});

const MID_BLOCK = [
  '    const flash = brandLadder?.flash ?? parseRGB(theme.accentShimmer) ?? FLASH;',
  '    const accentRGB = parseRGB(theme.accent);',
  '    const paleWordmark = interpolateColor(wordmarkRGB, { r: 255, g: 255, b: 255 }, 0.62);',
  '    const midWordmark = interpolateColor(wordmarkRGB, { r: 255, g: 255, b: 255 }, 0.32);',
].join('\n');

patch('lib/types/components/LogoV2.js', src => {
  if (src.includes('midWordmark')) return src;
  let out = src.replace('    const flash = brandLadder?.flash ?? FLASH;', MID_BLOCK);
  out = out.replace(
    '        ?? brandLadder?.mid\n        ?? taglineRGB;',
    '        ?? brandLadder?.mid\n        ?? (accentRGB !== null ? midWordmark : taglineRGB);',
  );
  out = out.replace(
    '        ?? brandLadder?.end\n        ?? PALE;',
    '        ?? brandLadder?.end\n        ?? (accentRGB !== null ? paleWordmark : PALE);',
  );
  return out;
});
