#!/usr/bin/env node
/**
 * Re-apply the "立绘形象" (maid portrait variant) patch after a dsh-tui upgrade.
 *
 * An upgrade replaces node_modules, so the three edits below have to be redone:
 *   1. assets/maid-<id>/{normal,happy}.png      (portrait art per variant)
 *   2. lib/types/components/maidPortrait.js     (variant lookup + setting read)
 *   3. lib/types/dsh-adapter/index.js           (schema key `maidPortraitSkin`)
 *   4. lib/types/settings/definitions.js       (the /settings select row the panel actually renders)
 *   5. lib/settings.json                        (generated mirror of the same row)
 *
 * Idempotent: running it twice is a no-op. Usage: node patch-portrait-options.mjs
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';

const HOME = process.env.DSH_TUI_HOME ?? join(homedir(), '.dsh-tui');
const PKG = join(homedir(), '.dsh', 'profiles', 'dsh-tui', 'node_modules',
  '@deepseek-harness-tui', 'dsh-tui');
const MASCOT = join(HOME, 'mascot');

const VARIANTS = ['mizuki', 'ena'];

function copyAssets() {
  for (const who of VARIANTS) {
    const src = join(MASCOT, `portrait_${who}.png`);
    if (!existsSync(src)) {
      console.log(`skip ${who}: ${src} missing`);
      continue;
    }
    const dir = join(PKG, 'assets', `maid-${who}`);
    mkdirSync(dir, { recursive: true });
    copyFileSync(src, join(dir, 'normal.png'));
    copyFileSync(src, join(dir, 'happy.png'));
    console.log(`assets maid-${who}`);
  }
}

function patchMaidPortrait() {
  const file = join(PKG, 'lib', 'types', 'components', 'maidPortrait.js');
  let s = readFileSync(file, 'utf8');
  if (s.includes('MAID_VARIANTS')) {
    console.log('maidPortrait.js already patched');
    return;
  }
  s = s.replace("import { existsSync, readFileSync } from 'node:fs';",
    "import { existsSync, readFileSync } from 'node:fs';\nimport { homedir } from 'node:os';\nimport { join } from 'node:path';");
  s = s.replace('/** Claude 娘', `/** 额外立绘档（用户自建）：每档一个资产目录，文件契约同 \`whale-girl\`。 */
