// Install the bundled themes into the dsh-tui data directory.
//
//   node install-themes.mjs              # copy mizuki.json / ena.json
//   node install-themes.mjs mizuki       # ... and make it the active theme
//   node install-themes.mjs --list       # show what is installed
//
// dsh-tui reads ~/.dsh-tui/themes/*.json (see CUSTOM_THEME_DIR in
// lib/types/customTheme.js) and remembers the active one in ~/.dsh-tui/theme.json
// as { "theme": "<name>" }.
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repoThemes = join(here, '..', 'themes');
const home = process.env.USERPROFILE ?? process.env.HOME;
const dataDir = join(home, '.dsh-tui');
const themeDir = join(dataDir, 'themes');

const args = process.argv.slice(2);
const listOnly = args.includes('--list');
const wanted = args.filter(a => !a.startsWith('-'));

mkdirSync(themeDir, { recursive: true });

if (listOnly) {
  for (const file of readdirSync(themeDir).filter(f => f.endsWith('.json'))) {
    const theme = JSON.parse(readFileSync(join(themeDir, file), 'utf8'));
    console.log(`${theme.name.padEnd(10)} ${theme.displayName ?? ''} -> ${file}`);
  }
  process.exit(0);
}

for (const file of readdirSync(repoThemes).filter(f => f.endsWith('.json'))) {
  copyFileSync(join(repoThemes, file), join(themeDir, file));
  const theme = JSON.parse(readFileSync(join(repoThemes, file), 'utf8'));
  console.log(`installed ${theme.name.padEnd(10)} ${Object.keys(theme.colors ?? {}).length} colour keys`);
}

const active = wanted[0];
if (active) {
  const prefPath = join(dataDir, 'theme.json');
  const pref = existsSync(prefPath) ? JSON.parse(readFileSync(prefPath, 'utf8')) : {};
  pref.theme = active;
  writeFileSync(prefPath, JSON.stringify(pref, null, 2));
  console.log(`active theme -> ${active} (${prefPath})`);
} else {
  console.log('run `node install-themes.mjs mizuki` (or ena) to make one active');
}
