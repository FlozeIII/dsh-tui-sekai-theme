// One-command setup: theme + (optional) mascot art + the two patches.
//
//   node scripts/setup.mjs                 # mizuki theme, art only if present
//   node scripts/setup.mjs ena
//   node scripts/setup.mjs mizuki --no-art # skip the mascot step entirely
//
// Everything it runs is also usable on its own; this is just the errand boy.
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, '..');
const home = process.env.USERPROFILE ?? process.env.HOME;

const args = process.argv.slice(2);
const theme = args.find(a => !a.startsWith('--')) ?? 'mizuki';
const skipArt = args.includes('--no-art');
const node = process.execPath;

function run(label, cmd, cmdArgs, { optional = false } = {}) {
  process.stdout.write(`\n[${label}]\n`);
  const result = spawnSync(cmd, cmdArgs, { stdio: 'inherit', cwd: repo });
  if (result.status !== 0) {
    if (optional) {
      process.stdout.write(`  skipped (exit ${result.status})\n`);
      return false;
    }
    process.exit(result.status ?? 1);
  }
  return true;
}

if (!['mizuki', 'ena'].includes(theme)) {
  console.error(`unknown theme "${theme}" (use mizuki | ena)`);
  process.exit(1);
}

run('theme', node, [join(here, 'install-themes.mjs'), theme]);

// Portrait art is not redistributed, so only wire it up when it is already built.
const artDir = join(repo, 'assets', `maid-${theme}`);
const art = join(artDir, 'normal.png');
if (skipArt) {
  process.stdout.write('\n[art]\n  skipped (--no-art)\n');
} else if (existsSync(art)) {
  run('art', node, [join(here, 'install-mascot.mjs'), theme,
    '--normal', art, '--happy', existsSync(join(artDir, 'happy.png')) ? join(artDir, 'happy.png') : art]);
} else {
  process.stdout.write(`\n[art]\n  no art at ${art}\n`);
  process.stdout.write('  build it with scripts/fetch-cursors.py + scripts/cursor_head.py first\n');
}

run('patch: wordmark colours', node, [join(here, 'patch-theme-colors.mjs')]);
run('patch: portrait setting', node, [join(here, 'patch-portrait-options.mjs')]);

// Report what the config file still needs.
const config = join(home, '.dsh', 'profiles', 'dsh-tui', 'cordis.patch.yml');
const wanted = [
  ['terminalImages', 'true'],
  ['whaleGirl', 'true'],
  ['maidPortraitSkin', theme],
];
let missing = [];
if (existsSync(config)) {
  const text = readFileSync(config, 'utf8');
  missing = wanted.filter(([key]) => !new RegExp(`^\\s*${key}\\s*:`, 'm').test(text));
}

process.stdout.write('\n=========================================\n');
process.stdout.write(`theme "${theme}" installed, patches applied.\n`);
if (missing.length) {
  process.stdout.write(`\nadd to ${config}:\n`);
  for (const [key, value] of missing) process.stdout.write(`  ${key}: ${value}\n`);
  process.stdout.write('  companion:\n    skin: whale\n');
} else {
  process.stdout.write('config already has the needed keys.\n');
}
process.stdout.write('\nrestart dsh-tui, then check /settings -> 开屏与吉祥物 -> 立绘形象\n');