export const MAID_VARIANTS = {
    'whale-girl': MAID_ASSETS,
    mizuki: { dir: 'maid-mizuki', normal: 'normal.png', happy: 'happy.png' },
    ena: { dir: 'maid-ena', normal: 'normal.png', happy: 'happy.png' },
};
/** 读持久化设置里的 \`maidPortraitSkin\`（\`/settings → 立绘形象\`）；坏值回落内置档。 */
function currentMaidVariant() {
    try {
        const home = process.env.DSH_TUI_HOME ?? join(homedir(), '.dsh-tui');
        const raw = JSON.parse(readFileSync(join(home, 'settings.json'), 'utf8'));
        const id = raw?.values?.maidPortraitSkin;
        return typeof id === 'string' && MAID_VARIANTS[id] !== undefined ? id : 'whale-girl';
    }
    catch {
        return 'whale-girl';
    }
}
/** Claude 娘`);
  s = s.replace(`export function portraitAssetsOf(brand) {
    return brand === 'claude' ? CLAUDE_GIRL_ASSETS : brand === 'codex' ? CODEX_GIRL_ASSETS : MAID_ASSETS;
}`, `export function portraitAssetsOf(brand) {
    if (brand === 'claude')
        return CLAUDE_GIRL_ASSETS;
    if (brand === 'codex')
        return CODEX_GIRL_ASSETS;
    return MAID_VARIANTS[currentMaidVariant()] ?? MAID_ASSETS;
}`);
  writeFileSync(file, s);
  console.log('patched maidPortrait.js');
}

function patchSchema() {
  const file = join(PKG, 'lib', 'types', 'dsh-adapter', 'index.js');
  let s = readFileSync(file, 'utf8');
  if (s.includes('maidPortraitSkin')) {
    console.log('schema already patched');
    return;
  }
  s = s.replace('    whaleGirl: Schema.boolean().default(false),',
    `    whaleGirl: Schema.boolean().default(false),
    // 立绘档（\`/settings → 立绘形象\`）：内置 whale-girl，或用户加的 mizuki / ena。
    maidPortraitSkin: Schema.transform(Schema.string(), value => value === 'mizuki' || value === 'ena' ? value : 'whale-girl'),`);
  writeFileSync(file, s);
  console.log('patched schema');
}

function patchSettingsRow() {
  // the /settings rows themselves are the explicit field array in the adapter
  const pluginPath = join(PKG, 'lib', 'types', 'dsh-adapter', 'plugin.js');
  if (existsSync(pluginPath)) {
    let src = readFileSync(pluginPath, 'utf8');
    let touched = false;
    if (!src.includes("maidPortraitSkin: Schema")) {
      const anchor = '            whaleGirl: Schema.boolean().default(false),';
      const addition = anchor + `
            // Which portrait art the splash / maid portrait draws (maidPortrait.js owns the map).
            maidPortraitSkin: Schema.string(),`;
      if (src.includes(anchor)) { src = src.replace(anchor, addition); touched = true; }
    }
    if (!src.includes("settingField('maidPortraitSkin')")) {
      const anchor = `                {
                    ...settingField('whaleGirl'),
                },`;
      const addition = anchor + `
                {
                    ...settingField('maidPortraitSkin'),
                },`;
      if (src.includes(anchor)) { src = src.replace(anchor, addition); touched = true; }
    }
    if (touched) { writeFileSync(pluginPath, src); console.log('plugin.js: maidPortraitSkin registered'); }
    else console.log('plugin.js: already registered');
  }

  // the /settings panel renders SETTING_DEFINITIONS, not lib/settings.json
  const defsPath = join(PKG, 'lib', 'types', 'settings', 'definitions.js');
  if (existsSync(defsPath)) {
    const defs = readFileSync(defsPath, 'utf8');
    if (!defs.includes('maidPortraitSkin')) {
      const marker = "    'whaleIdle': {";
      const block = `    'maidPortraitSkin': {
        label: 'Portrait art',
        descriptions: { zh: '立绘形象' },
        group: 'splash',
        hint: 'DeepSeek brand only: which portrait art the splash / maid portrait uses. Built-in maid keeps the original whale-girl; the character variants are installed by ~/.dsh-tui/mascot and can be re-applied after an upgrade.',
        hintDescriptions: { zh: '仅 DeepSeek 品牌：开屏/女仆娘立绘用哪一套形象。内置女仆娘即原版鲸娘；角色版由 ~/.dsh-tui/mascot 安装，升级 dsh-tui 后可重新应用。' },
        kind: 'select',
        options: [
            { value: 'whale-girl', label: 'Built-in maid', descriptions: { zh: '内置女仆娘' } },
            { value: 'mizuki', label: 'Mizuki · Amia', descriptions: { zh: '曁山瑞希 · Amia' } },
            { value: 'ena', label: 'Ena · Enanan', descriptions: { zh: '東雲絵名 · Enanan' } },
        ],
    },
`;
      const i = defs.indexOf(marker);
      if (i > 0) {
        writeFileSync(defsPath, defs.slice(0, i) + block + defs.slice(i));
        console.log('definitions.js: maidPortraitSkin row added');
      }
    } else {
      console.log('definitions.js: already has maidPortraitSkin');
    }
  }

  const file = join(PKG, 'lib', 'settings.json');
  const doc = JSON.parse(readFileSync(file, 'utf8'));
  if (doc.settings.some((s) => s.key === 'maidPortraitSkin')) {
    console.log('settings row already present');
    return;
  }
  const entry = {
    key: 'maidPortraitSkin',
    kind: 'select',
    group: 'splash',
    label: { en: 'Portrait art', zh: '立绘形象' },
    description: {
      en: 'Which art the maid portrait slot shows when it is enabled: the built-in maid, or a portrait installed under assets/maid-<id>. Requires the Maid portrait toggle above; without a Kitty/Sixel image protocol the character-art fallback is drawn instead.',
      zh: '「女仆娘立绘」开启时这个槽位画哪一张：内置女仆娘，或 assets/maid-<id> 下装好的自建立绘。需要上面的女仆娘立绘开关；终端不支持 Kitty/Sixel 时仍回落字符画。',
    },
    default: 'whale-girl',
    options: [
      { value: 'whale-girl', label: { en: 'Built-in maid', zh: '内置女仆娘' } },
      { value: 'mizuki', label: { en: 'Mizuki · Amia', zh: '暁山瑞希 · Amia' } },
      { value: 'ena', label: { en: 'Ena · Enanan', zh: '東雲絵名 · Enanan' } },
    ],
    restartRequired: false,
    deprecated: false,
  };
  const idx = doc.settings.findIndex((s) => s.key === 'whaleGirl') + 1;
  doc.settings.splice(idx, 0, entry);
  writeFileSync(file, JSON.stringify(doc, null, 2));
  console.log(`settings row inserted at ${idx}`);
}

copyAssets();
patchMaidPortrait();
patchSchema();
patchSettingsRow();
console.log('done — restart dsh-tui, then /settings → 开屏与吉祥物 → 立绘形象');
