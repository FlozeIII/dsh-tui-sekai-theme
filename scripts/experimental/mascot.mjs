#!/usr/bin/env node
// Install a companion mascot kit into the dsh-tui package.
//   node mascot.mjs auto     # follow ~/.dsh-tui/theme.json (mizuki / ena / else original)
//   node mascot.mjs mizuki | ena | whale
import { existsSync, readFileSync, writeFileSync, cpSync, rmSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const HOME = homedir();
const KITS = join(HOME, '.dsh-tui', 'mascot', 'kits');
const ORIGINAL = join(HOME, '.dsh-tui', 'mascot', 'whaleGirl-original');
const TARGET = join(HOME, '.dsh', 'profiles', 'dsh-tui', 'node_modules',
  '@deepseek-harness-tui', 'dsh-tui', 'assets', 'whaleGirl');
const THEME_JSON = join(HOME, '.dsh-tui', 'theme.json');
const SPLASH_DIR = join(HOME, '.dsh-tui', 'mascot', 'splash');
const PORTRAIT_DIR = join(HOME, '.dsh', 'profiles', 'dsh-tui', 'node_modules',
  '@deepseek-harness-tui', 'dsh-tui', 'assets', 'whale-girl');
const SPLASH_MODULE = join(HOME, '.dsh', 'profiles', 'dsh-tui', 'node_modules',
  '@deepseek-harness-tui', 'dsh-tui', 'lib', 'types', 'components', 'whaleGirlSprite.js');

function currentTheme() {
  try {
    return JSON.parse(readFileSync(THEME_JSON, 'utf8')).theme ?? null;
  } catch {
    return null;
  }
}

function countPng(dir) {
  let n = 0;
  const walk = (d) => {
    for (const e of readdirSync(d, { withFileTypes: true })) {
      const p = join(d, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.png')) n += 1;
    }
  };
  walk(dir);
  return n;
}

const arg = (process.argv[2] ?? 'auto').toLowerCase();
let who = arg;
if (who === 'auto') {
  const t = currentTheme();
  who = t === 'mizuki' || t === 'ena' ? t : 'whale';
}
if (!['mizuki', 'ena', 'whale'].includes(who)) {
  console.error(`unknown preset "${arg}" (use auto | mizuki | ena | whale)`);
  process.exit(1);
}

const src = who === 'whale' ? ORIGINAL : join(KITS, who);
if (!existsSync(join(src, 'frames.json'))) {
  console.error(`kit not found: ${src}`);
  process.exit(1);
}

rmSync(join(TARGET, 'img'), { recursive: true, force: true });
cpSync(join(src, 'frames.json'), join(TARGET, 'frames.json'));
cpSync(join(src, 'img'), join(TARGET, 'img'), { recursive: true });
for (const extra of ['README.md']) {
  if (existsSync(join(src, extra))) cpSync(join(src, extra), join(TARGET, extra));
}
writeFileSync(join(TARGET, '.mascot-preset'), who + '\n');

// Splash portrait: dsh-tui has no user-level override for the 30x30 start-up
// sprite, so we swap the generated module. `whale` restores the pristine copy
// saved on the first install.
if (existsSync(SPLASH_MODULE) && !existsSync(SPLASH_MODULE + '.orig')) {
  cpSync(SPLASH_MODULE, SPLASH_MODULE + '.orig');
}
const splashSrc = join(SPLASH_DIR, who + '.js');
if (who !== 'whale' && existsSync(splashSrc)) {
  cpSync(splashSrc, SPLASH_MODULE);
  console.log(`splash: ${who} 30x30 sprite installed`);
} else if (existsSync(SPLASH_MODULE + '.orig')) {
  cpSync(SPLASH_MODULE + '.orig', SPLASH_MODULE);
  console.log('splash: pristine whaleGirl sprite restored');
}

// Crisp portrait: the start-up art with an image protocol is just these PNGs
// (lib/types/components/maidPortrait.js MAID_ASSETS), so swap them per theme.
for (const [file, frame] of [['whale-girl.png', 'idle/00.png'],
                             ['whale-girl-happy.png', 'happy/00.png'],
                             ['whale-girl-dark.png', 'idle/00.png']]) {
  const dst = join(PORTRAIT_DIR, file);
  if (existsSync(dst) && !existsSync(dst + '.orig')) cpSync(dst, dst + '.orig');
  const art = join(src, 'img', frame.split('/')[0], frame.split('/')[1]);
  if (who !== 'whale' && existsSync(art)) {
    cpSync(art, dst);
  } else if (existsSync(dst + '.orig')) {
    cpSync(dst + '.orig', dst);
  }
}
console.log(`portrait: ${who === 'whale' ? 'pristine' : who + ' portrait assets installed'}`);

const frameCount = countPng(join(TARGET, 'img'));
const frames = JSON.parse(readFileSync(join(TARGET, 'frames.json'), 'utf8')).animations.length;
console.log(`mascot: ${who}  animations=${frames}  png=${frameCount}  installed -> ${TARGET}`);
