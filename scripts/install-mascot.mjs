// Install prepared portrait art into the dsh-tui package.
//
//   node install-mascot.mjs mizuki --normal ../assets/maid-mizuki/normal.png
//                                --happy  ../assets/maid-mizuki/happy.png
//   node install-mascot.mjs --restore mizuki
//
// `maidPortrait.js` looks for `assets/maid-<variant>/{normal,happy}.png`
// (301x288 or whatever you produced — it trims transparent edges and scales to
// the 40-column splash box). The stock look comes from `assets/whale-girl/`,
// which this script never touches, so `--restore` just deletes the copy.
import { copyFileSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { homedir } from 'node:os';

const HOME = homedir();
const PKG = join(HOME, '.dsh', 'profiles', 'dsh-tui', 'node_modules',
  '@deepseek-harness-tui', 'dsh-tui');

function usage() {
  console.error(`usage:
  node install-mascot.mjs <variant> --normal <file> [--happy <file>]
  node install-mascot.mjs --restore <variant>`);
  process.exit(1);
}

const args = process.argv.slice(2);
const restore = args.includes('--restore');
const flag = name => {
  const at = args.indexOf(name);
  return at >= 0 ? args[at + 1] : undefined;
};
const variant = args.find(a => !a.startsWith('--') && !args[args.indexOf(a) - 1]?.startsWith('--'));
if (!variant) usage();

const target = join(PKG, 'assets', `maid-${variant}`);

if (restore) {
  rmSync(target, { recursive: true, force: true });
  console.log(`removed ${target}`);
  process.exit(0);
}

const normal = flag('--normal');
const happy = flag('--happy') ?? normal;
if (!normal) usage();

for (const file of [normal, happy]) {
  if (!existsSync(resolve(file))) {
    console.error(`missing: ${resolve(file)}`);
    process.exit(1);
  }
}

mkdirSync(target, { recursive: true });
copyFileSync(resolve(normal), join(target, 'normal.png'));
copyFileSync(resolve(happy), join(target, 'happy.png'));
console.log(`installed ${variant} -> ${target}`);
console.log('pick it in /settings -> 开屏与吉祥物 -> 立绘形象 (needs patch-portrait-options.mjs)');
